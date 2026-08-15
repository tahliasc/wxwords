# wxwords

Exploring Te Reo Māori language, mātauranga Māori and weather.

Root agreement: `~/code/CLAUDE.md`. Origin is Gitea; **GitHub pushes are manual**
— note that `github` here is a **public** repo, so nothing secret may enter the tree.

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

## Stack

- Python 3.11, TensorFlow 2.18, PyTorch, transformers
- Node 20, Wrangler, Playwright, GitHub CLI
- Docker image `wxwords-dev` — also serves the snowie project
- Ports **8080** (static site) / **8787** (wrangler dev)

```bash
docker compose up -d && docker compose exec dev bash   # or: make up / make shell
python -m http.server 8080                             # serve the site
cd worker && npx wrangler deploy                       # deploy the Worker
```

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
