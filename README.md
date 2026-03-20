# ArmA Squads

A lightweight microservice that automatically generates and serves a `squad.xml` for Arma 3, synced live from a [PERSCOM](https://www.perscom.io/) roster.

Built as a replacement for the original [armasquads](https://github.com/ins0/armasquads) PHP application. Instead of manually managing members through a web UI, this service pulls your unit's active roster directly from PERSCOM and serves it automatically — no database, no manual updates.

---

## How it works

1. On startup, the service fetches all active personnel from the PERSCOM API
2. Each member with a valid Steam ID 64 is included in the generated `squad.xml`
3. A background task re-syncs on a configurable interval (default: every 5 minutes)
4. Arma 3 clients fetch `squad.xml` directly from the running service

---

## Requirements

- Docker and Docker Compose
- A PERSCOM API key (obtain from your PERSCOM administrator)
- Members must have their Steam ID 64 set in PERSCOM to appear in the XML

---

## Quick start

```bash
cd service
cp .env.example .env
# Edit .env — at minimum set PERSCOM_API_KEY and the SQUAD_* fields
nano .env
docker compose up -d
```

Verify it's working:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/squad.xml
```

Point your Arma 3 squad URL at `https://<your-domain>/squad.xml`.

---

## Configuration

All configuration is via environment variables. Copy `service/.env.example` to `service/.env` and edit it. The `.env` file is gitignored and never committed.

| Variable | Required | Default | Description |
|---|---|---|---|
| `PERSCOM_API_URL` | No | `https://api.1stcavalry.org` | Base URL of your PERSCOM API |
| `PERSCOM_API_KEY` | **Yes** | — | API key for authenticating with PERSCOM |
| `ACTIVE_STATUS_IDS` | No | `1` | Comma-separated PERSCOM status IDs to include (e.g. `1,2`) |
| `FILTER_UNIT_IDS` | No | _(all units)_ | Comma-separated unit IDs to restrict to. Leave blank for whole org |
| `SQUAD_TAG` | No | `1CAV` | Squad nick shown in-game (`<squad nick="...">`) |
| `SQUAD_NAME` | No | `1st Cavalry Division` | Full squad name |
| `SQUAD_EMAIL` | No | `admin@1stcavalry.org` | Contact email in squad.xml |
| `SQUAD_WEB` | No | `https://1stcavalry.org` | Squad website URL |
| `SQUAD_TITLE` | No | `1st Cavalry Division - Arma 3 MilSim` | Squad title/motto |
| `LOGO_FILENAME` | No | _(none)_ | Filename without extension of a `.paa` logo placed in `service/static/` |
| `SYNC_INTERVAL` | No | `300` | Seconds between automatic PERSCOM re-syncs |
| `SYNC_KEY` | No | `change-me` | Secret for authenticating manual `POST /sync` requests |

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/squad.xml` | The squad file consumed by Arma 3 |
| `GET` | `/squad.dtd` | DTD referenced by squad.xml |
| `GET` | `/{name}.paa` | PAA logo file served from `service/static/` |
| `GET` | `/health` | Returns sync status and member count (JSON) |
| `POST` | `/sync` | Trigger an immediate re-sync. Requires `X-Sync-Key: <SYNC_KEY>` header |

---

## squad.xml field mapping

| Arma 3 field | Source in PERSCOM |
|---|---|
| `<member id="...">` | `steamId64` |
| `<member nick="...">` | `rank.abbreviation` + `name` (e.g. `SGT V. Handberg`) |
| `<name>` | `name` |
| `<email>` | `email` |
| `<remark>` | `position.name` (e.g. `Squad Leader`) |

Members are sorted by `rank.rankOrder` (highest rank first). Only members with a valid 17-digit Steam ID 64 beginning with `7656119` are included.

---

## Adding a logo

1. Convert your logo to `.paa` format using [BI Tools](https://www.bohemia.net/community/projects/BI-tools)
2. Place the file in `service/static/`, e.g. `service/static/1cav.paa`
3. Set `LOGO_FILENAME=1cav` in your `.env`
4. Restart the service — the XML will include `<picture>1cav.paa</picture>` and the file will be served at `/1cav.paa`

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for reverse proxy configuration (Nginx, Caddy) and production hardening notes.

---

## License

[MIT](LICENSE.txt)
