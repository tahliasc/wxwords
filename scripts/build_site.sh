#!/usr/bin/env bash
#
# Assemble the PUBLIC website into dist/.
#
# Run by Cloudflare Pages on every push:
#   Build command:           bash scripts/build_site.sh
#   Build output directory:  dist
#
# Why an allowlist: the repo is private and also holds training code, the
# Worker source, notes and config. Publishing the repo root would expose all
# of it at <site>/CLAUDE.md, <site>/worker/src/index.js, and so on. Only the
# files below are served. A new page or asset must be added here to go live.
#
# Local preview of exactly what will be published:
#   bash scripts/build_site.sh && python3 -m http.server 8080 -d dist

set -euo pipefail

cd "$(dirname "$0")/.."
OUT=dist

# ── Public pages ─────────────────────────────────────────────────────────
PAGES=(
    index.html
    words.html
    upload.html
    review.html          # admin moderation — protected by the Worker's token
)

# ── Public assets ────────────────────────────────────────────────────────
ASSETS=(
    models/sky_mask.json
    models/sky_mask.png
    models/tfjs          # in-browser classifier (directory)
)

# ── Deliberately NOT published ───────────────────────────────────────────
#   sort_review.html, sort_review_webcam.html
#       internal training-data tools; load multi-MB local prediction files
#   data/weather_words.json   (needed by words.html)
#       mātauranga Māori with iwi / hapū / kaikōrero attribution — publishing
#       is a cultural decision, pending. Not tracked in git either.
#   everything else: training code, worker/, notes, config

rm -rf "$OUT"
mkdir -p "$OUT"

missing=0
for f in "${PAGES[@]}" "${ASSETS[@]}"; do
    if [[ ! -e "$f" ]]; then
        echo "ERROR: $f is listed but does not exist" >&2
        missing=1
        continue
    fi
    mkdir -p "$OUT/$(dirname "$f")"
    cp -R "$f" "$OUT/$f"
done
[[ $missing -eq 0 ]] || exit 1

# Never publish anything secret-shaped, even if it slips into an asset dir.
if find "$OUT" \( -name '.env*' -o -name '.dev.vars*' -o -name '*.pem' -o -name '*.key' \) \
        | grep -q .; then
    echo "ERROR: secret-like file found in $OUT — refusing to publish" >&2
    exit 1
fi

echo "Built $OUT/: $(find "$OUT" -type f | wc -l) files, $(du -sh "$OUT" | cut -f1)"
