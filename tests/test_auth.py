def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_register_success(client):
    res = client.post("/auth/register", json={
        "email": "newuser@gmail.com",
        "password": "password123",
        "full_name": "New User",
        "phone": "0911111111",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@gmail.com"
    assert data["role"] == "user"
    assert "id" in data


def test_register_duplicate_email(client):
    payload = {"email": "duplicate@gmail.com", "password": "123", "full_name": "Test"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 409


def test_login_success(client):
    client.post("/auth/register", json={"email": "logintest@gmail.com", "password": "abc123", "full_name": "Login Test"})
    res = client.post("/auth/login", json={"email": "logintest@gmail.com", "password": "abc123"})
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    res = client.post("/auth/login", json={"email": "nguyen.vana@gmail.com", "password": "saimatkhau"})
    assert res.status_code == 401


def test_login_wrong_email(client):
    res = client.post("/auth/login", json={"email": "khongtontai@gmail.com", "password": "123"})
    assert res.status_code == 401


def test_me(client, auth_headers):
    res = client.get("/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "email" in data
    assert "hashed_password" not in data


def test_me_no_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
