"""Build the Homekeep public website into _site/.

    python3 build.py            # uses site.json (base = /homekeep-site on the GitHub address)
    SITE_BASE= python3 build.py # once a custom domain is pointed at the site

What it does, in order:
  1. Reads site.json (paths, company line, contact email) and figures.json (the honesty switch).
  2. For every page in PAGES: takes the fragment in src/pages/, applies the honesty switch
     (figures.json confirmed=false REMOVES every class="unconfirmed" element and keeps the
     class="launch-only" alternative; confirmed=true does the opposite), fills the shell in
     src/layout.html with header, footer, menu, icons, meta and structured data, and writes
     _site/<path>/index.html.
  3. Legal documents in src/legal/ go through the same shell with the legal template
     (contents list generated from the h2s, a "Last updated" line, and the placeholder notice
     until a document is marked reviewed).
  4. Copies assets/, writes sitemap.xml, robots.txt, 404.html and .nojekyll.
The banned-word check (check.py) runs on the OUTPUT, not the sources, so anything the build
adds is checked too.
"""
import json, os, re, shutil, pathlib, html as htmlmod, datetime

ROOT = pathlib.Path(__file__).resolve().parent
SRC, OUT, ASSETS = ROOT / "src", ROOT / "_site", ROOT / "assets"

site = json.loads((ROOT / "site.json").read_text())
figures = json.loads((ROOT / "figures.json").read_text())
BASE = os.environ.get("SITE_BASE", site["base"])
ORIGIN = os.environ.get("SITE_ORIGIN", site["origin"])
CONFIRMED = bool(figures.get("confirmed"))
TODAY = datetime.date.today().isoformat()

# path, source, title, description, cta ("find" | "apply" | None), extra
PAGES = [
    dict(path="", src="home.html", cta="find", faq=True, home=True,
         title="Find a Vetted Local Cleaner | Homekeep",
         description="Browse background checked self employed cleaners near you, see their rates before you message and book through the app. Free to search."),
    dict(path="find-a-cleaner", src="find-a-cleaner.html", cta="find", nav="find",
         title="Find a Cleaner Near You | Homekeep",
         description="Search verified self employed cleaners in your area. See rates, reviews and availability before you message. Free to search, book in minutes."),
    dict(path="cleaners", src="cleaners.html", cta=None, nav="find", sticky=False,
         title="Cleaners near you | Homekeep",
         description="Browse self employed cleaners near you. First name, area, rate, experience and availability are visible to anyone."),
    dict(path="cleaners/example-maria", src="cleaner-example.html", cta=None, nav="find", sticky=False, noindex=True,
         title="Example cleaner profile | Homekeep",
         description="An example of what a cleaner's public profile on Homekeep looks like. Maria is not a real person."),
    dict(path="become-a-cleaner", src="become-a-cleaner.html", cta="apply", nav="become", faq=True,
         title="Self Employed Cleaning Work Near You | Homekeep",
         description="Set your own rate, choose your own customers and work close to home. Diary, invoices, mileage and tax records in one app. Apply in ten minutes."),
    dict(path="cleaner-app", src="cleaner-app.html", cta="apply", nav="become",
         title="The Homekeep App for Cleaners | Diary, Invoices, Mileage and Payments",
         description="Directions to every job, your diary, automatic time tracking, invoices raised for you, mileage recorded and a year end summary for your tax return. Free for every cleaner on Homekeep."),
    dict(path="pricing", src="pricing.html", cta="find", faq=True,
         title="Pricing | Homekeep",
         description="Cleaners set their own rates and you see the exact rate on every profile before you message anyone. No contract, no minimum term and no exit fee."),
    dict(path="about", src="about.html", cta="find", nav="about",
         title="About Homekeep | A marketplace, not an agency",
         description="Homekeep is a marketplace, not an agency. Cleaners run their own businesses, set their own prices and choose their own customers."),
    dict(path="contact", src="contact.html", cta=None, sticky=False,
         title="Contact Homekeep",
         description="How to reach Homekeep: support, complaints and questions about your account."),
    dict(path="legal", src="legal-index.html", cta=None, sticky=False,
         title="Legal | Homekeep",
         description="Homekeep's terms, privacy notice, cookie policy, insurance and complaints, modern slavery statement and how to delete your account."),
]

