"""Tests for auth endpoints: register, login, refresh, logout, me."""
from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _email() -> str:
    return f"auth_{uuid4().hex[:8]}@test.com"


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        r = await client.post("/auth/register", json={
            "email": _email(), "password": "SecurePass1!", "full_name": "Alice"
        })
        assert r.status_code == 201
        body = r.json()
        assert body["email"].endswith("@test.com")
        assert "id" in body
        assert "hashed_password" not in body  # never leak hash

    async def test_register_duplicate_email(self, client: AsyncClient):
        email = _email()
        await client.post("/auth/register", json={"email": email, "password": "SecurePass123!", "full_name": "A"})
        r = await client.post("/auth/register", json={"email": email, "password": "SecurePass123!", "full_name": "B"})
        assert r.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        r = await client.post("/auth/register", json={
            "email": "not-an-email", "password": "Pass1!", "full_name": "X"
        })
        assert r.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        r = await client.post("/auth/register", json={"email": _email()})
        assert r.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        email, pw = _email(), "MyPass123!"
        await client.post("/auth/register", json={"email": email, "password": pw, "full_name": "Bob"})
        r = await client.post("/auth/login", json={"email": email, "password": pw})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body

    async def test_login_wrong_password(self, client: AsyncClient):
        email = _email()
        await client.post("/auth/register", json={"email": email, "password": "RealPass1!", "full_name": "C"})
        r = await client.post("/auth/login", json={"email": email, "password": "WrongPass!"})
        assert r.status_code == 401

    async def test_login_unknown_user(self, client: AsyncClient):
        r = await client.post("/auth/login", json={"email": "nobody@nowhere.com", "password": "x"})
        assert r.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert "email" in r.json()

    async def test_me_unauthenticated(self, client: AsyncClient):
        r = await client.get("/auth/me")
        assert r.status_code in (401, 403)

    async def test_me_invalid_token(self, client: AsyncClient):
        r = await client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code in (401, 403)


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient):
        email, pw = _email(), "RefPass1!"
        await client.post("/auth/register", json={"email": email, "password": pw, "full_name": "D"})
        login = await client.post("/auth/login", json={"email": email, "password": pw})
        rt = login.json()["refresh_token"]
        r = await client.post("/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_refresh_invalid_token(self, client: AsyncClient):
        r = await client.post("/auth/refresh", json={"refresh_token": "bad.token"})
        assert r.status_code == 401
