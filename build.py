"""Build the Otterly public website into _site/.

    python3 build.py            # uses site.json (base = /homekeep-site on the GitHub address)
    SITE_BASE= python3 build.py # once a custom domain is pointed at the site

What it does, in order:
  1. Reads site.json (paths, company line, contact email), figures.json (the honesty switch)
     and roadmap.json (the household and cleaner roadmaps; one source for every page).
  2. For every page in PAGES: takes the fragment in src/pages/, applies the honesty switch
     (figures.json confirmed=false REMOVES every class="unconfirmed" element and keeps the
     class="launch-only" alternative), expands the helpers below, fills the shell in
     src/layout.html and writes _site/<path>/index.html.
  3. Legal documents in src/legal/ go through the same shell with the legal template
     (contents list from the h2s, a "Last updated" line, and the Draft notice until reviewed).
  4. Writes a forwarding page at every retired address (REDIRECTS) so old links still land.
  5. Copies assets/, writes sitemap.xml, robots.txt, 404.html and .nojekyll.

Helpers usable in page fragments:
  {{phone:NAME|Alt text}}        a real app screen that follows the visitor's light/dark setting
  {{phone-light:NAME|Alt}}       always the light screen      {{phone-dark:NAME|Alt}}  always dark
  {{roadmap:households}}         the three-column roadmap      {{roadmap-status}}  the honest status line
  {{count:households:now}}       how many items sit in a roadmap column
  {{mail:Subject words}}         a mailto: link to the contact address with that subject
The banned-word check (check.py) runs on the OUTPUT, so anything the build adds is checked too.
"""
import json, os, re, shutil, pathlib, html as htmlmod, datetime, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
SRC, OUT, ASSETS = ROOT / "src", ROOT / "_site", ROOT / "assets"

site = json.loads((ROOT / "site.json").read_text())
figures = json.loads((ROOT / "figures.json").read_text())
roadmap = json.loads((ROOT / "roadmap.json").read_text())
BASE = os.environ.get("SITE_BASE", site["base"])
ORIGIN = os.environ.get("SITE_ORIGIN", site["origin"])
CONFIRMED = bool(figures.get("confirmed"))
TODAY = datetime.date.today().isoformat()
NAME = site["company_name"]

PAGES = [
    dict(path="", src="home.html", home=True, top="band", faq=False,
         title="Otterly | Vetted local cleaners you can trust",
         description="Otterly is the phone app for households and independent cleaners in Hertfordshire and Essex. Find a verified cleaner, book a trial clean, and let the app handle the rest."),
    dict(path="households", src="households.html", nav="households", faq=True,
         title="For households | Otterly",
         description="Choose a verified, self-employed cleaner near you, see their own rate up front, book a trial clean, and follow every visit in the app."),
    dict(path="cleaners", src="cleaners.html", nav="cleaners", faq=True,
         title="For cleaners | Otterly",
         description="Set your own rate and days, find regular households close to home, and let the Otterly app keep your diary, invoices and earnings."),
    dict(path="companies", src="companies.html", nav="companies",
         title="For cleaning companies | Otterly",
         description="A version of Otterly for cleaning companies is being explored. Nothing is built yet. Tell us what you would need."),
    dict(path="web", src="web.html", nav="web",
         title="Use Otterly on the web | Otterly",
         description="Otterly is made for phones, but you will not need one. The web version opens alongside the app."),
    dict(path="about", src="about.html", nav="about",
         title="About Otterly | Get involved",
         description="Why Otterly exists, how the marketplace works, and how cleaners, advertisers, advisers and investors can help shape it."),
    dict(path="contact", src="contact.html",
         title="Contact | Otterly",
         description="How to reach Otterly: support, complaints and questions about your data."),
    dict(path="legal", src="legal-index.html",
         title="Legal | Otterly",
         description="Otterly's terms, privacy notice, cookie policy, insurance and complaints, modern slavery statement and how to delete your account."),
]

# Retired addresses from the September site, forwarded so no outside link breaks.
REDIRECTS = {
    "find-a-cleaner": "households/",
    "pricing": "households/#costs",
    "become-a-cleaner": "cleaners/",
    "cleaner-app": "cleaners/",
    "cleaners/example-maria": "households/",
}

