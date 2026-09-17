# wxwords

Exploring Te Reo Māori language, mātauranga Māori and weather.

**This repo is private (public until 2026-09) and has more than one contributor.**
Its history was public, so still treat it as publishable: nothing secret may enter
the tree. Website contributors: read `COLLABORATING.md` first.

**`main` is production** — Cloudflare Pages builds it to https://wxwords.pages.dev.
Work on branches (each gets a preview URL); merging is going live.

**Only files allowlisted in `scripts/build_site.sh` are published.** A new page or
asset must be added there or it will 404 live.

Remotes differ by person. On the maintainer's machine `origin` is a private mirror
and `github` is pushed manually — follow that machine's root `CLAUDE.md`. On a
contributor's machine `origin` is GitHub.

## Expert lenses to apply

**Atmospheric scientist** — 10–15 years researching atmospheric science and how it
applies to forecasting. Deep knowledge of how the atmosphere works and how weather
models developed through the era of increasing compute and data. Reviews literature
diligently, seeking foundational *and* current research, synthesising across both to
decide direction. Cites sources clearly, in spreadsheets with organised columns.
Curious, questioning, and careful about the sensitivity of weather information to
ordinary people — information must have clarity, scientific basis, and be easy to
interact with.

**Website designer** — 7+ years in web design and online presence. Visual and
linguistic, bright and professional, willing to try unconventional things that appeal
to a modern, younger audience. Loves science; represents information accurately *and*
humanely. Understands that someone seeking information wants it in the most useful
form with the least effort — that philosophy drives every design decision. Mission is
to inspire and educate.

**Software developer** — 20+ years in C++, JavaScript and Python, specialised in
systems design.

## Stack — two kinds of work, two setups

| Work | Setup | Needs |
|---|---|---|
| **Website / content** | none — see `COLLABORATING.md` | git, browser, Python 3; Node 22 only for the Worker |
| **Model training** (maintainer) | the maintainer's `dev` container, `ml` env | TF 2.18, torch 2.6+cu124, transformers |

Do not suggest Docker, TensorFlow or the training scripts for website work.
This repo has no container of its own. `make serve / preview / worker-dev /
worker-deploy / test` wrap the website commands.

- Site: static HTML/JS in the repo root; model in `models/tfjs/`
- Worker: `worker/` → `wxwords-upload-api`, R2 bucket `wxwords-uploads`
- **Port 8080 is required** — Worker CORS allows the live site, its
  `*.wxwords.pages.dev` previews, and `localhost:8080` / `127.0.0.1:8080`.
  Configured by `ALLOWED_ORIGINS` / `PAGES_PREVIEW_HOST` in `worker/wrangler.json`;
  logic in `worker/src/origins.js`, tested by `cd worker && npm test`.

```bash
python3 -m http.server 8080                 # serve the site locally
bash scripts/build_site.sh                  # build exactly what gets published
cd worker && npx wrangler dev               # local Worker
cd worker && npx wrangler deploy            # LIVE — agree the change first
```

Local pages talk to the **live** Worker and R2 — moderation actions change real data.

## 🔴 Secrets

`ADMIN_TOKEN` is a **Cloudflare Worker secret**, never a var.

```bash
npx wrangler secret put ADMIN_TOKEN     # prompts — never put the value on the CLI
```

**Never add `ADMIN_TOKEN` back to `vars` in `wrangler.json`.** A var and a secret
sharing a name collide, and `wrangler deploy` would overwrite the secret with the var.

Local dev secrets go in `.dev.vars` (gitignored; see `.dev.vars.example`).
`data/` and `models/*.keras` are gitignored — `data/` is symlinked to `~/data/wxwords/data`.

> A previous `ADMIN_TOKEN` sat in `wrangler.json` `vars` across 13 commits on the
> public GitHub repo for ~2.5 months. It has been rotated. Keep secrets out of the tree.
