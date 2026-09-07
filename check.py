"""Banned-word check for the legal spine. Runs on the BUILT site (_site/**/*.html) so anything
the build adds is checked too. Every hit fails the build, and the deploy workflow runs this
before publishing, so a banned word can never reach the public site.

Same list as the design prototype's check.py and the app's `npm run check:copy`.
Matches on visible text only: comments, scripts, styles and the hidden SVG symbol sheets are
stripped first. Word boundaries for words; phrases as written; case insensitive.
"""
import re, sys, pathlib

BANNED = [
    r"\bpay\b", r"\bpaid\b", r"\bpayslips?\b", r"\bwages?\b", r"\bsalary\b", r"\bshifts?\b", r"\brotas?\b",
    r"\bassigned\b", r"scheduled for you", r"our cleaners", r"our team", r"our staff", r"\bhire\b", r"\bemploy\b",
    r"we send you a cleaner", r"training required", r"quality controlled",
    r"cover arranged by us", r"cover is arranged", r"line manager", r"\bsupervisor\b", r"holiday pay", r"sick pay",
    r"time off", r"fully vetted", r"\bguaranteed\b", r"clock in", r"\buniform\b", r"undercutting", r"\bboss\b",
    r"send someone", r"match you", r"\breliability\b", r"length of service",
]
# The one allowed sentence (the footer disclaimer) and the one allowed phrase.
ALLOWED_SENTENCE = "we do not employ cleaners and we do not provide cleaning services"
ALLOWED_PHRASE = "your own boss"

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
files = sorted(root.rglob("*.html"))
if not files:
    print("no html files under", root); sys.exit(1)

fails = 0
for f in files:
    html = f.read_text()
    t = re.sub(r'<!--.*?-->', ' ', html, flags=re.S)
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<svg[^>]*style="position:absolute".*?</svg>', ' ', t, flags=re.S)
    # attribute text people can hear: aria-labels, alt, title, meta content
    attrs = " ".join(re.findall(r'(?:aria-label|alt|title|content|placeholder)="([^"]*)"', t))
    t = re.sub(r'<[^>]+>', ' ', t) + " " + attrs
    t = re.sub(r'\s+', ' ', t).lower()
    t = t.replace(ALLOWED_SENTENCE, ' ').replace(ALLOWED_PHRASE, ' ')
    n = 0
    for b in BANNED:
        for m in re.finditer(b, t):
            seg = t[max(0, m.start() - 60):m.end() + 60]
            print(f"  BANNED {b!r} in {f.relative_to(root)} -> …{seg.strip()}…")
            n += 1
    fails += n
print(f"checked {len(files)} pages, banned hits: {fails}")
sys.exit(1 if fails else 0)
