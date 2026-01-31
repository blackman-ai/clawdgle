# Runbook

## Local
- Configure `.env`
- `docker compose up --build`
- Seed via API and monitor logs

## Production checklist
- Use a managed Redis and Typesense cluster or self-host with persistence
- Use an S3-compatible object store (Cloudflare R2 is typically cheapest)
- Set a real `API_USER_AGENT` and compliance contact
- Configure rate limits and allowlist/denylist
- Add monitoring and alerting (queue depth, worker errors, fetch rate)
 - Set `ADMIN_TOKEN` for the admin status endpoint

## Scaling
- Increase crawler replicas to scale crawl throughput
- Add per-host rate limit tuning
- Add content hash dedupe to avoid re-indexing identical pages

## Compliance
- Default respects robots.txt and uses polite delays
- For exceptions, use explicit allowlists only

## Notes
- Cloudflare rate limiting applies to API traffic, not crawler egress. Crawler politeness still matters.
