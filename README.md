# SaaS Reservation Platform

Enterprise-grade multi-tenant SaaS reservation platform supporting Hotels, Medical Clinics, Dental Offices, Gyms, Beauty Salons, Coworking Spaces, Event Venues, and Professional Services.

---

## Architecture

- **Pattern**: Clean Architecture + Domain-Driven Design + CQRS
- **Multi-tenancy**: Shared schema with `tenant_id` + PostgreSQL Row-Level Security
- **API**: REST with versioning (`/api/v1/`)
- **Async processing**: Celery + Redis (notifications, reminders, reports)

```
saas-reservation-platform/
├── backend/                # FastAPI + Python 3.13
│   ├── app/
│   │   ├── core/           # Config, database, security, logging
│   │   ├── domain/         # Entities, value objects, events, repository interfaces
│   │   ├── application/    # Services, DTOs, commands, queries
│   │   ├── infrastructure/ # SQLAlchemy models, repositories, Redis, Celery
│   │   ├── api/            # FastAPI routers, middleware, exception handlers
│   │   └── workers/        # Celery tasks
│   ├── alembic/            # Database migrations
│   └── tests/              # Unit, integration, conftest
├── frontend/               # React 18 + TypeScript + Vite
│   └── src/
│       ├── components/     # Reusable UI components
│       ├── pages/          # Route-level page components
│       ├── hooks/          # React Query data hooks
│       ├── store/          # Zustand state (auth)
│       └── services/api/   # Axios API clients
├── infrastructure/
│   ├── nginx/              # Reverse proxy config
│   ├── prometheus/         # Metrics scraping
│   ├── grafana/            # Dashboards + provisioning
│   └── loki/               # Log aggregation
├── tests/
│   ├── e2e/                # Playwright end-to-end tests
│   ├── load/               # Locust performance tests
│   └── postman/            # Postman collection v2.1
├── docs/
│   ├── architecture/       # Business analysis, architecture docs
│   └── SECURITY_ASSESSMENT.md
├── scripts/
│   └── init-db.sql
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Tech Stack

| Layer          | Technology                                              |
|----------------|---------------------------------------------------------|
| Backend        | Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic           |
| Database       | PostgreSQL 16 (with RLS)                                |
| Cache / Broker | Redis 7                                                 |
| Task Queue     | Celery 5 + Celery Beat + Flower                         |
| Frontend       | React 18, TypeScript, Vite, TailwindCSS                 |
| State          | Zustand, React Query v5                                 |
| Auth           | JWT (access + refresh), bcrypt                          |
| Proxy          | Nginx 1.27                                              |
| Monitoring     | Prometheus, Grafana, Loki, Promtail                     |
| Testing        | Pytest, Playwright, Locust                              |
| Quality        | Ruff, Black, MyPy                                       |
| Deps           | uv, pyproject.toml, uv.lock                             |
| CI/CD          | GitHub Actions                                          |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2+
- Python 3.13+ (for local dev)
- Node 22+ (for local frontend dev)
- uv (`pip install uv`)

### With Docker Compose (recommended)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — change JWT secrets and passwords

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Access the platform
#    Frontend:   http://localhost:3000
#    API Docs:   http://localhost:8000/api/docs
#    Grafana:    http://localhost:3001  (admin/admin)
#    Flower:     http://localhost:5555  (admin/flower123)
#    MailHog:    http://localhost:8025
```

### Backend Local Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Local Development

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## API Overview

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/api/docs`

| Module           | Endpoints                                                      |
|------------------|----------------------------------------------------------------|
| Authentication   | POST /auth/register, /login, /logout, /refresh, /verify-email |
|                  | POST /auth/forgot-password, /reset-password, /change-password  |
|                  | GET  /auth/me                                                  |
| Tenants          | POST /tenants, GET /tenants, GET/PATCH /tenants/{id}           |
|                  | PATCH /tenants/{id}/settings                                   |
| Resources        | POST /resources, GET /resources, GET/PATCH/DELETE /resources/{id} |
| Reservations     | POST /reservations, GET /reservations, GET /reservations/{id}  |
|                  | GET /reservations/availability                                 |
|                  | POST /reservations/{id}/confirm, /cancel                       |
| Reports          | GET /reports/daily, /reports/summary                           |
| Health           | GET /health, /ready                                            |

---

## Running Tests

```bash
cd backend

# Unit + integration tests
uv run pytest

# With coverage report
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html

# E2E tests (requires running stack)
cd tests/e2e
npm install @playwright/test
npx playwright install
npx pytest test_reservation_flow.py

# Load tests (requires running stack)
cd tests/load
pip install locust
locust -f locustfile.py --host http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 60s --headless
```

---

## Environment Variables

See `backend/.env.example` for a full list. Critical variables:

| Variable                    | Required | Description                         |
|-----------------------------|----------|-------------------------------------|
| `DATABASE_URL`              | YES      | PostgreSQL async connection string  |
| `REDIS_URL`                 | YES      | Redis connection string             |
| `JWT_SECRET_KEY`            | YES      | ≥ 32 chars random string            |
| `JWT_REFRESH_SECRET_KEY`    | YES      | ≥ 32 chars random string            |
| `SECRET_KEY`                | YES      | Application secret key              |
| `SMTP_HOST`                 | YES      | Email server host                   |
| `SMTP_USERNAME`             | prod     | Email account                       |
| `SMTP_PASSWORD`             | prod     | Email password / app password       |

---

## Performance Targets

| Metric                | Target           |
|-----------------------|------------------|
| API P95 latency       | < 200ms          |
| API P99 latency       | < 500ms          |
| Concurrent users      | 1,000+           |
| Reservations/minute   | 500+             |
| Test coverage         | ≥ 90%            |
| Uptime SLA            | 99.9%            |

---

## Security

See [docs/SECURITY_ASSESSMENT.md](docs/SECURITY_ASSESSMENT.md) for the full security report.

Key controls:
- JWT with refresh token rotation + Redis blacklist
- bcrypt cost factor 12 for password hashing
- PostgreSQL Row-Level Security for tenant isolation
- Rate limiting on all endpoints (stricter on auth)
- Security headers (CSP, HSTS, X-Frame-Options)
- OWASP Top 10 compliance
- Trivy + Bandit scans in CI

---

## Deployment

See [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md).

CI/CD: GitHub Actions pipeline includes lint → test → security scan → Docker build → staging deploy.

---

## License

MIT License. See [LICENSE](LICENSE).
