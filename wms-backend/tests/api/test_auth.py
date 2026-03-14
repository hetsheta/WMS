import pytest


@pytest.mark.asyncio
async def test_register(client):
    res = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "securepass",
        "full_name": "New User",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "new@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    res = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepass",
        "full_name": "Dup User",
    })
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    res = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    res = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpass",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me(client, auth_headers):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 403
