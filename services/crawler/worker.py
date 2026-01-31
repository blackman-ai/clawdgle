import asyncio
import hashlib
import time
from urllib.parse import urlparse

import aiohttp

from clawdgle.config import load_config
from clawdgle.extract import discover_links, extract_markdown
from clawdgle.index import ensure_collection, make_typesense_client, now_ts, upsert_document
from clawdgle.queue import dequeue, enqueue, incr_stat, make_redis, mark_seen, set_heartbeat
from clawdgle.robots import is_allowed, crawl_delay
from clawdgle.storage import make_s3_client, put_markdown


async def fetch_html(session: aiohttp.ClientSession, url: str, timeout: int, max_bytes: int) -> str:
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        data = await resp.content.read(max_bytes)
        return data.decode("utf-8", errors="ignore")


def should_crawl_domain(cfg, url: str) -> bool:
    if not cfg.crawl_allow_domains:
        return True
    host = urlparse(url).netloc
    return any(host == d or host.endswith(f".{d}") for d in cfg.crawl_allow_domains)


def host_key(url: str) -> str:
    host = urlparse(url).netloc
    return f"crawl:host:{host}"


async def polite_wait(r, url: str, base_delay: int) -> None:
    key = host_key(url)
    last = r.get(key)
    now = time.time()
    delay = base_delay
    if last:
        try:
            last = float(last)
        except ValueError:
            last = 0
        if now - last < delay:
            await asyncio.sleep(delay - (now - last))
    r.set(key, time.time())


async def worker_loop():
    cfg = load_config()
    r = make_redis(cfg)
    s3 = make_s3_client(cfg)
    ts = make_typesense_client(cfg)
    ensure_collection(cfg, ts)

    timeout = aiohttp.ClientTimeout(total=cfg.crawl_timeout_secs)
    headers = {"User-Agent": cfg.api_user_agent}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while True:
            set_heartbeat(r, now_ts())
            item = dequeue(r)
            if not item:
                await asyncio.sleep(0.5)
                continue

            url = item.get("url")
            depth = int(item.get("depth", 0))
            if not url:
                continue

            if depth > cfg.crawl_max_depth:
                incr_stat(r, "skipped_max_depth")
                continue

            if not should_crawl_domain(cfg, url):
                incr_stat(r, "skipped_domain")
                continue

            if not mark_seen(r, url):
                incr_stat(r, "skipped_seen")
                continue

            if cfg.crawl_respect_robots and not is_allowed(url, cfg.api_user_agent):
                incr_stat(r, "skipped_robots")
                continue

            robots_delay = crawl_delay(url, cfg.api_user_agent) if cfg.crawl_respect_robots else 0
            await polite_wait(r, url, max(cfg.crawl_polite_delay_secs, robots_delay))

            try:
                html = await fetch_html(session, url, cfg.crawl_timeout_secs, cfg.crawl_max_bytes)
            except Exception:
                incr_stat(r, "fetch_errors")
                continue

            try:
                title, markdown = extract_markdown(html)
            except Exception:
                incr_stat(r, "extract_errors")
                continue

            s3_key = put_markdown(cfg, s3, url, markdown)
            incr_stat(r, "stored")

            doc = {
                "id": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                "url": url,
                "title": title or "",
                "content": markdown[:200000],
                "s3_key": s3_key,
                "fetched_at": now_ts(),
            }
            try:
                upsert_document(cfg, ts, doc)
            except Exception:
                incr_stat(r, "index_errors")
                pass
            else:
                incr_stat(r, "indexed")

            if depth < cfg.crawl_max_depth:
                for link in discover_links(url, html):
                    enqueue(r, link, depth + 1)
                incr_stat(r, "links_enqueued")


if __name__ == "__main__":
    asyncio.run(worker_loop())
