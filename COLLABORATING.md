# Collaborating on WxWords — website development

For contributors working on the **website and content**. Model training is not
covered here and needs none of its tooling — no Docker, no TensorFlow, no GPU.

---

## How the site works

```
 private GitHub repo ──► Cloudflare Pages ──► https://wxwords.pages.dev
   (main branch)          (runs scripts/build_site.sh)   │  calls
        │                                                ▼
        └─ worker/  ──(wrangler deploy)──►  Cloudflare Worker  ──►  R2 bucket
                                            wxwords-upload-api      wxwords-uploads
                                            (uploads, moderation,   (images, labels,
                                             webcam captures)        webcam captures)
```

| Piece | What it is | How it goes live |
|---|---|---|
| **Site** | static HTML/JS in the repo root: `index.html`, `words.html`, `upload.html`, `review.html` | **merging to `main`** — Cloudflare Pages rebuilds within a minute or two |
| **Model** | `models/tfjs/` — the in-browser cloud classifier | same as the site; it's just files |
| **Worker** | `worker/` — the upload/moderation API | `npx wrangler deploy`, separately |
| **Storage** | R2 bucket `wxwords-uploads` | managed through the Worker and the Cloudflare dashboard |

> ⚠️ **`main` is production.** Anything merged to `main` is public within minutes.
> Work on a branch and merge when it's ready.

### Only allowlisted files are published

The repo is **private** and also holds training code, the Worker source and notes.
Cloudflare publishes only what `scripts/build_site.sh` copies into `dist/` —
everything else stays private.

**Adding a new page or asset? Add it to `PAGES` or `ASSETS` in
`scripts/build_site.sh`**, or it will work locally and 404 on the live site.

### Every pull request gets a live preview

Cloudflare builds each branch at its own URL and posts it on the pull request, e.g.
`https://feature-glossary.wxwords.pages.dev`. Review the change there before
merging — it talks to the real Worker, so moderation actions are still live.

---

## 1. GitHub access

**Maintainer:** repo → Settings → Collaborators → *Add people* → their GitHub
username. Write access is enough. The repo is **private**, so this invite is the
only way in.

**Contributor:**

1. Accept the invitation (email, or github.com/notifications)
2. Add an SSH key to your GitHub account — GitHub no longer accepts passwords for git:
   ```bash
   ssh-keygen -t ed25519 -C "your-github-username"
   cat ~/.ssh/id_ed25519.pub     # paste at github.com/settings/keys
   ssh -T git@github.com         # "Hi <you>! You've successfully authenticated"
   ```
3. Clone:
   ```bash
   git clone git@github.com:tahliasc/wxwords.git
   cd wxwords
   ```
4. **Use your GitHub noreply address for commits.** The repo was public for years and
   its history may be again; GitHub also refuses pushes that would expose a private
   email (error `GH007`). Find yours at
   github.com/settings/emails — it looks like `12345+you@users.noreply.github.com`:
   ```bash
   git config user.email "12345+you@users.noreply.github.com"
   ```

---

## 2. Local development

You need **git, a browser, and Python 3** (for a throwaway web server). That's it.

```bash
cd wxwords
python3 -m http.server 8080
```

Open **http://localhost:8080**. Edit, refresh, repeat.

To see **exactly what will be published** (catches pages missing from the
allowlist):

```bash
bash scripts/build_site.sh
python3 -m http.server 8080 -d dist
```

**Use port 8080 exactly.** The Worker only accepts requests from the live site, its preview
URLs, and `localhost:8080` / `127.0.0.1:8080`. Any other port gets blocked by CORS, and
uploads and the review page will fail in confusing ways.

Your local copy talks to the **live** Worker and **live** R2 bucket. Browsing is
harmless; submitting uploads or approving/rejecting in `review.html` changes real
data.

### Not needed for website work

The repo also contains training code (`train_*.py`, `presort_*.py`,
`requirements.txt`, `data/`, the Docker files). Ignore it. `data/` isn't in git
anyway — it's ~4 GB and stays with the maintainer.

### Optional — VS Code / Codespaces

