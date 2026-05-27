# WxWords convenience targets
# Run inside the dev container or on the host with docker compose installed.

.PHONY: build up shell serve worker-deploy worker-tail captures clean

# Build the image (run once or after Dockerfile changes)
build:
	docker compose build

# Start the dev container in the background
up:
	docker compose up -d

# Open a bash shell inside the running container
shell:
	docker compose exec dev bash

# Start the static site server (run inside container or via `make`)
serve:
	docker compose exec dev python -m http.server 8080

# Deploy the Cloudflare Worker
worker-deploy:
	docker compose exec dev sh -c "cd worker && npx wrangler deploy"

# Tail Worker logs in real time
worker-tail:
	docker compose exec dev sh -c "cd worker && npx wrangler tail"

# List current webcam captures via the Worker API
captures:
	curl -s "https://wxwords-upload-api.tahliasc.workers.dev/captures?days=7" | python3 -m json.tool

# Stop and remove the container (volumes preserved)
down:
	docker compose down

# Stop and remove EVERYTHING including data/auth volumes
clean:
	docker compose down -v