# Legal documents: slug, title, whether a solicitor has reviewed it (placeholder notice until then).
LEGAL = [
    dict(slug="terms-for-households", src="terms-for-households.html", title="Terms for households", reviewed=False),
    dict(slug="terms-for-cleaners", src="terms-for-cleaners.html", title="Terms for cleaners", reviewed=False),
    dict(slug="privacy", src="privacy.html", title="Privacy policy", reviewed=False),
    dict(slug="cookies", src="cookies.html", title="Cookie policy", reviewed=False),
    dict(slug="insurance-and-complaints", src="insurance-and-complaints.html", title="Insurance and complaints", reviewed=False),
    dict(slug="modern-slavery", src="modern-slavery.html", title="Modern slavery statement", reviewed=False),
    dict(slug="delete-account", src="delete-account.html", title="Delete your account", reviewed=True, procedural=True),
]

layout = (SRC / "layout.html").read_text()
partials = {p.stem: p.read_text() for p in (SRC / "partials").glob("*.html")}

ICON_WARN = '<svg class="ic ic-20"><use href="#i-flag"/></svg>'

def fill(text, **vars):
    for k, v in vars.items():
        text = text.replace("{{" + k + "}}", v)
    return text

def honesty(frag):
    """Apply figures.json. Elements are removed from the HTML, not hidden with CSS."""
    drop = "launch-only" if CONFIRMED else "unconfirmed"
    keep = "unconfirmed" if CONFIRMED else "launch-only"
    # Remove whole elements carrying the drop class (balanced for the tags we use).
    for tag in ("span", "p", "h2", "div", "section", "li"):
        pat = re.compile(r'<' + tag + r'\b[^>]*\bclass="[^"]*\b' + drop + r'\b[^"]*"[^>]*>', re.S)
        while True:
            m = pat.search(frag)
            if not m:
                break
            # find matching close tag, respecting nesting of the same tag
            i, depth = m.end(), 1
            open_re = re.compile(r'<' + tag + r'\b|</' + tag + r'>')
            while depth:
                n = open_re.search(frag, i)
                if not n:
                    raise SystemExit(f"unbalanced <{tag}> near: {frag[m.start():m.start()+80]!r}")
                depth += 1 if n.group(0)[1] != '/' else -1
                i = n.end()
            frag = frag[:m.start()] + frag[i:]
    # Unwrap the keep class (leave the element, drop the marker class)
    frag = re.sub(r'\s*\b' + keep + r'\b', '', frag)
    frag = frag.replace('class=""', '').replace('class=" ', 'class="')
    return frag

def faq_schema(frag):
    qs = re.findall(r'<details><summary><h3>(.*?)</h3>.*?<div class="a">(.*?)</div></details>', frag, flags=re.S)
    if not qs:
        return ""
    def text(s):
        return htmlmod.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s))).strip()
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": text(q), "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in qs]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'

def org_schema():
    data = [{"@context": "https://schema.org", "@type": "Organization", "name": "Homekeep", "url": ORIGIN + BASE + "/"},
            {"@context": "https://schema.org", "@type": "WebSite", "name": "Homekeep", "url": ORIGIN + BASE + "/",
             "potentialAction": {"@type": "SearchAction", "target": ORIGIN + BASE + "/cleaners/?postcode={postcode}", "query-input": "required name=postcode"}}]
    return "\n".join('<script type="application/ld+json">' + json.dumps(d) + '</script>' for d in data)

def header(page):
    cta = page.get("cta")
    if cta == "find":
        h = '<a href="{{base}}/cleaners/" class="btn btn-brass" id="headerCta"><svg class="ic ic-20"><use href="#i-search"/></svg>See cleaners near you</a>'
    elif cta == "apply":
        h = '<a href="{{apply}}" class="btn btn-brass" id="headerCta"><svg class="ic ic-20"><use href="#i-chevron"/></svg>Apply in ten minutes</a>'
    else:
        h = ""
    out = partials["header"].replace("{{header_cta}}", h)
    for key in ("find", "become", "about"):
        out = out.replace("{{cur:" + key + "}}", ' class="is-current" aria-current="page"' if page.get("nav") == key else "")
    return out

