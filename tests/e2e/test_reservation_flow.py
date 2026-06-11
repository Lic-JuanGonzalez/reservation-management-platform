"""E2E tests using Playwright — reservation lifecycle flow."""
from __future__ import annotations

import re

import pytest
from playwright.async_api import Page, expect


BASE_URL = "http://localhost:3000"


@pytest.fixture(scope="module")
def test_email() -> str:
    import time
    return f"e2etest_{int(time.time())}@example.com"


class TestAuthFlow:
    async def test_register_and_see_verify_message(self, page: Page, test_email: str):
        await page.goto(f"{BASE_URL}/register")
        await page.fill('[name="first_name"]', "End")
        await page.fill('[name="last_name"]', "ToEnd")
        await page.fill('[name="email"]', test_email)
        await page.fill('[name="password"]', "E2eTest@123")
        await page.fill('[name="confirmPassword"]', "E2eTest@123")
        await page.click('button[type="submit"]')
        await expect(page).to_have_url(re.compile(r".*/verify-email-sent"))

    async def test_login_page_loads(self, page: Page):
        await page.goto(f"{BASE_URL}/login")
        await expect(page.locator("h1")).to_contain_text("Welcome back")
        await expect(page.locator('input[type="email"]')).to_be_visible()
        await expect(page.locator('input[type="password"]')).to_be_visible()

    async def test_login_with_invalid_credentials_shows_error(self, page: Page):
        await page.goto(f"{BASE_URL}/login")
        await page.fill('input[type="email"]', "nobody@example.com")
        await page.fill('input[type="password"]', "WrongPass@1")
        await page.click('button[type="submit"]')
        # Toast notification with error
        await expect(page.locator(".react-hot-toast")).to_be_visible(timeout=5000)

    async def test_redirect_to_login_when_unauthenticated(self, page: Page):
        await page.goto(f"{BASE_URL}/dashboard")
        await expect(page).to_have_url(re.compile(r".*/login"))

    async def test_forgot_password_page_accessible(self, page: Page):
        await page.goto(f"{BASE_URL}/login")
        await page.click("text=Forgot password?")
        await expect(page).to_have_url(re.compile(r".*/forgot-password"))


class TestDashboard:
    @pytest.fixture(autouse=True)
    async def login_as_admin(self, page: Page):
        """Log in with a pre-seeded admin account."""
        await page.goto(f"{BASE_URL}/login")
        await page.fill('input[type="email"]', "admin@demo.com")
        await page.fill('input[type="password"]', "Admin@Demo123")
        await page.click('button[type="submit"]')
        await page.wait_for_url(re.compile(r".*/dashboard"), timeout=5000)

    async def test_dashboard_renders_stats(self, page: Page):
        await expect(page.locator("h1")).to_contain_text("Good")
        # Stat cards should be visible
        await expect(page.locator("text=Total Reservations")).to_be_visible()
        await expect(page.locator("text=Confirmed")).to_be_visible()

    async def test_navigation_to_reservations(self, page: Page):
        await page.click("text=Reservations")
        await expect(page).to_have_url(re.compile(r".*/reservations"))
        await expect(page.locator("h1")).to_contain_text("Reservations")

    async def test_navigation_to_resources(self, page: Page):
        await page.click("text=Resources")
        await expect(page).to_have_url(re.compile(r".*/resources"))
        await expect(page.locator("h1")).to_contain_text("Resources")

    async def test_logout_redirects_to_login(self, page: Page):
        await page.click("text=Sign out")
        await expect(page).to_have_url(re.compile(r".*/login"), timeout=5000)
