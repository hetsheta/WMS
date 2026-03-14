import pytest
import uuid


@pytest.mark.asyncio
async def test_create_location_with_blank_barcode(client, auth_headers):
    warehouse_res = await client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"name": "Main Warehouse", "short_code": "MWH", "address": "Dock 1"},
    )
    assert warehouse_res.status_code == 201
    warehouse_id = warehouse_res.json()["id"]

    location_res = await client.post(
        f"/api/v1/warehouses/{warehouse_id}/locations",
        headers=auth_headers,
        json={"name": "Rack A1", "short_code": "A1", "barcode": ""},
    )

    assert location_res.status_code == 201
    assert location_res.json()["barcode"] is None


@pytest.mark.asyncio
async def test_new_user_starts_with_empty_master_data(client, db, test_user):
    from app.core.security import hash_password
    from app.models.models import User

    base_login = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    base_headers = {"Authorization": f"Bearer {base_login.json()['access_token']}"}

    create_wh = await client.post(
        "/api/v1/warehouses",
        headers=base_headers,
        json={"name": "Main Warehouse", "short_code": "MWH", "address": "Dock 1"},
    )
    assert create_wh.status_code == 201

    create_product = await client.post(
        "/api/v1/products",
        headers=base_headers,
        json={"name": "Widget", "sku": "WGT-001", "unit_of_measure": "pcs", "cost_price": "10"},
    )
    assert create_product.status_code == 201

    other_user = User(
        id=uuid.uuid4(),
        email="fresh@example.com",
        hashed_password=hash_password("password123"),
        full_name="Fresh User",
        is_active=True,
    )
    db.add(other_user)
    await db.commit()

    login_res = await client.post("/api/v1/auth/login", json={"email": "fresh@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    warehouses_res = await client.get("/api/v1/warehouses", headers=other_headers)
    products_res = await client.get("/api/v1/products", headers=other_headers)

    assert warehouses_res.status_code == 200
    assert warehouses_res.json() == []
    assert products_res.status_code == 200
    assert products_res.json()["items"] == []
