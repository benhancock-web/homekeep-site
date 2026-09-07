# Homekeep — public website

Static site for homekeep, built from the Stage B design prototype and served by GitHub Pages.

- `src/pages/*.html` — one fragment per page (the copy; edit here).
- `src/legal/*.html` — the legal documents (drafts until a solicitor has reviewed them; flip `reviewed` in `build.py`).
- `src/partials/` — header, footer, mobile menu, the SVG icon sheet. `src/layout.html` is the page shell.
- `assets/css/` — `tokens.css` and `design-system.css` are copied from the app's design system (generated from `tokens.json`; never hand-edit values). `site.css` holds the web-only additions. `fonts.css` + `assets/fonts/` self-host Jost, Carlito and DM Mono.
- `figures.json` — the launch honesty switch. `confirmed: false` removes every unconfirmed figure from the built HTML. Only Mark flips it.
- `site.json` — base path, company line, contact email, where "Apply" goes.

## Build and check

    python3 build.py              # → _site/
    python3 check.py _site        # banned words (the legal spine) — must be 0 hits
    python3 scripts/linkcheck.py  # every internal link resolves
    node scripts/shots.js         # screenshots, both themes, 390 + 1280 (needs Playwright + Chromium)

The deploy workflow (`.github/workflows/deploy.yml`) runs build → check → linkcheck → deploy on every push to `main`. A banned word or a broken link fails the build and nothing deploys.

## Moving to a custom domain

Set `base` to `""` and `origin` to the domain in `site.json`, add a `CNAME` file containing the bare domain to the repo root (and copy it into `_site/` in `build.py`), point DNS at GitHub Pages, and set the custom domain in the repo's Pages settings.
