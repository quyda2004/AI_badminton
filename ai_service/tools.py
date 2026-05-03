"""
Tất cả tool gọi HTTP tới backend-service.
KHÔNG query DB trực tiếp — đúng với kiến trúc microservice.
"""
from datetime import datetime, date, time, timedelta, timezone

import httpx

from .config import BACKEND_SERVICE_URL

VN_TZ = timezone(timedelta(hours=7))

_HEADERS = {"Content-Type": "application/json"}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_courts(token: str) -> list[dict]:
    with httpx.Client() as client:
        res = client.get(f"{BACKEND_SERVICE_URL}/courts", headers=_auth(token))
        return res.json()


def check_availability(token: str, court_id: str, date_str: str) -> list[dict]:
    with httpx.Client() as client:
        res = client.get(
            f"{BACKEND_SERVICE_URL}/courts/{court_id}/availability",
            params={"date": date_str},
            headers=_auth(token),
        )
        return res.json()


def create_booking(token: str, court_id: str, date_str: str, start_hour: int, end_hour: int) -> dict:
    check_date = date.fromisoformat(date_str)
    start_dt   = datetime.combine(check_date, time(start_hour, 0), tzinfo=VN_TZ)
    end_dt     = datetime.combine(check_date, time(end_hour,   0), tzinfo=VN_TZ)

    with httpx.Client() as client:
        res = client.post(
            f"{BACKEND_SERVICE_URL}/bookings",
            json={
                "court_id":   court_id,
                "start_time": start_dt.isoformat(),
                "end_time":   end_dt.isoformat(),
            },
            headers=_auth(token),
        )
        return res.json()


def get_my_bookings(token: str) -> list[dict]:
    with httpx.Client() as client:
        res = client.get(f"{BACKEND_SERVICE_URL}/bookings", headers=_auth(token))
        return res.json()


def cancel_booking(token: str, booking_id: str) -> dict:
    with httpx.Client() as client:
        res = client.put(
            f"{BACKEND_SERVICE_URL}/bookings/{booking_id}/cancel",
            headers=_auth(token),
        )
        return res.json()


def cancel_booking_by_info(token: str, court_name: str, date_str: str, start_hour: int) -> dict:
    with httpx.Client() as client:
        res = client.get(f"{BACKEND_SERVICE_URL}/bookings", headers=_auth(token))
        bookings = res.json()

    check_date = date.fromisoformat(date_str)

    target = None
    for b in bookings:
        if b.get("status") == "cancelled":
            continue
        if court_name.lower() not in b.get("court_name", "").lower():
            continue
        raw = b.get("start_time", "")
        booking_start = datetime.fromisoformat(raw)
        if booking_start.tzinfo is None:
            booking_start = booking_start.replace(tzinfo=timezone.utc)
        booking_start_vn = booking_start.astimezone(VN_TZ)
        if booking_start_vn.date() == check_date and booking_start_vn.hour == start_hour:
            target = b
            break

    if not target:
        return {"error": f"Không tìm thấy booking sân '{court_name}' ngày {date_str} lúc {start_hour:02d}:00"}

    with httpx.Client() as client:
        res = client.put(
            f"{BACKEND_SERVICE_URL}/bookings/{target['id']}/cancel",
            headers=_auth(token),
        )
        return res.json()
