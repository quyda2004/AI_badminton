def test_list_bookings(client, auth_headers):
    res = client.get("/bookings", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_bookings_no_token(client):
    res = client.get("/bookings")
    assert res.status_code == 401


def test_create_booking(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]

    res = client.post("/bookings", headers=auth_headers, json={
        "court_id": court_id,
        "start_time": "2026-06-01T08:00:00+00:00",
        "end_time":   "2026-06-01T10:00:00+00:00",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["court_id"] == court_id
    assert data["status"] == "confirmed"
    assert data["total_price"] > 0


def test_create_booking_duplicate_slot(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[1]["id"]

    payload = {
        "court_id": court_id,
        "start_time": "2026-06-02T10:00:00+00:00",
        "end_time":   "2026-06-02T12:00:00+00:00",
    }
    client.post("/bookings", headers=auth_headers, json=payload)
    res = client.post("/bookings", headers=auth_headers, json=payload)
    assert res.status_code == 409


def test_get_booking(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]

    created = client.post("/bookings", headers=auth_headers, json={
        "court_id": court_id,
        "start_time": "2026-06-03T14:00:00+00:00",
        "end_time":   "2026-06-03T15:00:00+00:00",
    }).json()

    res = client.get(f"/bookings/{created['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_cancel_booking(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]

    created = client.post("/bookings", headers=auth_headers, json={
        "court_id": court_id,
        "start_time": "2026-06-04T16:00:00+00:00",
        "end_time":   "2026-06-04T17:00:00+00:00",
    }).json()

    res = client.put(f"/bookings/{created['id']}/cancel", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


def test_cancel_already_cancelled(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]

    created = client.post("/bookings", headers=auth_headers, json={
        "court_id": court_id,
        "start_time": "2026-06-05T18:00:00+00:00",
        "end_time":   "2026-06-05T19:00:00+00:00",
    }).json()

    client.put(f"/bookings/{created['id']}/cancel", headers=auth_headers)
    res = client.put(f"/bookings/{created['id']}/cancel", headers=auth_headers)
    assert res.status_code == 400


def test_reschedule_booking(client, auth_headers):
    courts = client.get("/courts").json()
    court_id = courts[0]["id"]

    created = client.post("/bookings", headers=auth_headers, json={
        "court_id": court_id,
        "start_time": "2026-06-06T08:00:00+00:00",
        "end_time":   "2026-06-06T09:00:00+00:00",
    }).json()

    res = client.put(f"/bookings/{created['id']}/reschedule", headers=auth_headers, json={
        "new_start_time": "2026-06-07T10:00:00+00:00",
        "new_end_time":   "2026-06-07T11:00:00+00:00",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert "2026-06-07" in data["start_time"]
