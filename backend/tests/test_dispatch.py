import pytest
from app.dispatch import Candidate, haversine, rank, nearest

def test_haversine():
    assert haversine((0,0),(0,0)) == 0
    assert haversine((0,0),(0,1)) == pytest.approx(111.195,rel=0.001)
    assert haversine((0,0),(0,180)) == pytest.approx(20015.087,rel=.001)

def test_rank_excludes_unavailable_and_breaks_ties():
    drivers = [Candidate(2,0,0),Candidate(1,0,0),Candidate(3,0,.01,False)]
    assert [id for _,id in rank(drivers,(0,0),0)] == [1,2]

def test_pickup_alignment_differs_from_nearest():
    drivers = [Candidate(1,0,0),Candidate(2,0,.03)]
    assert nearest(drivers,(0,0))[1] == 1
    assert next(rank(drivers,(0,0),8))[1] == 2

def test_empty():
    assert list(rank([], (0,0),4)) == []
    assert nearest([], (0,0)) is None

@pytest.mark.parametrize("state", ["CREATED","ACCEPTED","PREPARING","READY_FOR_PICKUP","PICKED_UP","DELIVERED","CANCELLED"])
def test_state_graph(client, state):
    response = client.post("/api/orders", json={"customer_id":1,"merchant_id":1,"lat":40.7,"lng":-74})
    id = response.json()["id"]
    if state == "CANCELLED":
        assert client.patch(f"/api/orders/{id}/status",json={"status":state}).status_code == 200
    elif state != "CREATED":
        path = ["ACCEPTED","PREPARING","READY_FOR_PICKUP","PICKED_UP","DELIVERED"]
        for target in path[:path.index(state)+1]:
            if target == "PICKED_UP":
                a = client.post(f"/api/orders/{id}/dispatch").json()
                assert client.post(f"/api/assignments/{a['id']}/accept").status_code == 200
            assert client.patch(f"/api/orders/{id}/status",json={"status":target}).status_code == 200
    assert client.get(f"/api/orders/{id}").json()["status"] == state
    assert client.patch(f"/api/orders/{id}/status",json={"status":"CREATED"}).status_code == 409
    assert client.get(f"/api/orders/{id}").json()["status"] == state
