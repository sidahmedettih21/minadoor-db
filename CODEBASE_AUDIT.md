# CODEBASE AUDIT - MinaDoor Travel DB

Date: 2026-05-26
Reviewer: Codex
Confidence score: 0.86

## Architecture summary

MinaDoor is a small FastAPI application with SQLAlchemy async models, Alembic migrations, PostgreSQL, Redis-backed import/export job state, a static Alpine.js frontend, and nginx serving/proxying the UI.

Actual runtime shape:

```text
Browser
  -> nginx :80
      -> static files from frontend/
      -> /api/* proxy to api:8000
  -> FastAPI app
      -> PostgreSQL for users, travel types, clients, audit_log migration table
      -> Redis for rate limits, refresh-token blocklist, import preview cache, export job status
      -> local filesystem for generated exports
```

The README claims a production-style app with JWT auth, refresh rotation, client CRUD, import/export, and admin management. The code does not currently meet that claim. Authentication is intentionally disabled in the backend dependency layer and frontend auto-login is enabled. Several core client/export endpoints reference a missing `Client.travel_type` relationship and likely fail at runtime. The nginx proxy and frontend API paths are inconsistent, so the app served through nginx cannot reliably reach the backend.

## Tech stack

Backend, from `backend/requirements.txt`:

- Python container base: `python:3.11-slim`
- FastAPI `0.111.0`
- Uvicorn `0.29.0`
- SQLAlchemy async `2.0.30`
- asyncpg `0.29.0`
- Alembic `1.13.1`
- Redis client `5.0.6`
- python-jose `3.3.0`
- passlib `1.7.4`
- bcrypt `4.1.3`
- python-multipart `0.0.9`
- openpyxl `3.1.2`
- WeasyPrint `61.1`
- python-magic `0.4.27`
- Pydantic `2.7.1`
- python-json-logger `2.0.7`
- pytest `8.2.0`
- httpx `0.27.0`

Infrastructure:

- Docker Compose
- PostgreSQL image `postgres:16` in compose, while README says PostgreSQL 15
- Redis image `redis:7`
- nginx image `nginx:alpine`

Frontend:

- Static HTML/CSS/JS
- Alpine.js `3.13.3` from CDN
- htmx `1.9.10` from CDN
- DOMPurify `3.0.6` from CDN, loaded twice
- Tailwind from CDN without a pinned version

## Identified gaps

- Authentication and authorization are not active. Backend dependencies return a hardcoded admin user for every protected request.
- Login is broken even if auth is re-enabled: it uses `db.get(User, email)` against a primary-key lookup, while OAuth2 form username is an email.
- Admin bootstrap is broken: `backend/manage.py` imports nonexistent `async_session`, and the Docker entrypoint never runs it.
- Initial migration seeds an invalid placeholder bcrypt hash for `admin@minadoor.com`.
- nginx strips `/api/` before proxying, but most frontend calls already target `/api/v1/*`; those calls become `/v1/*` upstream and 404.
- Frontend login/logout/download use `/api/api/v1/*`, while the generic API helper uses `/api/v1/*`.
- `Client.travel_type` relationship is missing from the model, but routers/services use `selectinload(Client.travel_type)` and `c.travel_type`.
- Pydantic v2 response serialization is incorrectly configured with `orm_mode = True`; models need `from_attributes = True`.
- Import preview accepts travel type text/code but confirm validates `travel_type_id` as an integer, making realistic imports fail.
- Export path has no strict format enum, no escaping for PDF HTML, no CSV/XLSX formula-injection protection, and no row limits.
- Health checks swallow exceptions and return HTTP 200 even when dependencies are degraded.
- Request ID middleware exists but is not registered.
- Tests mock out the database module globally and do not exercise a real database, real Redis, nginx routing, auth, or response serialization.
- No CI config, no type checking config, no lint config beyond a gitleaks pre-commit entry, no coverage gate.
- Docker hardening is incomplete: direct API port exposure, no TLS, no Redis auth, unpinned image digests, no service resource limits.

## Contract mismatches

- README default login says `admin@minadoor.com` / `admin123`, but migration seeds an invalid placeholder hash and `manage.py` does not run.
- README says all API endpoints are under `/api/v1`; health is mounted at `/health`.
- Frontend served through nginx calls `/api/v1/*`, but nginx forwards those as `/v1/*` because `proxy_pass http://api:8000/` strips the `/api/` prefix.
- Frontend login uses JSON, while `OAuth2PasswordRequestForm` expects form-encoded fields.
- Frontend has UI for editing travel types and users with PATCH/DELETE routes that do not exist in the backend.
- Frontend template links expect downloadable files, but `/api/v1/templates/{lang}` returns JSON only.
- Import preview returns only the first 50 preview rows, while confirm sends preview rows and relies on Redis cache for the complete dataset. If Redis cache is unavailable, only the first 50 rows are imported.
- Tests use travel type values like `umrah`, while the production schema requires integer `travel_type_id`.

## Security surface

- Public HTTP surface: nginx on port 80 and direct API on port 8000 in compose.
- Auth endpoints exist but are not effective because `get_current_user()` and `get_refresh_token_user()` bypass token validation.
- Refresh-token blocklist is written by rotation but not checked by the active dependency.
- JWT defaults are HS256 and a development fallback secret.
- Hardcoded DB password appears in `docker-compose.yml`.
- CSP is effectively disabled by allowing `default-src *`, `unsafe-inline`, and `unsafe-eval`.
- CDN scripts are loaded without subresource integrity.
- Redis has no authentication in compose.
- Import upload validation checks MIME and XLSX ZIP magic only; CSV content is not magic-byte validated and file parsing is synchronous.
- Exported PDF HTML interpolates user-controlled fields without HTML escaping.
- CSV/XLSX exports write user-controlled fields without formula neutralization.
- Audit log table exists in migration but application code never writes audit events.
- Structured logging exists but lacks request_id, user_id, event names, and consistent error context.

## Debt inventory

- `fix_all.sh` is a large file-overwriting script that contains stale assumptions and should not be kept as a production artifact.
- `minadoor_super_report.md` is generated state dumped into the repo and includes stale code/report content.
- `__pycache__` and `.pyc` files are tracked in git despite `.gitignore`.
- Pydantic v1-style validators and config are used under Pydantic v2.
- Several broad `except Exception` blocks silently continue or only log a warning.
- Frontend has many empty `catch (e) {}` blocks.
- Documentation contains mojibake/encoding artifacts in generated reports and some files.
- Tests are mostly parser/unit tests and do not validate deployed behavior.
- Model and migration drift exists: app model types/index names differ from migration, and migration includes `audit_log` with no ORM model.

## Run/local verification notes

- `python` is not available on PATH in this shell.
- Docker is not available on PATH, so compose startup could not be executed.
- Bundled Python could compile the backend app with `python -m compileall app`.
- Bundled Python does not have FastAPI, SQLAlchemy, or pytest installed, so pytest could not be executed in this environment.
- Bundled Node successfully parsed `frontend/js/app.js` with `node --check`.
- `gitleaks` and `pip-audit` are not installed locally.

