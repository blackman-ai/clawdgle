import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx


def _robots_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed(url: str, user_agent: str, timeout: int = 10) -> bool:
    robots_url = _robots_url(url)
    rp = RobotFileParser()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(robots_url)
            if resp.status_code >= 400:
                return True
            rp.parse(resp.text.splitlines())
    except Exception:
        return True
    return rp.can_fetch(user_agent, url)


def crawl_delay(url: str, user_agent: str, timeout: int = 10) -> int:
    robots_url = _robots_url(url)
    rp = RobotFileParser()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(robots_url)
            if resp.status_code >= 400:
                return 0
            rp.parse(resp.text.splitlines())
    except Exception:
        return 0
    return rp.crawl_delay(user_agent) or 0