LEGAL = [
    dict(slug="terms-for-households", src="terms-for-households.html", title="Terms for households", reviewed=False),
    dict(slug="terms-for-cleaners", src="terms-for-cleaners.html", title="Terms for cleaners", reviewed=False),
    dict(slug="privacy", src="privacy.html", title="Privacy policy", reviewed=False),
    dict(slug="cookies", src="cookies.html", title="Cookie policy", reviewed=False),
    dict(slug="insurance-and-complaints", src="insurance-and-complaints.html", title="Insurance and complaints", reviewed=False),
    dict(slug="modern-slavery", src="modern-slavery.html", title="Modern slavery statement", reviewed=False),
    dict(slug="delete-account", src="delete-account.html", title="Delete your account", reviewed=True),
]

layout = (SRC / "layout.html").read_text()
partials = {p.stem: p.read_text() for p in (SRC / "partials").glob("*.html")}
ICON_WARN = '<svg class="ic ic-20" aria-hidden="true"><use href="#i-flag"/></svg>'
COLS = [("now", "In the app now", "Built and working in the test version.", "t-now"),
        ("testing", "In testing", "Built, and being checked before it is switched on.", "t-test"),
        ("later", "Coming later", "Planned. No dates yet.", "t-later")]


def fill(text, **vars):
    for k, v in vars.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def honesty(frag):
    """Apply figures.json. Elements are removed from the HTML, not hidden with CSS."""
    drop = "launch-only" if CONFIRMED else "unconfirmed"
    keep = "unconfirmed" if CONFIRMED else "launch-only"
    for tag in ("span", "p", "h2", "div", "section", "li"):
        pat = re.compile(r'<' + tag + r'\b[^>]*\bclass="[^"]*\b' + drop + r'\b[^"]*"[^>]*>', re.S)
        while True:
            m = pat.search(frag)
            if not m:
                break
            i, depth = m.end(), 1
            open_re = re.compile(r'<' + tag + r'\b|</' + tag + r'>')
            while depth:
                n = open_re.search(frag, i)
                if not n:
                    raise SystemExit(f"unbalanced <{tag}> near: {frag[m.start():m.start()+80]!r}")
                depth += 1 if n.group(0)[1] != '/' else -1
                i = n.end()
            frag = frag[:m.start()] + frag[i:]
    frag = re.sub(r'\s*\b' + keep + r'\b', '', frag)
    return frag.replace('class=""', '').replace('class=" ', 'class="')


def phone(kind, name, alt):
    src = "{{base}}/assets/shots/"
    alt = htmlmod.escape(alt.strip(), quote=True)
    for theme in ("light", "dark"):
        if not (ASSETS / "shots" / f"{theme}_{name}.webp").exists():
            raise SystemExit(f"missing screenshot {theme}_{name}.webp")
    img = f'<img src="{src}{{T}}_{name}.webp" alt="{alt}" width="600" height="1298" loading="lazy" decoding="async">'
    if kind == "phone":
        inner = (f'<picture><source srcset="{src}dark_{name}.webp" media="(prefers-color-scheme: dark)">'
                 + img.replace("{T}", "light") + '</picture>')
    else:
        inner = img.replace("{T}", "light" if kind == "phone-light" else "dark")
    return f'<span class="phone">{inner}</span>'


def roadmap_html(who):
    out = ['<div class="road">']
    for key, label, sub, cls in COLS:
        items = roadmap[who][key]
        out.append(f'<div class="road-col"><h3 class="road-head"><span class="tag {cls}">{label}</span>'
                   f'<span class="road-n">{len(items)}</span></h3><p class="road-sub">{sub}</p><ul>')
        for title, note in items:
            out.append(f'<li><strong>{title}</strong>' + (f'<span>{note}</span>' if note else '') + '</li>')
        out.append('</ul></div>')
    out.append('</div>')
    return "".join(out)


RIPPLES = ('<svg class="ripples" viewBox="0 0 1400 320" preserveAspectRatio="xMidYMax meet" aria-hidden="true" focusable="false">'
           '<ellipse cx="700" cy="320" rx="690" ry="170"/><ellipse cx="700" cy="320" rx="500" ry="118"/><ellipse cx="700" cy="320" rx="310" ry="70"/></svg>')


