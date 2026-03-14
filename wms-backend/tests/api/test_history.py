import pytest
import uuid


@pytest.mark.asyncio
async def test_move_history_returns_operation_lines(client, auth_headers, db, test_user):
    from app.models.models import Location, Product, Warehouse

    wh = Warehouse(id=uuid.uuid4(), name="WH-HIST", short_code="WHH", created_by=test_user.id)
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf H", short_code="SH")
    prod = Product(id=uuid.uuid4(), name="History Item", sku="HIST-001", created_by=test_user.id)
    db.add_all([wh, loc, prod])
    await db.commit()

    create_res = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "operation_type": "receipt",
            "warehouse_id": str(wh.id),
            "lines": [
                {
                    "product_id": str(prod.id),
                    "location_id": str(loc.id),
                    "qty_demand": "3",
                }
            ],
        },
    )
    assert create_res.status_code == 201

    op_id = create_res.json()["id"]
    await client.post(f"/api/v1/operations/{op_id}/validate", headers=auth_headers)
    ready_res = await client.post(f"/api/v1/operations/{op_id}/ready", headers=auth_headers)
    line_id = ready_res.json()["move_lines"][0]["id"]
    await client.post(
        f"/api/v1/operations/{op_id}/confirm",
        headers=auth_headers,
        json={line_id: "3"},
    )

    history_res = await client.get("/api/v1/operations/history", headers=auth_headers)
    assert history_res.status_code == 200
    payload = history_res.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["reference"].startswith("RCP/")
