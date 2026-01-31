import json
from typing import Optional

import redis

from clawdgle.config import Config


def make_redis(cfg: Config) -> redis.Redis:
    return redis.Redis.from_url(cfg.redis_url, decode_responses=True)


def enqueue(r: redis.Redis, url: str, depth: int) -> None:
    payload = json.dumps({"url": url, "depth": depth})
    r.lpush("crawl:queue", payload)


def enqueue_suggestion(r: redis.Redis, payload: dict) -> None:
    r.lpush("suggest:queue", json.dumps(payload))


def list_suggestions(r: redis.Redis, limit: int = 50) -> list[dict]:
    items = r.lrange("suggest:queue", 0, max(0, limit - 1))
    results = []
    for item in items:
        try:
            results.append(json.loads(item))
        except json.JSONDecodeError:
            continue
    return results


def dequeue(r: redis.Redis) -> Optional[dict]:
    item = r.brpop("crawl:queue", timeout=5)
    if not item:
        return None
    _, payload = item
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def seen_key(url: str) -> str:
    return f"crawl:seen:{url}"


def mark_seen(r: redis.Redis, url: str) -> bool:
    return r.setnx(seen_key(url), 1)


def incr_stat(r: redis.Redis, name: str, inc: int = 1) -> None:
    r.incrby(f"crawl:stats:{name}", inc)


def get_stats(r: redis.Redis) -> dict:
    keys = r.keys("crawl:stats:*")
    stats = {}
    for key in keys:
        stats[key.replace("crawl:stats:", "")] = int(r.get(key) or 0)
    return stats


def set_heartbeat(r: redis.Redis, ts: int) -> None:
    r.set("crawl:heartbeat", ts, ex=120)


def get_heartbeat(r: redis.Redis) -> int:
    val = r.get("crawl:heartbeat")
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0
