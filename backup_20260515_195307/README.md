# MinaDoor Travel DB

Complete headless API + admin frontend for travel agency client management.

## Quick Start

```bash
cd minadoor
cp .env.example .env
docker-compose up -d
```

- API: http://localhost:8000
- Frontend: http://localhost
- API Docs: http://localhost:8000/docs

## Default Login
- Email: `admin@minadoor.com`
- Password: `admin123`

## Features
- JWT auth with refresh token rotation
- Client CRUD with fuzzy search (pg_trgm)
- Multi-language UI (EN/FR/AR) + RTL support
- Excel/CSV import with preview & validation
- Async export to XLSX/CSV/PDF
- Travel type & user management (admin)
- Batch client entry

## Stack
- FastAPI + SQLAlchemy async + PostgreSQL 15 + Redis
- Alpine.js + HTMX + Tailwind CSS
- Docker Compose + Nginx

## API
All endpoints under `/api/v1`. See OpenAPI docs at `/docs`.

## Database
Migrations via Alembic. Seeded with 5 travel types and 1 admin user.
