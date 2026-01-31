# clawdgle

A markdown-first, agent-optimized web indexer: crawl -> normalize -> store -> search.

## What this is
- Crawls pages (polite + robots.txt aware by default)
- Extracts main content and normalizes to Markdown
- Stores Markdown in S3-compatible object storage
- Indexes text + metadata in a search engine
- Serves a simple agent-friendly API (search + fetch by URL)

## Quickstart (local)
1) Copy env defaults:
   - `cp .env.example .env`
2) Start services:
   - `docker compose up --build`
3) Seed URLs:
   - `curl -X POST localhost:8080/seed -H 'Content-Type: application/json' -d '{"urls":["https://example.com"],"depth":1}'`
4) Search:
   - `curl 'localhost:8080/search?q=example'`
5) Fetch markdown by URL:
   - `curl 'localhost:8080/doc?url=https://example.com'`
6) Admin status (if `ADMIN_TOKEN` set):
   - `curl 'localhost:8080/admin?token=YOUR_TOKEN'`
7) Admin UI:
   - `open http://localhost:8080/admin-ui`
8) Admin stats JSON:
   - `curl 'localhost:8080/stats?token=YOUR_TOKEN'`

## Design goals
- Markdown-first storage, usable by autonomous agents
- Cheap storage and index; compatible with cloud object stores
- Continuous, polite crawling with rate limits
- Open-source and auditable

## Repo structure
- `services/api`: FastAPI service for search + fetch + seed
- `services/crawler`: worker that fetches, extracts, stores, indexes
- `src/clawdgle`: shared library
- `docs`: architecture and runbook

## Deploy
- See `docs/DEPLOY_HETZNER.md` for the cheapest single-node deployment.

## Compliance
Default behavior is to respect `robots.txt` and basic crawl delays. Optional overrides should be explicit and opt-in.

## Cloudflare R2 (prod)
- Set `S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com`
- Set `S3_REGION=auto`
- Set `S3_ACCESS_KEY` and `S3_SECRET_KEY` to your R2 credentials

## Admin auth (optional)
- `ADMIN_TOKEN` is required to access `/admin`, `/stats`, and `/admin-ui`
- Optional Basic Auth gate: set `ADMIN_BASIC_USER` and `ADMIN_BASIC_PASS`

## License
TBD
