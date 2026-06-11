# SaaS Reservation Platform

Multi-tenant SaaS reservation platform supporting Hotels, Medical Clinics, Dental Offices, Gyms, Beauty Salons, Coworking Spaces, Event Venues, and Professional Services.

---

## Architecture

- **Pattern**: Clean Architecture + Domain-Driven Design + CQRS
- **Multi-tenancy**: Shared schema with `tenant_id` isolation per request
- **API**: REST with versioning (`/api/v1/`)
- **Async processing**: Celery + Redis (notifications, reminders, auto-completion)

```
reservation-management-platform/
├── backend/                # FastAPI + Python 3.13
│   ├── app/
│   │   ├── core/           # Config, database, security, logging
│   │   ├── domain/         # Entities, value objects, events, repository interfaces
│   │   ├── application/    # Services, DTOs, commands, queries
│   │   ├── infrastructure/ # SQLAlchemy models, repositories, Redis, Celery
│   │   ├── api/            # FastAPI routers, middleware, exception handlers
│   │   └── workers/        # Celery tasks
│   ├── alembic/            # Database migrations
│   └── tests/              # Unit and integration tests
├── frontend/               # React 18 + TypeScript + Vite + Tailwind
│   └── src/
│       ├── components/     # Reusable UI components
│       ├── pages/          # Route-level pages (Dashboard, Reservations, Resources, Reports, Settings)
│       ├── hooks/          # React Query data hooks
│       ├── store/          # Zustand state (auth)
│       └── services/api/   # Axios API clients
├── infrastructure/
│   ├── nginx/              # Reverse proxy config
│   ├── prometheus/         # Metrics scraping
│   ├── grafana/            # Dashboards + provisioning
│   └── loki/               # Log aggregation
├── tests/
│   └── postman/            # Postman/Apidog collection v2.1 + environment
├── scripts/
│   └── init-db.sql
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Tech Stack

| Layer          | Technology                                           |
|----------------|------------------------------------------------------|
| Backend        | Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic        |
| Database       | PostgreSQL 16                                        |
| Cache / Broker | Redis 7                                              |
| Task Queue     | Celery 5 + Celery Beat + Flower                      |
| Frontend       | React 18, TypeScript, Vite, Tailwind CSS             |
| State          | Zustand, TanStack Query v5                           |
| Auth           | JWT (access + refresh tokens), bcrypt cost 12        |
| Proxy          | Nginx 1.27                                           |
| Monitoring     | Prometheus, Grafana, Loki, Promtail                  |
| Testing        | Pytest, Postman/Apidog collection                    |
| CI/CD          | GitHub Actions                                       |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2+

### Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set JWT secrets and passwords

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Seed super admin (dev only)
curl -X POST http://localhost:8000/api/v1/dev/setup \
  -H "X-Dev-Key: dev-secret-key-change-me"

# 5. Access
#    Frontend:   http://localhost:3000
#    API Docs:   http://localhost:8000/api/docs
#    Grafana:    http://localhost:3001  (admin / admin)
#    Flower:     http://localhost:5555
#    MailHog:    http://localhost:8025
```

---

## Dev Endpoints

Protected by `X-Dev-Key` header (set `DEV_API_KEY` in `.env`, default `dev-secret-key-change-me`).

| Endpoint | Description |
|---|---|
| `POST /api/v1/dev/setup` | Create super admin (`superadmin@test.com` / `SuperAdmin1234!`) |
| `POST /api/v1/dev/activate-all` | Skip email verification for all pending users |
| `GET /api/v1/dev/verification-token?email=` | Retrieve email verification token |
| `GET /api/v1/dev/reset-token?email=` | Retrieve password reset token |

---

## API Overview

Base URL: `http://localhost:8000/api/v1`  
Interactive docs: `http://localhost:8000/api/docs`

| Module         | Endpoints |
|----------------|-----------|
| Authentication | `POST /auth/register` `/login` `/logout` `/refresh` `/verify-email` |
|                | `POST /auth/forgot-password` `/reset-password` `/change-password` |
|                | `GET /auth/me` |
| Tenants        | `POST /tenants` `GET /tenants` `GET/PATCH /tenants/{id}` |
|                | `PATCH /tenants/{id}/settings` |
| Resources      | `POST /resources` `GET /resources` `GET/PATCH/DELETE /resources/{id}` |
| Reservations   | `POST /reservations` `GET /reservations` `GET /reservations/{id}` |
|                | `GET /reservations/availability` |
|                | `POST /reservations/{id}/confirm` `/cancel` |
| Reports        | `GET /reports/daily` `/reports/summary` |
| Health         | `GET /health` `/ready` |

---

## Testing

Import the Postman collection and environment from `tests/postman/`:

- `reservation_platform.postman_collection.json` — all endpoints with auth, bodies, and query params
- `develop_env.postman_environment.json` — environment variables (`baseUrl`, `access_token`, etc.)

Run backend unit/integration tests:

```bash
cd backend
uv run pytest
uv run pytest --cov=app --cov-report=html
```

---

## Environment Variables

See `backend/.env.example` for the full list. Critical variables:

| Variable                 | Description                        |
|--------------------------|------------------------------------|
| `DATABASE_URL`           | PostgreSQL async connection string |
| `REDIS_URL`              | Redis connection string            |
| `JWT_SECRET_KEY`         | ≥ 32 chars random string           |
| `JWT_REFRESH_SECRET_KEY` | ≥ 32 chars random string           |
| `SECRET_KEY`             | Application secret key             |
| `DEV_API_KEY`            | Key for dev-only endpoints         |

---

## Security

- JWT access + refresh tokens with Redis blacklist on logout
- bcrypt cost factor 12 for password hashing
- Rate limiting on all endpoints (stricter on auth routes)
- Security headers (CSP, HSTS, X-Frame-Options)
- Tenant isolation via `tenant_id` on every query

---

## License

MIT License. See [LICENSE](LICENSE).
