import hashlib
from typing import Tuple

import boto3

from clawdgle.config import Config


def make_s3_client(cfg: Config):
    return boto3.client(
        "s3",
        endpoint_url=cfg.s3_endpoint_url,
        region_name=cfg.s3_region,
        aws_access_key_id=cfg.s3_access_key,
        aws_secret_access_key=cfg.s3_secret_key,
    )


def s3_key_for_url(cfg: Config, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"{cfg.s3_prefix}{digest}.md"


def put_markdown(cfg: Config, s3_client, url: str, markdown: str) -> str:
    key = s3_key_for_url(cfg, url)
    s3_client.put_object(
        Bucket=cfg.s3_bucket,
        Key=key,
        Body=markdown.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
    )
    return key


def get_markdown(cfg: Config, s3_client, key: str) -> str:
    resp = s3_client.get_object(Bucket=cfg.s3_bucket, Key=key)
    data = resp["Body"].read()
    return data.decode("utf-8")