def store_note():
    links = []
    if site.get("app_store_url"):
        links.append(f'<a href="{site["app_store_url"]}">App Store</a>')
    if site.get("play_store_url"):
        links.append(f'<a href="{site["play_store_url"]}">Google Play</a>')
    if links:
        return "Get Otterly on the " + " and ".join(links) + "."
    return 'Not in the App Store or Google Play yet. <a href="{{base}}/households/#roadmap">See what\'s in the app today</a>.'


def helpers(frag):
    frag = frag.replace("{{ripples}}", RIPPLES).replace("{{store_note}}", store_note())
    frag = re.sub(r'\{\{(phone|phone-light|phone-dark):([a-z_-]+)\|([^}]*)\}\}', lambda m: phone(m.group(1), m.group(2), m.group(3)), frag)
    frag = re.sub(r'\{\{roadmap:(households|cleaners)\}\}', lambda m: roadmap_html(m.group(1)), frag)
    frag = re.sub(r'\{\{count:(households|cleaners):(now|testing|later)\}\}', lambda m: str(len(roadmap[m.group(1)][m.group(2)])), frag)
    frag = frag.replace("{{roadmap-status}}", roadmap["status_line"])
    frag = re.sub(r'\{\{mail:([^}]*)\}\}', lambda m: "mailto:" + site["contact_email"] + "?subject=" + urllib.parse.quote(m.group(1).strip()), frag)
    return frag


def faq_schema(frag):
    qs = re.findall(r'<details[^>]*><summary>(.*?)</summary>\s*<div class="a">(.*?)</div>\s*</details>', frag, flags=re.S)
    if not qs:
        return ""
    def text(s):
        return htmlmod.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s))).strip()
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": text(q), "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in qs]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def org_schema():
    data = {"@context": "https://schema.org", "@type": "Organization", "name": NAME, "url": ORIGIN + BASE + "/",
            "logo": ORIGIN + BASE + "/assets/img/apple-touch-icon.png"}
    return '<script type="application/ld+json">' + json.dumps(data) + '</script>'


def header(page):
    out = partials["header"]
    for key in ("households", "cleaners", "companies", "about", "web"):
        out = out.replace("{{cur:" + key + "}}", ' aria-current="page"' if page.get("nav") == key else "")
    return out.replace("{{header_class}}", "site-header on-band" if page.get("top") == "band" else "site-header")


def app_meta():
    """Safari's own Smart App Banner on iPhone, once the App Store listing exists."""
    return f'<meta name="apple-itunes-app" content="app-id={site["ios_app_id"]}">' if site.get("ios_app_id") else ""


def app_banner():
    """App-first nudge for phone visitors: points iPhone and Android visitors at their store, dismissible,
    remembered for 30 days. Renders nothing until a store URL is set in site.json."""
    ios, android = site.get("app_store_url", ""), site.get("play_store_url", "")
    if not (ios or android):
        return ""
    cfg = json.dumps({"ios": ios, "android": android, "smart": bool(site.get("ios_app_id"))})
    return (f'<div class="app-banner" id="appBanner" role="region" aria-label="Get the Otterly app" hidden data-apps=\'{cfg}\'>'
            '<img src="{{base}}/assets/img/apple-touch-icon.png" alt="" width="48" height="48">'
            '<div class="app-banner-text"><strong>Otterly works best in the app</strong><span>Bookings, visits and earnings in your pocket.</span></div>'
            '<div class="app-banner-actions"><a class="btn btn-band" id="appBannerGet" href="#">Get the app</a>'
            '<button type="button" class="app-banner-stay" id="appBannerStay">Continue on the website</button></div></div>')


