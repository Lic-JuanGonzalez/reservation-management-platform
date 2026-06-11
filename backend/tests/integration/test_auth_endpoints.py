"""Integration tests for /api/v1/auth endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestRegisterEndpoint:
    async def test_register_success(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "ValidPass@123",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["first_name"] == "John"
        assert "hashed_password" not in data

    async def test_register_invalid_email(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "ValidPass@123",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        assert response.status_code == 422

    async def test_register_duplicate_email(self, async_client: AsyncClient):
        payload = {
            "email": "duplicate@example.com",
            "password": "ValidPass@123",
            "first_name": "John",
            "last_name": "Doe",
        }
        await async_client.post("/api/v1/auth/register", json=payload)
        response = await async_client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409


class TestLoginEndpoint:
    async def test_login_unverified_user_rejected(self, async_client: AsyncClient):
        # Register without email verification
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "unverified@example.com",
                "password": "ValidPass@123",
                "first_name": "Jane",
                "last_name": "Smith",
            },
        )
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "unverified@example.com", "password": "ValidPass@123"},
        )
        assert response.status_code == 403

    async def test_login_wrong_credentials(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "ValidPass@123"},
        )
        assert response.status_code == 401

    async def test_login_missing_fields(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/auth/login", json={"email": "test@example.com"}
        )
        assert response.status_code == 422


class TestHealthEndpoints:
    async def test_health_returns_200(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
