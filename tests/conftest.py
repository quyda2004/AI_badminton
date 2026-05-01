import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.deps import engine
from models import Base
from scripts.seed import seed_users, seed_courts, seed_bookings, seed_payments


@pytest.fixture(scope="session", autouse=True)
def reset_db():
    # Reset sạch DB trước mỗi lần chạy test
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        users    = seed_users(session)
        courts   = seed_courts(session)
        bookings = seed_bookings(session, users, courts)
        seed_payments(session, bookings)
        session.commit()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_headers(client):
    res = client.post("/auth/login", json={"email": "nguyen.vana@gmail.com", "password": "123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    res = client.post("/auth/login", json={"email": "admin@badminton.com", "password": "admin"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
