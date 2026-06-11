# System Architecture — SaaS Reservation Platform

## 1. Architectural Style

**Primary Pattern:** Clean Architecture + Domain-Driven Design  
**API Style:** REST with versioning (`/api/v1/`)  
**Multi-tenancy:** Shared schema with `tenant_id` discriminator + Row-Level Security  
**Async Processing:** Celery + Redis for notifications, reports, background jobs  

---

## 2. C4 Model

### Level 1 — System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Internet                                     │
│                                                                     │
│  ┌──────────┐    HTTPS     ┌─────────────────────┐    HTTPS        │
│  │ Browser  │◄────────────►│  Nginx Reverse Proxy │                 │
│  │ Mobile   │              └─────────┬───────────┘                 │
│  └──────────┘                        │                             │
│                            ┌─────────▼───────────┐                 │
│                            │  SaaS Reservation   │                 │
│                            │     Platform        │                 │
│                            └─────────┬───────────┘                 │
│                                      │                             │
│              ┌───────────────────────┼───────────────────┐         │
│              │                       │                   │         │
│    ┌─────────▼──────┐   ┌────────────▼──────┐  ┌────────▼───────┐ │
│    │  Email Service │   │   SMS Gateway     │  │  Push Service  │ │
│    │  (SMTP/SES)    │   │   (Twilio etc)    │  │  (FCM/APNS)    │ │
│    └────────────────┘   └───────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Level 2 — Container Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SaaS Reservation Platform                         │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   React SPA  │    │  FastAPI App │    │   Celery Workers     │  │
│  │ (TypeScript) │───►│   (Python)   │───►│   (Python)           │  │
│  │   Port 3000  │    │   Port 8000  │    │   Async Tasks        │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                             │                         │             │
│                    ┌────────┼─────────────────────────┤            │
│                    │        │                         │             │
│             ┌──────▼──┐  ┌──▼──────┐  ┌──────────────▼──────────┐ │
│             │PostgreSQL│  │  Redis  │  │    Celery Beat           │ │
│             │Port 5432 │  │ Port    │  │  (Scheduled Tasks)       │ │
│             │          │  │  6379   │  └─────────────────────────┘  │
│             └──────────┘  └─────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Level 3 — Component Diagram (FastAPI Application)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        API Layer (Routers)                   │   │
│  │  /auth  /tenants  /users  /resources  /reservations         │   │
│  │  /availability  /notifications  /reports                    │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │                     Application Layer                        │   │
│  │  Commands │ Queries │ Handlers │ DTOs │ Validators           │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │                       Domain Layer                           │   │
│  │  Entities │ Value Objects │ Domain Services │ Events        │   │
│  │  Repository Interfaces │ Business Rules                     │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │                   Infrastructure Layer                       │   │
│  │  SQLAlchemy Repos │ Redis Cache │ Celery Tasks │ Email      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Clean Architecture Layer Responsibilities

### Domain Layer (innermost, no dependencies)
- **Entities**: Business objects with identity (Tenant, User, Resource, Reservation)
- **Value Objects**: Immutable domain concepts (TimeSlot, Money, EmailAddress)
- **Domain Services**: Business logic spanning multiple entities
- **Repository Interfaces**: Contracts for data access (no implementation)
- **Domain Events**: Facts that occurred in the domain

### Application Layer
- **Commands**: Mutating use cases (CreateReservation, CancelReservation)
- **Queries**: Read-only use cases (GetAvailableSlots, GetReservationHistory)
- **Handlers**: Command/Query handlers orchestrating domain + infrastructure
- **DTOs**: Input/output transfer objects for application boundary
- **Application Services**: Orchestration, no business logic

### Infrastructure Layer
- **Repositories**: SQLAlchemy implementations of domain repository interfaces
- **ORM Models**: SQLAlchemy mapped models (separate from domain entities)
- **Cache**: Redis implementation for session, slots cache
- **Messaging**: Celery task definitions, Redis pub/sub
- **External**: Email, SMS, push notification providers

### API Layer (outermost)
- **Routers**: FastAPI route definitions
- **Schemas**: Pydantic request/response schemas
- **Middleware**: Auth, logging, rate limiting, correlation ID
- **Exception Handlers**: Global error handling, HTTP mapping

---

## 4. Multi-Tenant Strategy

### Approach: Shared Schema with tenant_id + PostgreSQL Row-Level Security

**Rationale:**
- Cost-efficient for SaaS (single DB cluster)
- RLS provides database-enforced isolation
- Easier operations than per-tenant DBs
- Scales to thousands of tenants

**Implementation:**
```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON reservations
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set per-request
SET app.current_tenant_id = '<tenant-uuid>';
```

**Application-level enforcement:**
- Middleware extracts `tenant_id` from JWT
- All repository queries include `where(Model.tenant_id == tenant_id)`
- Integration tests verify cross-tenant isolation

---

## 5. Data Flow: Reservation Creation

