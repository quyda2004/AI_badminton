def test_list_courts(client):
    res = client.get("/courts")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_courts_only_active(client):
    courts = client.get("/courts").json()
    for court in courts:
        assert court["status"] == "active"


def test_create_court_as_admin(client, admin_headers):
    res = client.post("/courts", headers=admin_headers, json={
        "name": "Sân Test",
        "type": "standard",
        "price_per_hour": 100000,
        "status": "active",
        "description": "Sân tạo từ test",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Sân Test"
    assert data["price_per_hour"] == 100000.0


def test_create_court_as_user_forbidden(client, auth_headers):
    res = client.post("/courts", headers=auth_headers, json={
        "name": "Sân Lậu",
        "price_per_hour": 50000,
    })
    assert res.status_code == 403


def test_create_court_no_token(client):
    res = client.post("/courts", json={"name": "Sân X", "price_per_hour": 50000})
    assert res.status_code == 401


def test_get_availability(client):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]
    res = client.get(f"/courts/{court_id}/availability", params={"date": "2026-05-10"})
    assert res.status_code == 200
    slots = res.json()
    assert len(slots) == 16  # 6h → 22h = 16 slots
    for slot in slots:
        assert "start" in slot
        assert "end" in slot
        assert "available" in slot


def test_get_availability_invalid_court(client):
    res = client.get("/courts/khongtontai/availability", params={"date": "2026-05-10"})
    assert res.status_code == 404
