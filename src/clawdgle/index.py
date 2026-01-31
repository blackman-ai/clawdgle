import time
from typing import Optional

import typesense

from clawdgle.config import Config


def make_typesense_client(cfg: Config):
    return typesense.Client(
        {
            "nodes": [
                {
                    "host": cfg.typesense_host,
                    "port": cfg.typesense_port,
                    "protocol": cfg.typesense_protocol,
                }
            ],
            "api_key": cfg.typesense_api_key,
            "connection_timeout_seconds": 5,
        }
    )


def ensure_collection(cfg: Config, client) -> None:
    try:
        client.collections[cfg.typesense_collection].retrieve()
        return
    except Exception:
        pass

    schema = {
        "name": cfg.typesense_collection,
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "url", "type": "string"},
            {"name": "title", "type": "string", "optional": True},
            {"name": "content", "type": "string", "optional": True},
            {"name": "s3_key", "type": "string"},
            {"name": "fetched_at", "type": "int64"},
        ],
        "default_sorting_field": "fetched_at",
    }
    client.collections.create(schema)


def upsert_document(cfg: Config, client, doc: dict) -> None:
    client.collections[cfg.typesense_collection].documents.upsert(doc)


def search(cfg: Config, client, q: str, page: int = 1, per_page: int = 10) -> dict:
    return client.collections[cfg.typesense_collection].documents.search(
        {
            "q": q,
            "query_by": "title,content,url",
            "page": page,
            "per_page": per_page,
        }
    )


def find_by_url(cfg: Config, client, url: str) -> Optional[dict]:
    results = client.collections[cfg.typesense_collection].documents.search(
        {
            "q": url,
            "query_by": "url",
            "filter_by": f"url:={url}",
            "per_page": 1,
        }
    )
    hits = results.get("hits", [])
    if not hits:
        return None
    return hits[0]["document"]


def now_ts() -> int:
    return int(time.time())
