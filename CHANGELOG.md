# Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — 2026-06-11

### Backend — Bug Fixes

- **Celery worker mapper init** (`backend/app/workers/celery_app.py`): Added `import app.infrastructure.database.models` to register all SQLAlchemy ORM mappers before task execution, fixing `InvalidRequestError: TenantModel not found` on worker startup.
- **Tenant `trial_ends_at` type mismatch**: Fixed `DatatypeMismatchError` by changing column type from `Mapped[str | None]` to `Mapped[datetime | None]` with proper `DateTime(timezone=True)`.
- **Reports date range off-by-one** (`backend/app/api/v1/routers/reports.py`): Changed `start_time <= end_date` to `start_time < end_date + timedelta(days=1)` so that reservations on the `end_date` day are correctly included (timezone-aware timestamps were being excluded at midnight UTC boundary).
- **Reports daily range limit**: Increased max date range from 90 days to 365 days.

### Backend — Features

- **Dev API key protection** (`backend/app/api/v1/routers/dev.py`): All dev endpoints (`/dev/setup`, `/dev/activate-all`, `/dev/verification-token`, `/dev/reset-token`) now require `X-Dev-Key` header matching `DEV_API_KEY` config value.
- **Tenant settings in response** (`backend/app/application/dtos/tenant_dtos.py`): Added `TenantSettingsResponse` model and included `settings` field in `TenantResponse` so `GET /tenants/{id}` returns full settings object.
- **`DEV_API_KEY` config** (`backend/app/core/config.py`): Added `DEV_API_KEY: str = "dev-secret-key-change-me"` setting.

### Infrastructure

- **Docker Compose log verbosity** (`docker-compose.yml`): Added `GF_LOG_LEVEL: warn` for Grafana, `--log.level=warn` for Loki, Promtail, and Prometheus to reduce noise.
- **Frontend `VITE_API_BASE_URL`** (`docker-compose.yml`): Fixed env var from `http://localhost:8000` to `http://localhost:8000/api` so the frontend `apiClient` builds the correct base URL (`/api/v1`).
- **Frontend config volumes** (`docker-compose.yml`): Added bind mounts for `postcss.config.js` and `tailwind.config.js` so Tailwind CSS persists across container restarts.

### Frontend — Bug Fixes

- **Missing `postcss.config.js`**: Created `frontend/postcss.config.js` with `tailwindcss` and `autoprefixer` plugins — without it Tailwind directives were not processed by Vite and the app rendered unstyled.
- **Cancellation rate `×100` double** (`ReportsPage.tsx`): Backend returns rate already as percentage (e.g. `60.0`); frontend was multiplying by 100 again showing `6000%`. Removed the extra `× 100`.
- **Progress bar same fix** (`ReportsPage.tsx`): `Math.min(cancellation_rate * 100, 100)` → `Math.min(cancellation_rate, 100)`.
- **Reports default date range**: Changed default from "Last 30 days" to "This month" (full calendar month via `endOfMonth`). "This month" preset now uses `endOfMonth` as end date instead of today.

### Frontend — Features

- **`CreateReservationModal`** (`src/components/reservations/CreateReservationModal.tsx`): New modal with resource selector, date picker, available slot grid, and notes field. Wired to "New Reservation" button in `ReservationsPage`.
- **`ResourceModal`** (`src/components/resources/ResourceModal.tsx`): Create/edit resource modal with name, type, description, capacity, slot duration, buffer, amenities tags, and per-day working hours. Wired to "Add Resource" and "Edit" buttons in `ResourcesPage`.
- **Confirm reservation** (`ReservationsPage.tsx`): Added "Confirm" icon button (green) for `pending` reservations alongside existing "Cancel" button. Uses `useConfirmReservation` mutation.
- **`ReportsPage`** (`src/pages/ReportsPage.tsx`): Full reports page with summary stat cards, cancellation rate progress bar, daily breakdown bar chart, date presets (Last 7d / Last 30d / This month), and custom date range inputs.
- **`SettingsPage`** (`src/pages/SettingsPage.tsx`): Tenant settings page with business profile section (name, phone, website, address) and booking rules section (timezone, locale, currency, booking limits, toggles for reminders/verification/guest bookings).
- **`useConfirmReservation` hook** (`src/hooks/useReservations.ts`): Added mutation hook for `POST /reservations/{id}/confirm`.
- **`useResources` hook** (`src/hooks/useResources.ts`): New query hook for listing resources.
- **`reports` API service** (`src/services/api/reports.ts`): New service with `daily` and `summary` endpoints.
- **`tenants` API service** (`src/services/api/tenants.ts`): New service with `get`, `update`, and `updateSettings` endpoints.
- **Dashboard "All time" label**: Added `All time` section label above stat cards for clarity.
- **Dashboard completed stat**: Added `completed` count to stat calculation (was missing from filters).
- **Dashboard chart**: Added "Completed" bar to status overview chart.
- **Custom Recharts tooltips**: Replaced default Recharts tooltip in Dashboard (compact single-line with color accent bar) and Reports (card with colored dot per status row).

### Tests / Collections

- **`tests/postman/reservation_platform.postman_collection.json`**: Cleaned Apidog export — removed 4 duplicate endpoints with missing `/api/v1/` prefix, renamed misnamed dev endpoint, removed typo header.
- **`tests/postman/develop_env.postman_environment.json`**: Apidog environment file with all required variables (`baseUrl`, `access_token`, `refresh_token`, `verification_token`, etc.).
