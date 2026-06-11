# Business Analysis — SaaS Reservation Platform

## Executive Summary

Multi-tenant SaaS reservation platform enabling businesses across verticals (hospitality,
healthcare, fitness, beauty, coworking, events, professional services) to manage resources,
schedules, and customer bookings through a unified, configurable interface.

---

## 1. Stakeholder Map

| Stakeholder       | Role                               | Primary Goal                          |
|-------------------|------------------------------------|---------------------------------------|
| Super Admin       | Platform operator                  | Manage tenants, subscriptions, health |
| Tenant Admin      | Business owner / manager           | Configure resources, view reports     |
| Employee          | Staff member                       | Manage reservations, schedules        |
| Customer          | End consumer                       | Book, view, cancel reservations       |
| Billing System    | External payment processor         | Subscription lifecycle                |
| Notification Svc  | Email / SMS / Push provider        | Deliver event notifications           |

---

## 2. Business Verticals & Resource Mapping

| Vertical            | Resource Type       | Reservation Unit  | Key Constraint        |
|---------------------|---------------------|-------------------|-----------------------|
| Hotel               | Room                | Night / hours     | Occupancy, check-in   |
| Medical Clinic      | Doctor / Room       | Appointment slot  | License, specialty    |
| Dental Office       | Dentist / Chair     | Appointment slot  | Treatment type        |
| Gym                 | Trainer / Class     | Session / class   | Capacity, equipment   |
| Beauty Salon        | Stylist / Station   | Service slot      | Service duration      |
| Coworking Space     | Desk / Meeting Room | Hours / day       | Capacity, amenities   |
| Event Venue         | Hall / Space        | Event block       | Capacity, catering    |
| Professional Svc    | Professional        | Consultation slot | Specialty, duration   |

---

## 3. Functional Requirements

### FR-AUTH-001: User Registration
**Actor:** Customer, Tenant Admin  
**Description:** Users register with email, password, and required profile data.  
**Acceptance Criteria:**
- Email must be unique per tenant scope
- Password minimum 8 chars, 1 uppercase, 1 number, 1 special char
- Verification email sent on registration
- Account inactive until email verified

### FR-AUTH-002: Authentication
**Actor:** All roles  
**Description:** Authenticated access via JWT tokens with refresh mechanism.  
**Acceptance Criteria:**
- Access token TTL: 15 minutes
- Refresh token TTL: 7 days
- Refresh token rotation on use
- Token blacklist on logout

### FR-AUTH-003: Password Management
**Actor:** All roles  
**Description:** Forgot/reset/change password flows.  
**Acceptance Criteria:**
- Reset link expires in 1 hour
- Old password required for change
- Invalidate all sessions on password change

### FR-TENANT-001: Tenant Onboarding
**Actor:** Super Admin  
**Description:** Create and configure new tenant with subscription plan.  
**Acceptance Criteria:**
- Unique slug per tenant
- Default roles created automatically
- Welcome email sent to tenant admin
- Tenant isolated from other tenants

### FR-TENANT-002: Tenant Configuration
**Actor:** Tenant Admin  
**Description:** Configure business settings, branding, and operational parameters.  
**Acceptance Criteria:**
- Business name, logo, timezone, locale
- Working hours per day of week
- Holiday calendar
- Notification preferences

### FR-RESOURCE-001: Resource CRUD
**Actor:** Tenant Admin, Employee  
**Description:** Manage bookable resources (rooms, staff, equipment).  
**Acceptance Criteria:**
- Name, description, type, capacity, amenities
- Active/inactive status
- Photo upload support
- Bulk operations supported

### FR-RESOURCE-002: Availability Rules
**Actor:** Tenant Admin  
**Description:** Define when resources are bookable.  
**Acceptance Criteria:**
- Weekly recurring schedule
- Override for specific dates
- Maintenance windows block booking
- Blackout periods configurable

### FR-RESERVATION-001: Create Reservation
**Actor:** Customer, Employee  
**Description:** Book a resource for a specific time slot.  
**Acceptance Criteria:**
- No double booking (enforced at DB level)
- Slot must fall within availability window
- Minimum/maximum advance booking window respected
- Confirmation notification sent
- Reservation reference number generated

### FR-RESERVATION-002: Modify Reservation
**Actor:** Customer, Employee  
**Description:** Change time, resource, or details of existing reservation.  
**Acceptance Criteria:**
- Original slot released on modification
- New slot validated against availability
- Modification notification sent
- History preserved

### FR-RESERVATION-003: Cancel Reservation
**Actor:** Customer, Employee, Tenant Admin  
**Description:** Cancel an existing reservation.  
**Acceptance Criteria:**
- Cancellation policy enforced (configurable per tenant)
- Slot released immediately
- Cancellation notification sent
- Reason captured for reporting

### FR-RESERVATION-004: Waiting List
**Actor:** Customer  
**Description:** Join waiting list when desired slot is unavailable.  
**Acceptance Criteria:**
- Auto-promote when slot becomes available
- Notification sent on promotion
- Configurable waiting list capacity