def sticky(page):
    if page.get("sticky") is False or not page.get("cta"):
        return ""
    if page["cta"] == "find":
        inner = '<a class="btn btn-brass" href="{{base}}/cleaners/"><svg class="ic ic-20"><use href="#i-search"/></svg>See cleaners near you</a>'
    else:
        inner = '<a class="btn btn-brass" href="{{apply}}"><svg class="ic ic-20"><use href="#i-chevron"/></svg>Apply in ten minutes</a>'
    return '  <div class="sticky-cta is-auto">' + inner + '</div>'

def render(page, content, structured=""):
    path = page["path"]
    canonical = ORIGIN + BASE + "/" + (path + "/" if path else "")
    robots = '<meta name="robots" content="noindex">' if (site.get("noindex") or page.get("noindex")) else ""
    out = fill(layout, title=page["title"], description=page["description"], canonical=canonical, robots=robots,
               structured=structured, icons=partials["icons"], header=header(page), content=content,
               sticky=sticky(page), footer=partials["footer"], menu=partials["menu"])
    links = []
    if site.get("app_store_url"):
        links.append(f'<a class="btn btn-outline" href="{site["app_store_url"]}" style="color:var(--eucalyptus);box-shadow:inset 0 0 0 1.5px var(--eucalyptus)">Get it on the App Store</a>')
    if site.get("play_store_url"):
        links.append(f'<a class="btn btn-outline" href="{site["play_store_url"]}" style="color:var(--eucalyptus);box-shadow:inset 0 0 0 1.5px var(--eucalyptus)">Get it on Google Play</a>')
    out = fill(out, apply=site["apply_url"], store_links=('<div class="store-links">' + "".join(links) + '</div>') if links else "")
    out = fill(out, base=BASE, company_name=site["company_name"], company_line=site["company_line"],
               contact_email=site["contact_email"] or "hello@example.invalid", today=TODAY)
    if "{{" in out:
        raise SystemExit(f"unfilled placeholder in {path or 'home'}: {re.findall(r'{{[^}]+}}', out)[:5]}")
    dest = OUT / path / "index.html" if path else OUT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return canonical

def legal_page(doc):
    body = (SRC / "legal" / doc["src"]).read_text()
    # contents from h2 ids
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
<section class="tight">
  <div class="container">
    <div class="legal">
      <aside class="contents" aria-label="Contents"><h2>Contents</h2>{contents}<a href="{{{{base}}}}/legal/">All legal documents</a></aside>
      <article class="prose">
        <h1>{doc["title"]}</h1>
        <p class="meta">Last updated {updated} · version 0.1</p>
        {notice}
        {body}
      </article>
    </div>
  </div>
</section>'''
    page = dict(path="legal/" + doc["slug"], title=doc["title"] + " | Homekeep", cta=None, sticky=False,
                description=f"Homekeep {doc['title'].lower()}.")
    return render(page, content)

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    urls = []
    for page in PAGES:
        frag = (SRC / "pages" / page["src"]).read_text()
        frag = honesty(frag)
        structured = (org_schema() if page.get("home") else "") + (faq_schema(frag) if page.get("faq") else "")
        urls.append((render(page, frag, structured), page.get("noindex")))
    for doc in LEGAL:
        urls.append((legal_page(doc), False))
    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    # 404 page
    page = dict(path="404", title="Page not found | Homekeep", cta="find", sticky=False, description="That page does not exist.")
    render(page, '<section class="tight"><div class="container prose"><h1>That page is not here</h1><p>The address may have changed. Try the <a href="{{base}}/">home page</a>, <a href="{{base}}/find-a-cleaner/">find a cleaner</a> or <a href="{{base}}/become-a-cleaner/">become a cleaner</a>.</p></div></section>')
    shutil.move(OUT / "404" / "index.html", OUT / "404.html"); (OUT / "404").rmdir()
    # sitemap + robots
    if site.get("noindex"):
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    else:
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}{BASE}/sitemap.xml\n")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{u}</loc></url>" for u, noindex in urls if not noindex]
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    print(f"built {len(urls)} pages → _site/  (base={BASE!r}, figures confirmed={CONFIRMED}, noindex={site.get('noindex')})")

if __name__ == "__main__":
    main()
