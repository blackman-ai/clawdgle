import base64

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from clawdgle.config import load_config
from clawdgle.index import ensure_collection, find_by_url, make_typesense_client, search
from clawdgle.queue import (
    enqueue,
    enqueue_suggestion,
    get_heartbeat,
    get_stats,
    list_suggestions,
    make_redis,
)
from clawdgle.storage import get_markdown, make_s3_client

app = FastAPI(title="clawdgle", version="0.1")

cfg = load_config()
redis_client = make_redis(cfg)
ts_client = make_typesense_client(cfg)
ensure_collection(cfg, ts_client)
s3_client = make_s3_client(cfg)


class SeedRequest(BaseModel):
    urls: list[str]
    depth: int = 1


class SuggestRequest(BaseModel):
    url: str
    reason: str | None = None
    contact: str | None = None


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>clawdgle</title>
    <style>
      body { font-family: sans-serif; margin: 40px; }
      input { width: 60%; padding: 10px; font-size: 16px; }
      button { padding: 10px 14px; font-size: 16px; }
    </style>
  </head>
  <body>
    <h1>clawdgle</h1>
    <form action="/search" method="get">
      <input name="q" placeholder="Search markdown index" />
      <button type="submit">Search</button>
    </form>
    <h2>Ingest a URL</h2>
    <input id="suggest-url" placeholder="https://example.com" />
    <button id="suggest-send">Submit</button>
    <div id="suggest-status"></div>
    <p><a href="/donate">Donate</a></p>
    <script>
      const sUrl = document.getElementById("suggest-url");
      const sBtn = document.getElementById("suggest-send");
      const sStatus = document.getElementById("suggest-status");
      sBtn.addEventListener("click", async () => {
        sStatus.textContent = "Submitting...";
        try {
          const resp = await fetch("/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: sUrl.value })
          });
          if (!resp.ok) {
            sStatus.textContent = "Error: " + resp.status;
            return;
          }
          sStatus.textContent = "Submitted.";
          sUrl.value = "";
        } catch (err) {
          sStatus.textContent = "Error: " + err;
        }
      });
    </script>
  </body>
</html>"""


def _basic_auth_ok(request: Request) -> bool:
    if not cfg.admin_basic_user or not cfg.admin_basic_pass:
        return True
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
    except Exception:
        return False
    user, _, pw = decoded.partition(":")
    return user == cfg.admin_basic_user and pw == cfg.admin_basic_pass


def _token_ok(request: Request) -> bool:
    if not cfg.admin_token:
        return False
    token = request.headers.get("x-admin-token") or request.query_params.get("token") or ""
    return token == cfg.admin_token


def _admin_ok(request: Request) -> bool:
    return _token_ok(request) and _basic_auth_ok(request)


@app.get("/admin")
async def admin(request: Request):
    if not _admin_ok(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    stats = get_stats(redis_client)
    queue_depth = redis_client.llen("crawl:queue")
    heartbeat_ts = get_heartbeat(redis_client)
    return {"stats": stats, "queue_depth": queue_depth, "crawler_heartbeat": heartbeat_ts}


@app.get("/stats")
async def stats(request: Request):
    if not _admin_ok(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    stats = get_stats(redis_client)
    queue_depth = redis_client.llen("crawl:queue")
    heartbeat_ts = get_heartbeat(redis_client)
    return {"stats": stats, "queue_depth": queue_depth, "crawler_heartbeat": heartbeat_ts}


@app.get("/suggestions")
async def suggestions(request: Request, limit: int = 50):
    if not _admin_ok(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"items": list_suggestions(redis_client, limit=limit)}


@app.get("/admin-ui", response_class=HTMLResponse)
async def admin_ui():
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>clawdgle admin</title>
    <style>
      body { font-family: sans-serif; margin: 40px; }
      input { width: 320px; padding: 8px; font-size: 14px; }
      button { padding: 8px 12px; font-size: 14px; }
      pre { background: #f5f5f5; padding: 12px; }
    </style>
  </head>
  <body>
    <h1>clawdgle admin</h1>
    <p>Enter your admin token to view crawler status.</p>
    <input id="token" placeholder="Admin token" />
    <div style="margin-top: 8px;">
      <input id="user" placeholder="Basic auth user (optional)" />
      <input id="pass" type="password" placeholder="Basic auth pass (optional)" />
    </div>
    <button id="load">Load status</button>
    <label style="margin-left: 10px;">
      <input id="auto" type="checkbox" /> Auto refresh (10s)
    </label>
    <div id="status">Status: unknown</div>
    <div id="updated">Last updated: never</div>
    <pre id="output">No data yet.</pre>
    <script>
      const btn = document.getElementById("load");
      const token = document.getElementById("token");
      const out = document.getElementById("output");
      const status = document.getElementById("status");
      const updated = document.getElementById("updated");
      const auto = document.getElementById("auto");
      const user = document.getElementById("user");
      const pass = document.getElementById("pass");
      let timer = null;

      async function loadStatus() {
        out.textContent = "Loading...";
        status.textContent = "Status: loading...";
        const headers = { "x-admin-token": token.value || "" };
        if (user.value && pass.value) {
          const basic = btoa(user.value + ":" + pass.value);
          headers["authorization"] = "Basic " + basic;
        }
        try {
          const resp = await fetch("/admin", { headers });
          if (!resp.ok) {
            out.textContent = "Error: " + resp.status + " " + resp.statusText;
            status.textContent = "Status: error";
            return;
          }
          const data = await resp.json();
          out.textContent = JSON.stringify(data, null, 2);
          const now = Math.floor(Date.now() / 1000);
          const hb = data.crawler_heartbeat || 0;
          const age = hb ? (now - hb) : 999999;
          status.textContent = age <= 120 ? "Status: crawler active" : "Status: crawler stale";
          updated.textContent = "Last updated: " + new Date().toLocaleString();
        } catch (err) {
          out.textContent = "Error: " + err;
          status.textContent = "Status: error";
        }
      }

      btn.addEventListener("click", loadStatus);
      auto.addEventListener("change", () => {
        if (auto.checked) {
          loadStatus();
          timer = setInterval(loadStatus, 10000);
        } else if (timer) {
          clearInterval(timer);
          timer = null;
        }
      });
    </script>
  </body>
</html>"""


@app.post("/seed")
async def seed(req: SeedRequest):
    for url in req.urls:
        enqueue(redis_client, url, req.depth)
    return {"queued": len(req.urls)}


@app.post("/ingest")
async def ingest(req: SuggestRequest):
    enqueue(redis_client, req.url, 0)
    enqueue_suggestion(
        redis_client,
        {"url": req.url, "reason": req.reason or "", "contact": req.contact or ""},
    )
    return {"ok": True, "queued": req.url}


@app.get("/donate")
async def donate():
    if cfg.donate_url:
        return RedirectResponse(url=cfg.donate_url, status_code=307)
    raise HTTPException(status_code=404, detail="Donate URL not configured")


@app.get("/search")
async def search_endpoint(q: str, page: int = 1, per_page: int = 10):
    results = search(cfg, ts_client, q, page=page, per_page=per_page)
    return results


@app.get("/doc")
async def doc(url: str):
    doc = find_by_url(cfg, ts_client, url)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    s3_key = doc.get("s3_key")
    if not s3_key:
        raise HTTPException(status_code=500, detail="Missing storage key")
    markdown = get_markdown(cfg, s3_client, s3_key)
    return {
        "url": doc.get("url"),
        "title": doc.get("title"),
        "markdown": markdown,
        "fetched_at": doc.get("fetched_at"),
    }