```
Customer → POST /api/v1/reservations
    │
    ▼
Auth Middleware (validate JWT, extract tenant_id)
    │
    ▼
Rate Limit Middleware (per tenant, per user)
    │
    ▼
ReservationRouter.create_reservation()
    │
    ▼
CreateReservationCommand → CreateReservationHandler
    │
    ├─► AvailabilityService.check_slot_available()
    │       └─► ResourceRepository.get_availability()
    │       └─► ReservationRepository.check_overlap()  [SELECT FOR UPDATE SKIP LOCKED]
    │
    ├─► ReservationDomainService.validate_business_rules()
    │
    ├─► ReservationRepository.create()  [atomic transaction]
    │
    └─► EventBus.publish(ReservationCreatedEvent)
            └─► Celery: send_confirmation_email.delay()
            └─► Celery: schedule_reminder.delay()
    │
    ▼
HTTP 201 Created + ReservationResponseDTO
```

---

## 6. Availability Engine Design

```
AvailabilityEngine
├── WorkingHoursRule        (Mon-Fri 09:00-18:00)
├── HolidayRule             (tenant holiday calendar)
├── MaintenanceWindowRule   (one-off blocks)
├── BlackoutPeriodRule      (recurring blocks)
└── ExistingBookingsRule    (confirmed reservations)

Algorithm:
1. Generate candidate slots for requested date range
2. Apply each rule as a filter (subtract unavailable periods)
3. Return remaining available slots

Concurrency:
- Slot availability checked inside serializable transaction
- SELECT FOR UPDATE SKIP LOCKED on reservation rows
- Redis cache for computed availability (TTL 30s, invalidated on booking)
```

---

## 7. Caching Strategy

| Data                      | Cache Key Pattern                          | TTL    | Invalidation                |
|---------------------------|--------------------------------------------|--------|-----------------------------|
| Available slots           | `avail:{tenant}:{resource}:{date}`         | 30s    | On reservation create/cancel |
| User session              | `session:{user_id}`                        | 15min  | On logout, password change  |
| Tenant config             | `tenant:{tenant_id}:config`                | 5min   | On config update            |
| Resource list             | `tenant:{tenant_id}:resources`             | 2min   | On resource CRUD            |
| Rate limit counters       | `rl:{tenant_id}:{user_id}:{endpoint}`      | Window | Sliding window              |

---

## 8. Security Architecture

```
Request Pipeline:
  ┌──────────────────────────────────────────────────┐
  │  Nginx (TLS termination, DDoS mitigation)        │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  Rate Limiter (Redis sliding window per IP/user)  │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  Security Headers Middleware                      │
  │  (HSTS, X-Frame-Options, CSP, etc.)              │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  JWT Auth Middleware                              │
  │  (Verify signature, expiry, blacklist check)     │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  RBAC Authorization (per endpoint permissions)   │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  Tenant Isolation (extract + inject tenant_id)   │
  └────────────────────┬─────────────────────────────┘
                       │
  ┌────────────────────▼─────────────────────────────┐
  │  Business Logic (Domain + Application Layer)     │
  └──────────────────────────────────────────────────┘
```

---

## 9. Deployment Architecture

```
                           ┌─────────────┐
                           │  CloudFlare │  (DNS, CDN, DDoS)
                           └──────┬──────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │     Nginx (Load Balancer)   │
                    └──────────┬─────────────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
    ┌──────────▼──┐  ┌─────────▼───┐  ┌───────▼─────┐
    │  API Node 1 │  │  API Node 2 │  │  API Node 3 │
    └─────────────┘  └─────────────┘  └─────────────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
               ┌───────────────┼──────────────────┐
               │               │                  │
    ┌──────────▼──┐  ┌─────────▼───┐  ┌──────────▼───┐
    │  PostgreSQL │  │    Redis    │  │  Celery      │
    │  Primary    │  │  Cluster   │  │  Workers     │
    │  + Replica  │  └─────────────┘  └──────────────┘
    └─────────────┘
```

---

## 10. Architectural Decision Records

### ADR-001: Shared Schema Multi-Tenancy
**Decision:** Use shared schema with `tenant_id` column + RLS  
**Rationale:** Cost efficiency, operational simplicity, sufficient isolation  
**Consequences:** Must enforce tenant_id in every query; RLS as defense-in-depth  

### ADR-002: CQRS for Reservation Queries
**Decision:** Separate read models for availability and reporting queries  
**Rationale:** Read patterns differ from write patterns; enables read replicas  
**Consequences:** Eventual consistency acceptable for non-critical reads  

### ADR-003: Celery for Async Tasks
**Decision:** Celery with Redis broker for notifications and background jobs  
**Rationale:** Mature ecosystem, reliable delivery, easy monitoring  
**Consequences:** Redis becomes critical dependency; need celery flower for monitoring  

### ADR-004: JWT with Refresh Token Rotation
**Decision:** Short-lived access tokens + rotating refresh tokens stored in Redis  
**Rationale:** Balance security and UX; rotation prevents token theft reuse  
**Consequences:** Redis required for token blacklist; logout invalidates server-side  
