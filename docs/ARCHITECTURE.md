# Architecture

## Services
- api: HTTP endpoints for seed, search, and fetch-by-URL
- api: Admin status endpoint (token-protected)
- crawler: async worker that fetches pages, extracts main content, normalizes to Markdown, stores in S3, and indexes in Typesense

## Data flow
1) API seeds URLs into Redis queue
2) crawler pulls URL + depth
3) crawler respects robots.txt (default), host rate limits, and max depth
4) crawler stores Markdown in S3-compatible storage
5) crawler upserts doc metadata + content into Typesense
6) API serves search results and markdown retrieval

## Storage
- Object store: S3-compatible bucket (MinIO for local, R2/S3 in prod)
- Search index: Typesense
- Queue + seen set: Redis
- Stats: Redis counters (crawl:stats:*)

## Notes
- The crawler is stateless; scaling is adding more workers
- Dedup is by URL hash (can be extended with content hash)
