from concurrent.futures import ThreadPoolExecutor
import pytest

def create(client):
    r = client.post("/api/orders",json={"customer_id":1,"merchant_id":1,"lat":40.75,"lng":-73.98,"prep_minutes":8})
    assert r.status_code == 201
    return r.json()["id"]

def ready(client,id):
    for status in ["ACCEPTED","PREPARING","READY_FOR_PICKUP"]:
        assert client.patch(f"/api/orders/{id}/status",json={"status":status}).status_code == 200

def test_order_lifecycle(client):
    id = create(client)
    assert client.get(f"/api/orders/{id}").json()["status"] == "CREATED"
    assert client.patch(f"/api/orders/{id}/status",json={"status":"DELIVERED"}).status_code == 409
    ready(client,id)
    assert client.patch(f"/api/orders/{id}/status",json={"status":"PICKED_UP"}).status_code == 409
    a = client.post(f"/api/orders/{id}/dispatch").json()
    assert client.post(f"/api/orders/{id}/dispatch").status_code == 409
    assert client.post(f"/api/assignments/{a['id']}/accept").status_code == 200
    assert client.post(f"/api/assignments/{a['id']}/accept").status_code == 409
    assert client.post("/api/demo/step").json()["moved"] == 1
    for status in ["PICKED_UP","DELIVERED"]:
        assert client.patch(f"/api/orders/{id}/status",json={"status":status}).status_code == 200
    d = client.get("/api/dashboard").json()
    assert all(x["available"] for x in d["drivers"])
    assert d["assignments"] == []
    assert client.patch(f"/api/orders/{id}/status",json={"status":"CANCELLED"}).status_code == 409

@pytest.mark.parametrize("patch", [{"lat":91},{"lng":181},{"prep_minutes":-1},{"customer_id":0}])
def test_invalid_input(client,patch):
    payload = {"customer_id":1,"merchant_id":1,"lat":40.7,"lng":-74}
    payload.update(patch)
    assert client.post("/api/orders",json=payload).status_code == 422

def test_missing_foreign_key(client):
    assert client.post("/api/orders",json={"customer_id":999,"merchant_id":1,"lat":0,"lng":0}).status_code == 404
    assert client.get("/api/orders/999").status_code == 404

def test_unavailable(client):
    for id in [1,2]:
        assert client.patch(f"/api/drivers/{id}",json={"lat":40.7,"lng":-74,"available":False}).status_code == 200
    id = create(client)
    ready(client,id)
    assert client.post(f"/api/orders/{id}/dispatch").status_code == 409

def test_cancellation_releases_driver(client):
    id = create(client)
    ready(client,id)
    a = client.post(f"/api/orders/{id}/dispatch").json()
    assert client.patch(f"/api/drivers/{a['driver_id']}",json={"lat":0,"lng":0,"available":True}).status_code == 409
    assert client.patch(f"/api/orders/{id}/status",json={"status":"CANCELLED"}).status_code == 200
    assert client.post(f"/api/assignments/{a['id']}/accept").status_code == 409
    assert client.get("/api/dashboard").json()["assignments"] == []

def test_concurrent_same_order(client):
    id = create(client)
    ready(client,id)
    with ThreadPoolExecutor(max_workers=4) as pool:
        codes = list(pool.map(lambda _: client.post(f"/api/orders/{id}/dispatch").status_code, range(4)))
    assert codes.count(201) == 1
    assert set(codes) <= {201,409}
    assert len(client.get("/api/dashboard").json()["assignments"]) == 1

def test_concurrent_competing_orders(client):
    ids = [create(client) for _ in range(4)]
    for id in ids:
        ready(client,id)
    with ThreadPoolExecutor(max_workers=4) as pool:
        codes = list(pool.map(lambda id: client.post(f"/api/orders/{id}/dispatch").status_code, ids))
    assert 1 <= codes.count(201) <= 2
    assert set(codes) <= {201,409}
    assignments = client.get("/api/dashboard").json()["assignments"]
    assert len({a["driver_id"] for a in assignments}) == len(assignments)
    assert len({a["order_id"] for a in assignments}) == len(assignments)

def test_websocket_event(client):
    with client.websocket_connect("/ws") as ws:
        id = create(client)
        assert ws.receive_json() == {"type":"order.created","id":id}
