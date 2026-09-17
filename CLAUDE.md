# wxwords

Exploring Te Reo Māori language, mātauranga Māori and weather.

**This repo is public, and has more than one contributor.** Nothing secret may
enter the tree. Website contributors: read `COLLABORATING.md` first.

**`main` is production** — GitHub Pages serves it at
https://tahliasc.github.io/wxwords/. Work on branches; merging is going live.

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
`Dockerfile.retired` and the stub `docker-compose.yml` are retired — ignore them.

- Site: static HTML/JS in the repo root; model in `models/tfjs/`
- Worker: `worker/` → `wxwords-upload-api`, R2 bucket `wxwords-uploads`
- **Port 8080 is required** — Worker CORS allows only the live site and
  `localhost:8080` / `127.0.0.1:8080`. 8787 is `wrangler dev`.

```bash
python3 -m http.server 8080                 # serve the site locally
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