def render(page, content, structured=""):
    path = page["path"]
    canonical = ORIGIN + BASE + "/" + (path + "/" if path else "")
    robots = '<meta name="robots" content="noindex">' if (site.get("noindex") or page.get("noindex")) else ""
    out = fill(layout, title=page["title"], description=page["description"], canonical=canonical, robots=robots,
               structured=structured, icons=partials["icons"], header=header(page), content=content,
               footer=partials["footer"], menu=partials["menu"], body_class=page.get("body_class", ""))
    out = helpers(out)
    # The hero's phones are the first thing seen: load them straight away, not lazily.
    out = re.sub(r'<div class="hero-phones">.*?</div>', lambda m: m.group(0).replace('loading="lazy"', 'loading="eager" fetchpriority="high"'), out, flags=re.S)
    web = site.get("web_app_url", "")
    out = fill(out, app_meta=app_meta(), app_banner=app_banner())
    out = fill(out, web_signin=(f'<a class="btn btn-tonal" href="{web}">Sign in on the web</a>' if web else
                                '<span class="pill-soon">Opens alongside the app</span>'))
    out = fill(out, base=BASE, company_name=NAME, company_line=site["company_line"],
               contact_email=site["contact_email"] or "hello@example.invalid", today=TODAY, year=TODAY[:4])
    if "{{" in out:
        raise SystemExit(f"unfilled placeholder in {path or 'home'}: {re.findall(r'{{[^}]+}}', out)[:5]}")
    dest = OUT / path / "index.html" if path else OUT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return canonical


def legal_page(doc):
    body = (SRC / "legal" / doc["src"]).read_text()
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    contents = "".join(f'<a href="#{i}">{t}</a>' for i, t in heads)
    meta = re.search(r'<!--\s*updated:\s*([0-9-]+)\s*-->', body)
    updated = meta.group(1) if meta else TODAY
    notice = "" if doc["reviewed"] else (
        '<div class="notice" role="note">' + ICON_WARN +
        '<p><strong>Draft.</strong> This document is a working draft that has not yet been reviewed by a solicitor. '
        'It shows what the final document will cover. It is published so the address exists; it is not yet the agreement you rely on. '
        'Questions about it: <a href="{{base}}/contact/">contact us</a>.</p></div>')
    content = f'''
<section class="page-head"><div class="container"><p class="over"><a href="{{{{base}}}}/legal/">Legal</a></p><h1>{doc["title"]}</h1><p class="meta">Last updated {updated} · version 0.1</p></div></section>
<section class="section tight"><div class="container legal">
  <aside class="contents" aria-label="Contents"><h2 class="over">Contents</h2>{contents}<a href="{{{{base}}}}/legal/">All legal documents</a></aside>
  <article class="prose">{notice}{body}</article>
</div></section>'''
    page = dict(path="legal/" + doc["slug"], title=doc["title"] + " | Otterly", description=f"Otterly {doc['title'].lower()}.")
    return render(page, content)


def redirect(old, new):
    target = BASE + "/" + new
    dest = OUT / old / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f'<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Moved | Otterly</title>'
                    f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={target}">'
                    f'<link rel="canonical" href="{ORIGIN}{target}"></head><body><p>This page has moved to '
                    f'<a href="{target}">{ORIGIN}{target}</a>.</p></body></html>')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    urls = []
    for page in PAGES:
        frag = honesty((SRC / "pages" / page["src"]).read_text())
        structured = (org_schema() if page.get("home") else "") + (faq_schema(frag) if page.get("faq") else "")
        urls.append((render(page, frag, structured), page.get("noindex")))
    for doc in LEGAL:
        urls.append((legal_page(doc), False))
    for old, new in REDIRECTS.items():
        redirect(old, new)
    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    page = dict(path="404", title="Page not found | Otterly", description="That page does not exist.")
    render(page, '<section class="page-head"><div class="container"><h1>That page is not here</h1><p class="lede">The address may have changed. Try the <a href="{{base}}/">home page</a>, <a href="{{base}}/households/">for households</a> or <a href="{{base}}/cleaners/">for cleaners</a>.</p></div></section>')
    shutil.move(OUT / "404" / "index.html", OUT / "404.html"); (OUT / "404").rmdir()
    if site.get("noindex"):
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    else:
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}{BASE}/sitemap.xml\n")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{u}</loc></url>" for u, noindex in urls if not noindex]
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    print(f"built {len(urls)} pages + {len(REDIRECTS)} forwards → _site/  (base={BASE!r}, figures confirmed={CONFIRMED}, noindex={site.get('noindex')})")


if __name__ == "__main__":
    main()
