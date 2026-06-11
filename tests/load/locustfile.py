"""Locust load test scenarios for the SaaS Reservation Platform."""
from __future__ import annotations

import random
import string
import uuid
from datetime import UTC, datetime, timedelta

from locust import HttpUser, between, task


def random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{suffix}@example.com"


class ReservationPlatformUser(HttpUser):
    """Simulates a customer browsing availability and making reservations."""

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        """Register and login a user at the start of each VU session."""
        self.email = random_email()
        self.password = "LoadTest@123"
        self.access_token = None
        self.tenant_id = None

        # Register
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "first_name": "Load",
                "last_name": "User",
            },
            name="/api/v1/auth/register",
        )

        # In load tests, email verification is bypassed via seed data
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/api/v1/auth/login",
        )
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.access_token = data.get("access_token")

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(5)
    def browse_availability(self) -> None:
        """Highest-frequency task: check available slots."""
        resource_id = "00000000-0000-0000-0000-000000000001"  # seed data resource
        date = (datetime.now(UTC) + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
        self.client.get(
            "/api/v1/reservations/availability",
            params={"resource_id": resource_id, "date": date},
            headers=self._auth_headers(),
            name="/api/v1/reservations/availability",
        )

    @task(3)
    def list_reservations(self) -> None:
        self.client.get(
            "/api/v1/reservations",
            params={"limit": 20},
            headers=self._auth_headers(),
            name="/api/v1/reservations [list]",
        )

    @task(2)
    def list_resources(self) -> None:
        self.client.get(
            "/api/v1/resources",
            params={"limit": 20},
            headers=self._auth_headers(),
            name="/api/v1/resources [list]",
        )

    @task(1)
    def create_reservation(self) -> None:
        start = datetime.now(UTC) + timedelta(hours=random.randint(3, 72))
        end = start + timedelta(hours=1)
        self.client.post(
            "/api/v1/reservations",
            json={
                "resource_id": "00000000-0000-0000-0000-000000000001",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=self._auth_headers(),
            name="/api/v1/reservations [create]",
        )

    @task(1)
    def health_check(self) -> None:
        self.client.get("/health", name="/health")


class AdminUser(HttpUser):
    """Simulates a tenant admin reviewing reports and managing resources."""

    wait_time = between(2, 5)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        self.access_token = None
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@acme.com", "password": "Admin@Acme123"},
        )
        if login_resp.status_code == 200:
            self.access_token = login_resp.json().get("access_token")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    @task(4)
    def view_dashboard_reservations(self) -> None:
        self.client.get(
            "/api/v1/reservations",
            params={"limit": 50},
            headers=self._headers(),
            name="/api/v1/reservations [admin list]",
        )

    @task(2)
    def view_daily_report(self) -> None:
        today = datetime.now(UTC).date()
        week_ago = today - timedelta(days=7)
        self.client.get(
            "/api/v1/reports/daily",
            params={"start_date": str(week_ago), "end_date": str(today)},
            headers=self._headers(),
            name="/api/v1/reports/daily",
        )

    @task(1)
    def view_summary_report(self) -> None:
        today = datetime.now(UTC).date()
        month_ago = today - timedelta(days=30)
        self.client.get(
            "/api/v1/reports/summary",
            params={"start_date": str(month_ago), "end_date": str(today)},
            headers=self._headers(),
            name="/api/v1/reports/summary",
        )

    @task(1)
    def list_resources(self) -> None:
        self.client.get(
            "/api/v1/resources",
            headers=self._headers(),
            name="/api/v1/resources [admin]",
        )
