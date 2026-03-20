# Deployment Guide

This service is a single Docker container intended to run alongside your other unit services (website, PERSCOM, etc.) via Docker Compose.

---

## Standalone (development / testing)

```bash
cd service
docker compose up -d
```

The service listens on port `8080` by default.

---

## Integrating with an existing Docker Compose stack

Rather than running its own `docker compose`, add the service to your main stack's `docker-compose.yml`:

```yaml
services:
  armasquads:
    build: ./armasquads/service
    restart: unless-stopped
    env_file:
      - ./armasquads/service/.env
    volumes:
      - ./armasquads/service/static:/app/static:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    # Don't expose port directly — let the reverse proxy handle it
    expose:
      - "8080"
```

> Remove the `ports:` mapping from `service/docker-compose.yml` when using a reverse proxy — only expose the port to the proxy container, not to the host.

---

## Reverse proxy configuration

The service speaks plain HTTP. TLS termination should be handled by your reverse proxy.

### Nginx

```nginx
server {
    listen 443 ssl;
    server_name squads.1stcavalry.org;

    ssl_certificate     /etc/ssl/certs/1stcavalry.org.crt;
    ssl_certificate_key /etc/ssl/private/1stcavalry.org.key;

    location / {
        proxy_pass         http://armasquads:8080;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 10s;
    }
}
```

### Caddy

```caddy
squads.1stcavalry.org {
    reverse_proxy armasquads:8080
}
```

Caddy handles TLS automatically via Let's Encrypt.

---

## Environment variables in production

Never commit `.env` to version control. In production, pass secrets via:

- **Docker secrets** (Swarm) — mount as `/run/secrets/<name>` and reference in config
- **Environment variables** injected by your CI/CD pipeline
- **A `.env` file** on the host machine, kept out of the repo (already gitignored)

---

## Manual sync

To force an immediate re-sync without restarting the container:

```bash
curl -s -X POST https://squads.1stcavalry.org/sync \
  -H "X-Sync-Key: your-sync-key-here"
```

This is useful after a mass rank change or roster update in PERSCOM.

---

## Health checks

The `/health` endpoint returns JSON and is suitable for use with Docker, Kubernetes liveness probes, or an uptime monitor:

```json
{
  "status": "ok",
  "last_sync": "2026-03-20T12:00:00+00:00",
  "last_error": null,
  "member_count": 47
}
```

`status` will be `"starting"` until the first sync completes (typically within a few seconds of container start).

---

## Updating

```bash
cd service
docker compose pull   # if using a registry
docker compose up -d --build
```

No database migrations or state to manage — the service is stateless. All data comes from PERSCOM.