`.devcontainer/` gives a light Node 22 + Python environment with port 8080
forwarded. In VS Code: *Reopen in Container*. On github.com: *Code → Codespaces →
Create*. Nothing to install locally with Codespaces.

---

## 3. Cloudflare access

Only needed to **deploy the Worker** or **inspect the R2 bucket**. Pure website edits
don't need it.

**Maintainer:** Cloudflare dashboard → *Manage Account → Members → Invite*. Grant the
narrowest role that covers the work:

| They need to… | Role |
|---|---|
| look at uploads/captures in R2 | **Cloudflare R2 Admin** or R2 read-only |
| deploy Worker changes | **Workers Admin** |
| nothing on Cloudflare | no invite — local dev still works |

Avoid *Administrator* — it covers billing, DNS and every other product on the account.

**Contributor**, once invited:

```bash
# needs Node 22+
cd worker
npx wrangler login          # browser sign-in with YOUR Cloudflare account
npx wrangler dev            # local Worker at http://localhost:8787
npx wrangler deploy         # LIVE — only after agreeing the change
npx wrangler tail           # live logs
```

Everyone uses their **own** Cloudflare login. Never share API tokens.

---

## 4. Content management

Moderation happens in the live site, with an admin token:

| Page | Does |
|---|---|
| `review.html` | approve / reject community uploads |
| `upload.html` | submit images (public) |

The token is a **Cloudflare Worker secret** (`ADMIN_TOKEN`). It is never in this
repo and must never be added to it — not in code, not in `wrangler.json`, not in a
commit message.

**Maintainer** shares it through a password manager or Signal — never email, chat or
an issue. If it's ever exposed, rotate it:

```bash
cd worker && npx wrangler secret put ADMIN_TOKEN     # prompts for the value
```

> Do **not** add `ADMIN_TOKEN` to `vars` in `wrangler.json`. A var and a secret with
> the same name collide, and the next `wrangler deploy` silently overwrites the
> secret.

For local Worker testing, put secrets in `worker/.dev.vars` (gitignored — see
`worker/.dev.vars.example`).

---

## 5. Working together

### Branches and pull requests

```bash
git switch -c feature/short-description     # branch off main
# ...edit, test at localhost:8080...
git add -p                                  # review what you're staging
git commit -m "Add Māori names to the cloud glossary"
git push -u origin feature/short-description
```

Then open a pull request on GitHub. The other person reviews; **merging is going
live**.

**Never push straight to `main`.** On this private repo GitHub can't technically block
it, so the rule is ours to keep: every change goes through a pull request.

- Keep PRs small — one page or one feature
- Pull before starting: `git switch main && git pull`
- Worker changes: say so in the PR, and agree who runs `wrangler deploy`
- Big binaries (images, models) — ask first; the repo is already large

### Before every push

```bash
git diff --cached
git diff --cached | grep -iE "token|secret|password|api_key|@gmail"   # must be empty
```

Never commit: `.env`, `.dev.vars`, tokens, personal email addresses, exported email
or personal data. `.gitignore` covers the known ones — check anyway.

### If something breaks live

1. **Fastest:** Cloudflare dashboard → Workers & Pages → `wxwords` → *Deployments* →
   pick the last good one → *Rollback*. Live in seconds.
2. Then fix the code: open the merged pull request on GitHub → *Revert* → merge the
   revert PR.
3. Worker: `npx wrangler rollback` restores the previous deployment.

### Content conventions

- Te Reo Māori: use macrons (ā ē ī ō ū) — never drop them or substitute
- Weather science: every claim needs a source; add it to `REFERENCES.md`
- Keep pages readable on a phone

---

## Maintainer checklist

- [ ] GitHub: add collaborator (Write) — the repo is private
- [ ] Branch protection is **not available** for private repos on GitHub Free, so
      "PRs only" is a working agreement, not an enforced rule. Cloudflare's
      one-click rollback is the safety net.
- [ ] Cloudflare: invite with a scoped role, if they deploy or inspect R2
- [ ] Share the admin token through a password manager or Signal
- [ ] Point them at this file
