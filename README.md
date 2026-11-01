# Otterly — public website

Static site for Otterly (the repo keeps its old name, `homekeep-site`), served by GitHub Pages. Rebuilt in Stage 7 of the November 2026 redesign in the "Riverbank" brand.

- `src/pages/*.html` — one fragment per page (the copy; edit here): home, households, cleaners, companies, web, about, contact, legal index.
- `src/legal/*.html` — the legal documents (drafts until a solicitor has reviewed them; flip `reviewed` in `build.py`).
- `src/partials/` — header, footer, mobile menu, the line-icon sheet. `src/layout.html` is the page shell.
- `roadmap.json` — the household and cleaner roadmaps (In the app now / In testing / Coming later). One source for every page. **Nothing goes in "now" unless it is built.**
- `assets/css/tokens.css` — copied from the app's generated `build/tokens.css`; never hand-edit. `site.css` holds the website's own layout. `fonts.css` + `assets/fonts/` self-host Newsreader and Albert Sans (OFL).
- `assets/brand/` — the Otterly logo SVGs from the brand pack (provenance metadata stripped). `assets/shots/` — real app screens, light and dark, 600×1298 WebP.
- `figures.json` — the launch honesty switch. `confirmed: false` removes every unconfirmed figure from the built HTML. Only Mark flips it.
- `site.json` — base path, company line, contact email, `web_app_url` (empty = "opens alongside the app"), store URLs (empty = "not in the stores yet").

## Page helpers
`{{phone:NAME|Alt text}}` draws a real app screen that follows the visitor's light/dark setting (`phone-light` / `phone-dark` fix the theme). `{{roadmap:households}}`, `{{count:cleaners:now}}`, `{{mail:Subject}}` and `{{ripples}}` are described at the top of `build.py`.

## Build and check

    python3 build.py              # → _site/
    python3 check.py _site        # banned words (the legal spine) — must be 0 hits
    python3 scripts/linkcheck.py  # every internal link resolves
    node scripts/shots.js         # screenshots, both themes (needs Playwright + Chromium)

The deploy workflow (`.github/workflows/deploy.yml`) runs build → check → linkcheck → deploy on every push to `main`. A banned word or a broken link fails the build and nothing deploys.

## Refreshing the app screenshots

1. In the app repo: `EXPO_PUBLIC_USE_MOCK=1 npx expo export --platform web` (sample canon data only).
2. `node scripts/capture_app_screens.mjs <app>/dist raw /h/find /h/cleaner /home /visits ...`
3. `ALBERT_SANS_TTF=<app>/assets/fonts/AlbertSans_600SemiBold.ttf python3 scripts/frame_phone.py framed raw/*.png`
4. Convert to 600 px WebP (q86) into `assets/shots/` keeping the `light_` / `dark_` names.

Device captures from a real iPhone can replace these later at the same names.

## Moving to a custom domain

Set `base` to `""` and `origin` to the domain in `site.json`, add a `CNAME` file containing the bare domain to the repo root (and copy it into `_site/` in `build.py`), point DNS at GitHub Pages, and set the custom domain in the repo's Pages settings. Turn `noindex` off only when Ben says.