### FR-NOTIFICATION-001: Event Notifications
**Actor:** System  
**Description:** Send notifications on reservation lifecycle events.  
**Channels:** Email, SMS, Push  
**Events:** Created, Updated, Confirmed, Cancelled, Reminder (24h, 1h)  
**Acceptance Criteria:**
- Async delivery via Celery
- Retry on failure (max 3 attempts)
- Delivery status tracked
- Customer preferences respected

### FR-REPORT-001: Operational Reports
**Actor:** Tenant Admin, Employee  
**Description:** Access reservation and resource utilization reports.  
**Reports:**
- Daily/monthly reservation counts
- Occupancy rate by resource
- Revenue summary (if payment integrated)
- Cancellation analysis
- Customer retention metrics

---

## 4. Non-Functional Requirements

### NFR-PERF-001: Response Time
- API P95 latency < 200ms under normal load
- API P99 latency < 500ms
- Report generation < 2 seconds

### NFR-PERF-002: Throughput
- Sustain 1,000 concurrent users
- 500 reservations/minute peak
- No degradation under 2x peak for 10 minutes

### NFR-AVAIL-001: Availability
- 99.9% uptime SLA (< 8.7 hours downtime/year)
- Zero-downtime deployments
- Automated failover for database

### NFR-SCALE-001: Scalability
- Horizontal scaling for API layer
- Read replicas for reporting queries
- Stateless application servers

### NFR-SEC-001: Security
- OWASP Top 10 compliance
- Data encrypted in transit (TLS 1.3)
- Secrets managed via environment variables
- PII data access audited

### NFR-TENANT-001: Isolation
- Complete data isolation between tenants
- No cross-tenant data leakage
- Per-tenant rate limits
- Per-tenant resource quotas

### NFR-OBS-001: Observability
- Structured JSON logging
- Distributed tracing
- Business and infrastructure metrics
- Alert on SLA breach

---

## 5. Business Rules

| ID    | Rule                                                                                    |
|-------|-----------------------------------------------------------------------------------------|
| BR-01 | Reservation cannot overlap for same resource                                            |
| BR-02 | Reservation slot must be within resource working hours                                  |
| BR-03 | Customer cannot have more than N concurrent active reservations (configurable per plan) |
| BR-04 | Cancellation within X hours of start time incurs penalty (configurable per tenant)      |
| BR-05 | Waiting list auto-promotion respects FIFO order                                         |
| BR-06 | Tenant data purged 30 days after subscription cancellation                              |
| BR-07 | Super Admin cannot access tenant data without explicit audit trail                      |
| BR-08 | Resource availability changes do not affect confirmed reservations                      |
| BR-09 | Email verification required before first reservation                                    |
| BR-10 | Reservation reminder sent 24h and 1h before start time                                 |

---

## 6. User Stories

### Epic: Authentication
- **US-001**: As a new user, I want to register with my email so I can create an account
- **US-002**: As a registered user, I want to log in so I can access my reservations
- **US-003**: As a user, I want to reset my password so I can recover access
- **US-004**: As a user, I want my session to remain active securely so I don't have to log in repeatedly

### Epic: Reservation Management
- **US-010**: As a customer, I want to search available slots so I can choose a convenient time
- **US-011**: As a customer, I want to book a resource so I can secure my preferred time
- **US-012**: As a customer, I want to cancel a reservation so I can free up the slot
- **US-013**: As a customer, I want to receive reminders so I don't forget my reservation
- **US-014**: As a customer, I want to view my reservation history so I can track past bookings

### Epic: Resource Management
- **US-020**: As a tenant admin, I want to add resources so customers can book them
- **US-021**: As a tenant admin, I want to set availability rules so bookings are restricted to working hours
- **US-022**: As a tenant admin, I want to block dates so resources are unavailable during maintenance

### Epic: Reporting
- **US-030**: As a tenant admin, I want to see daily occupancy so I can optimize scheduling
- **US-031**: As a tenant admin, I want monthly revenue reports so I can track business performance
- **US-032**: As a tenant admin, I want cancellation reports so I can identify problem areas

---

## 7. Acceptance Criteria Template

```gherkin
Feature: Reservation Creation

  Background:
    Given tenant "acme-clinic" is active
    And resource "Dr. Smith" has availability Monday-Friday 09:00-17:00
    And customer "john@example.com" is verified

  Scenario: Successful reservation creation
    Given the slot 2026-07-01 10:00-11:00 is available
    When customer submits reservation for that slot
    Then reservation is created with status "pending"
    And confirmation email is sent to customer
    And reservation reference number is generated

  Scenario: Double booking prevention
    Given slot 2026-07-01 10:00-11:00 is already reserved
    When another customer submits reservation for same slot
    Then request is rejected with HTTP 409 Conflict
    And error message "Slot unavailable" is returned

  Scenario: Outside availability window
    Given resource has no availability on Saturday
    When customer submits reservation for Saturday
    Then request is rejected with HTTP 422
    And error message "Resource not available on requested date"
```
