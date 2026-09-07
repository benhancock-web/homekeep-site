"""One-off: split the Stage B prototype (website.src.html) into one source fragment per page.

Run once at repo creation; the fragments in src/pages/ are the editable sources from then on.
Copy is kept verbatim. Only the prototype's navigation mechanics change:
  - data-page="p-x" hops become real hrefs ({{base}}/path/),
  - clickable cards become links,
  - the studio bar, page picker and figures switch are dropped (figures.json replaces the switch).
"""
import re, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent.parent / "src" / "pages"
OUT.mkdir(parents=True, exist_ok=True)

ROUTES = {
    "p-home": "{{base}}/",
    "p-find": "{{base}}/find-a-cleaner/",
    "p-results": "{{base}}/cleaners/",
    "p-profile": "{{base}}/cleaners/example-maria/",
    "p-become": "{{base}}/become-a-cleaner/",
    "p-app": "{{base}}/cleaner-app/",
    "p-pricing": "{{base}}/pricing/",
    "p-about": "{{base}}/about/",
}
FILES = {
    "p-home": "home.html", "p-find": "find-a-cleaner.html", "p-results": "cleaners.html",
    "p-profile": "cleaner-example.html", "p-become": "become-a-cleaner.html", "p-app": "cleaner-app.html",
    "p-pricing": "pricing.html", "p-about": "about.html",
}

html = SRC.read_text()
pages = re.findall(r'<div class="page(?: is-active)?" id="(p-[a-z]+)">\n(.*?)\n</div>\n\n?(?=<div class="page|\s*</main>)', html, flags=re.S)
assert len(pages) == 8, len(pages)

def rewrite(frag: str) -> str:
    # "Apply" buttons on the cleaner pages go to the apply destination, not back to the page.
    frag = re.sub(r'<a class="btn btn-brass" href="#" data-page="p-become"', '<a class="btn btn-brass" href="{{apply}}"', frag)
    # Form submit buttons: the form itself carries the action.
    frag = frag.replace('<form class="postcode" onsubmit="return false">', '<form class="postcode" method="get" action="{{base}}/cleaners/">')
    frag = re.sub(r'<button class="btn btn-brass" type="submit"( id="heroCta")? data-page="p-results">', '<button class="btn btn-brass" type="submit">', frag)
    # Links with a placeholder href and a data-page hop.
    def link(m):
        return f'href="{ROUTES[m.group(2)]}"' if m.group(1) is None else f'{m.group(1)}href="{ROUTES[m.group(2)]}"'
    frag = re.sub(r'(?:(href="#") )?data-page="(p-[a-z]+)"', lambda m: f'href="{ROUTES[m.group(2)]}"', frag)
    frag = re.sub(r'href="#" href="', 'href="', frag)
    # Clickable cards: <article ... href=...> and <div class="item" href=...> become anchors.
    frag = re.sub(r'<article class="([^"]*)" href="([^"]*)" style="cursor:pointer">(.*?)</article>',
                  lambda m: f'<a class="{m.group(1)}" href="{m.group(2)}">{m.group(3)}</a>', frag, flags=re.S)
    frag = re.sub(r'<article class="([^"]*)" href="([^"]*)" style="box-shadow:inset 0 0 0 1px var\(--hairline\);cursor:pointer">',
                  lambda m: f'<a class="{m.group(1)}" href="{m.group(2)}" style="box-shadow:inset 0 0 0 1px var(--hairline)">', frag)
    frag = re.sub(r'<div class="result-card" href="([^"]*)" style="box-shadow:inset 0 0 0 1px var\(--hairline\);cursor:pointer">(.*?)</div></div></div>',
                  lambda m: f'<a class="result-card" href="{m.group(1)}" style="box-shadow:inset 0 0 0 1px var(--hairline)">{m.group(2)}</div></div></a>', frag, flags=re.S)
    frag = re.sub(r'<div class="item" href="([^"]*)" style="cursor:pointer">(.*?)</div>\n',
                  lambda m: f'<a class="item" href="{m.group(1)}">{m.group(2)}</a>\n', frag, flags=re.S)
    return frag

for pid, body in pages:
    (OUT / FILES[pid]).write_text(rewrite(body) + "\n")
    print("wrote", FILES[pid], len(body))
