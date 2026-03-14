import pytest
import uuid


@pytest.mark.asyncio
async def test_create_receipt(client, auth_headers, db, test_user):
    from app.models.models import Warehouse, Location, Product
    wh = Warehouse(id=uuid.uuid4(), name="Main WH", short_code="MWH", created_by=test_user.id)
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf A", short_code="SA")
    prod = Product(id=uuid.uuid4(), name="Widget", sku="WGT-001", created_by=test_user.id)
    db.add_all([wh, loc, prod])
    await db.commit()

    res = await client.post("/api/v1/operations", headers=auth_headers, json={
        "operation_type": "receipt",
        "warehouse_id": str(wh.id),
        "lines": [{
            "product_id": str(prod.id),
            "location_id": str(loc.id),
            "qty_demand": "10",
        }],
    })
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["reference"].startswith("RCP/")
    assert len(data["move_lines"]) == 1


@pytest.mark.asyncio
async def test_operation_state_machine(client, auth_headers, db, test_user):
    from app.models.models import Warehouse, Location, Product
    wh = Warehouse(id=uuid.uuid4(), name="WH2", short_code="WH2", created_by=test_user.id)
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf B", short_code="SB")
    prod = Product(id=uuid.uuid4(), name="Gadget", sku="GDG-001", created_by=test_user.id)
    db.add_all([wh, loc, prod])
    await db.commit()

    create_res = await client.post("/api/v1/operations", headers=auth_headers, json={
        "operation_type": "receipt",
        "warehouse_id": str(wh.id),
        "lines": [{"product_id": str(prod.id), "location_id": str(loc.id), "qty_demand": "5"}],
    })
    op_id = create_res.json()["id"]

    val_res = await client.post(f"/api/v1/operations/{op_id}/validate", headers=auth_headers)
    assert val_res.json()["status"] == "validated"

    ready_res = await client.post(f"/api/v1/operations/{op_id}/ready", headers=auth_headers)
    assert ready_res.json()["status"] == "ready"

    line_id = ready_res.json()["move_lines"][0]["id"]
    confirm_res = await client.post(
        f"/api/v1/operations/{op_id}/confirm",
        headers=auth_headers,
        json={line_id: "5"},
    )
    assert confirm_res.json()["status"] == "done"


@pytest.mark.asyncio
async def test_invalid_state_transition(client, auth_headers, db, test_user):
    from app.models.models import Warehouse
    wh = Warehouse(id=uuid.uuid4(), name="WH3", short_code="WH3", created_by=test_user.id)
    db.add(wh)
    await db.commit()

    create_res = await client.post("/api/v1/operations", headers=auth_headers, json={
        "operation_type": "delivery",
        "warehouse_id": str(wh.id),
        "lines": [],
    })
    op_id = create_res.json()["id"]

    res = await client.post(f"/api/v1/operations/{op_id}/ready", headers=auth_headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_operations_list_is_scoped_to_current_user(client, db, test_user):
    from app.core.security import hash_password
    from app.models.models import User, Warehouse, Location, Product

    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other User",
        is_active=True,
    )
    db.add(other_user)
    await db.commit()

    own_wh = Warehouse(id=uuid.uuid4(), name="Own WH", short_code="OWN", created_by=test_user.id)
    own_loc = Location(id=uuid.uuid4(), warehouse_id=own_wh.id, name="Own Shelf", short_code="OS")
    own_prod = Product(id=uuid.uuid4(), name="Own Product", sku="OWN-001", created_by=test_user.id)

    other_wh = Warehouse(id=uuid.uuid4(), name="Other WH", short_code="OTH", created_by=other_user.id)
    other_loc = Location(id=uuid.uuid4(), warehouse_id=other_wh.id, name="Other Shelf", short_code="TS")
    other_prod = Product(id=uuid.uuid4(), name="Other Product", sku="OTH-001", created_by=other_user.id)
    db.add_all([own_wh, own_loc, own_prod, other_wh, other_loc, other_prod])
    await db.commit()

    login_res = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    own_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    other_login = await client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    own_create = await client.post(
        "/api/v1/operations",
        headers=own_headers,
        json={
            "operation_type": "receipt",
            "warehouse_id": str(own_wh.id),
            "lines": [{"product_id": str(own_prod.id), "location_id": str(own_loc.id), "qty_demand": "2"}],
        },
    )
    assert own_create.status_code == 201

    other_create = await client.post(
        "/api/v1/operations",
        headers=other_headers,
        json={
            "operation_type": "receipt",
            "warehouse_id": str(other_wh.id),
            "lines": [{"product_id": str(other_prod.id), "location_id": str(other_loc.id), "qty_demand": "4"}],
        },
    )
    assert other_create.status_code == 201

    own_list = await client.get("/api/v1/operations", headers=own_headers)
    other_list = await client.get("/api/v1/operations", headers=other_headers)

    assert own_list.status_code == 200
    assert own_list.json()["total"] == 1
    assert own_list.json()["items"][0]["warehouse_id"] == str(own_wh.id)
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 1
    assert other_list.json()["items"][0]["warehouse_id"] == str(other_wh.id)
