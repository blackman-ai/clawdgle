import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass
class Config:
    api_user_agent: str

    crawl_concurrency: int
    crawl_timeout_secs: int
    crawl_max_bytes: int
    crawl_max_depth: int
    crawl_allow_domains: list[str]
    crawl_respect_robots: bool
    crawl_polite_delay_secs: int

    redis_url: str

    typesense_host: str
    typesense_port: int
    typesense_protocol: str
    typesense_api_key: str
    typesense_collection: str

    s3_endpoint_url: str
    s3_region: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_prefix: str

    admin_token: str
    admin_basic_user: str
    admin_basic_pass: str
    donate_url: str


def load_config() -> Config:
    allow_domains = os.getenv("CRAWL_ALLOW_DOMAINS", "").strip()
    allow_domains_list = [d.strip() for d in allow_domains.split(",") if d.strip()]

    return Config(
        api_user_agent=os.getenv("API_USER_AGENT", "ClawdgleBot/0.1"),

        crawl_concurrency=_get_int("CRAWL_CONCURRENCY", 4),
        crawl_timeout_secs=_get_int("CRAWL_TIMEOUT_SECS", 20),
        crawl_max_bytes=_get_int("CRAWL_MAX_BYTES", 5_000_000),
        crawl_max_depth=_get_int("CRAWL_MAX_DEPTH", 2),
        crawl_allow_domains=allow_domains_list,
        crawl_respect_robots=_get_bool("CRAWL_RESPECT_ROBOTS", True),
        crawl_polite_delay_secs=_get_int("CRAWL_POLITE_DELAY_SECS", 1),

        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),

        typesense_host=os.getenv("TYPESENSE_HOST", "localhost"),
        typesense_port=_get_int("TYPESENSE_PORT", 8108),
        typesense_protocol=os.getenv("TYPESENSE_PROTOCOL", "http"),
        typesense_api_key=os.getenv("TYPESENSE_API_KEY", "typesense123"),
        typesense_collection=os.getenv("TYPESENSE_COLLECTION", "clawdgle_docs"),

        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
        s3_region=os.getenv("S3_REGION", "us-east-1"),
        s3_access_key=os.getenv("S3_ACCESS_KEY", "minioadmin"),
        s3_secret_key=os.getenv("S3_SECRET_KEY", "minioadmin"),
        s3_bucket=os.getenv("S3_BUCKET", "clawdgle"),
        s3_prefix=os.getenv("S3_PREFIX", "markdown/"),

        admin_token=os.getenv("ADMIN_TOKEN", ""),
        admin_basic_user=os.getenv("ADMIN_BASIC_USER", ""),
        admin_basic_pass=os.getenv("ADMIN_BASIC_PASS", ""),
        donate_url=os.getenv("DONATE_URL", ""),
    )
