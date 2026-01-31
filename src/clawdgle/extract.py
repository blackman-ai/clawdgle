from typing import Iterable, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from readability import Document
from markdownify import markdownify as md


def extract_markdown(html: str) -> Tuple[str, str]:
    doc = Document(html)
    title = doc.short_title()
    cleaned_html = doc.summary(html_partial=True)
    markdown = md(cleaned_html, heading_style="ATX")
    return title, markdown


def discover_links(base_url: str, html: str) -> Iterable[str]:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        href = href.strip()
        if href.startswith("#"):
            continue
        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        yield url
