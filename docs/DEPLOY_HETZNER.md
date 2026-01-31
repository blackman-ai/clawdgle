# Hetzner Deployment (Cheapest Path)

This is a minimal, single-node deployment using Docker Compose.

## 1) Provision a VM
- Choose a small CX instance (shared vCPU).
- Ubuntu 22.04 LTS is a safe default.

## 2) Install Docker
```
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
Log out/in to apply group changes.

## 3) Clone and configure
```
git clone <your-repo-url> clawdgle
cd clawdgle
cp .env.example .env
```

Edit `.env`:
- Set `S3_ENDPOINT_URL` to your Cloudflare R2 endpoint
- Set `S3_REGION=auto`
- Set `S3_ACCESS_KEY` / `S3_SECRET_KEY`
- Set `ADMIN_TOKEN` to a strong value
- Optionally set `ADMIN_BASIC_USER` / `ADMIN_BASIC_PASS`
- Set `API_USER_AGENT` to include contact info

## 4) Start services
```
docker compose up --build -d
```

## 5) Verify
```
curl http://localhost:8080/health
```

## 6) Expose via Cloudflare
- Point your domain to the VM's IP.
- Add a DNS A record.
- Use Cloudflare proxy for inbound rate limiting.

## 7) Admin UI
- Visit `https://<your-domain>/admin-ui`
- Paste your `ADMIN_TOKEN`
