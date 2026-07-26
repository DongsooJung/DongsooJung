# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
Static website collection for **STARGATE EDU** (Korean education brand). There is **no backend, database, package manager, or build step** — just plain HTML/CSS with a tiny bit of vanilla JS. It is deployed via GitHub Pages (`.nojekyll` = raw HTML served directly).

Pages (each is a standalone `index.html`):
- `index.html` — main landing page (root)
- `lp/index.html` — marketing landing page
- `koi-coach/index.html` — KOI Coach sub-page
- `mobile/index.html` — mobile-style page with an interactive bottom-tab switcher (`switchTab()`)

### Running locally (dev)
No dependencies to install. Serve the repo root with any static HTTP server, e.g.:

```bash
python3 -m http.server 8000   # run from repo root
```

Then open `http://localhost:8000/` (main), `/lp/`, `/koi-coach/`, `/mobile/`.

### Lint / test / build
There is **none** — no linter, no test suite, no build tooling exist in this repo. "Testing" means serving the files and visually verifying the four HTML pages render and the `mobile/` tab bar switches content.

### Gotchas
- `배포_실행.ps1` is a **Windows-only PowerShell deploy** script (git + `gh` CLI) — it is for production deployment, not local dev; do not run it in the cloud VM.
- No `CNAME` file exists in the working tree even though README/docs reference one; that is expected.
- Google Fonts load from a CDN; pages still render with fallback fonts if offline.
