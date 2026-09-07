"""Every internal href/src in the built site must resolve to a file. Fails the build otherwise."""
import re, sys, pathlib, json
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
base = json.loads(pathlib.Path("site.json").read_text())["base"]
import os
base = os.environ.get("SITE_BASE", base)
bad, n = [], 0
for f in root.rglob("*.html"):
    html = f.read_text()
    for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
        u = m.group(1)
        if u.startswith(("http", "mailto:", "tel:", "#", "data:")):
            continue
        n += 1
        u = u.split("#")[0].split("?")[0]
        if u.startswith(base + "/"):
            u = u[len(base):]
        if u.startswith("/"):
            target = root / u.lstrip("/")
        else:
            target = f.parent / u
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            bad.append(f"{f.relative_to(root)} -> {m.group(1)}")
print(f"checked {n} internal links, broken: {len(bad)}")
for b in bad: print("  BROKEN", b)
sys.exit(1 if bad else 0)
