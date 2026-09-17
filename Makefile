# WxWords convenience targets — no Docker needed.
# Website work needs only python3 (and Node 22 for the Worker targets).
# Model training runs in the maintainer's `dev` container, not from here.

.PHONY: serve build preview worker-dev worker-deploy worker-tail test captures

# Serve the working tree at http://localhost:8080 (port 8080 is required — Worker CORS)
serve:
	python3 -m http.server 8080

# Build exactly what Cloudflare publishes into dist/
build:
	bash scripts/build_site.sh

# Build, then serve dist/ — catches pages missing from the allowlist
preview: build
	python3 -m http.server 8080 -d dist

# Run the Worker locally at http://localhost:8787
worker-dev:
	cd worker && npx wrangler dev

# Deploy the Worker — LIVE. Agree the change first.
worker-deploy:
	cd worker && npm test && npx wrangler deploy

# Tail live Worker logs
worker-tail:
	cd worker && npx wrangler tail

# Worker unit tests (CORS allowlist)
test:
	cd worker && npm test

# List recent webcam captures via the Worker API
captures:
	curl -s "https://wxwords-upload-api.tahliasc.workers.dev/captures?days=7" | python3 -m json.tool
