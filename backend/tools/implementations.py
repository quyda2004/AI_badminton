import uuid
from datetime import datetime, time, timedelta, timezone, date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

VN_TZ = timezone(timedelta(hours=7))


def _fmt(dt: datetime) -> str:
    """Trả về datetime dạng string theo múi giờ VN (UTC+7)."""
    return dt.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M")


load_dotenv()

from ..config import DATABASE_URL
from ..models import Court, Booking

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def get_courts() -> list[dict]:
    """Lấy danh sách tất cả sân cầu lông đang hoạt động."""
    with Session() as db:
        courts = db.execute(select(Court).where(Court.status == "active")).scalars().all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "price_per_hour": float(c.price_per_hour),
                "status": c.status,
            }
            for c in courts
        ]


def check_availability(court_id: str, date_str: str) -> list[dict]:
    """
    Kiểm tra slot trống của sân theo ngày.
    date_str: định dạng YYYY-MM-DD
    """
    with Session() as db:
        court = db.get(Court, court_id)
        if not court:
            return [{"error": "Sân không tồn tại"}]

        check_date = date.fromisoformat(date_str)
        slots = []
        for hour in range(6, 22):
            start_dt = datetime.combine(check_date, time(hour, 0), tzinfo=VN_TZ)
            end_dt = start_dt + timedelta(hours=1)
            conflict = db.execute(
                select(Booking).where(
                    Booking.court_id == court_id,
                    Booking.status != "cancelled",
                    Booking.start_time < end_dt,
                    Booking.end_time > start_dt,
                )
            ).first()
            slots.append({
                "start": f"{hour:02d}:00",
                "end": f"{hour+1:02d}:00",
                "available": conflict is None,
            })
        return slots


def create_booking(user_id: str, court_id: str, date_str: str, start_hour: int, end_hour: int) -> dict:
    """
    Đặt sân cho user.
    date_str: YYYY-MM-DD, start_hour/end_hour: 6-22
    """
    with Session() as db:
        court = db.get(Court, court_id)
        if not court or court.status != "active":
            return {"error": "Sân không tồn tại hoặc không hoạt động"}

        check_date = date.fromisoformat(date_str)
        start_dt = datetime.combine(check_date, time(start_hour, 0), tzinfo=VN_TZ)
        end_dt = datetime.combine(check_date, time(end_hour, 0), tzinfo=VN_TZ)

        conflict = db.execute(
            select(Booking).where(
                Booking.court_id == court_id,
                Booking.status != "cancelled",
                Booking.start_time < end_dt,
                Booking.end_time > start_dt,
            )
        ).first()
        if conflict:
            return {"error": "Khung giờ này đã được đặt rồi"}

        hours = (end_dt - start_dt).total_seconds() / 3600
        total_price = float(court.price_per_hour) * hours

        booking = Booking(
            id=str(uuid.uuid4()),
            user_id=user_id,
            court_id=court_id,
            start_time=start_dt,
            end_time=end_dt,
            total_price=total_price,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return {
            "booking_id": booking.id,
            "court": court.name,
            "start_time": _fmt(booking.start_time),
            "end_time": _fmt(booking.end_time),
            "total_price": float(booking.total_price),
            "status": booking.status,
        }


def get_my_bookings(user_id: str) -> list[dict]:
    """Lấy danh sách booking của user."""
    with Session() as db:
        bookings = db.execute(
            select(Booking, Court)
            .join(Court, Booking.court_id == Court.id)
            .where(Booking.user_id == user_id)
            .order_by(Booking.start_time.desc())
        ).all()
        return [
            {
                "booking_id": b.id,
                "court": c.name,
                "start_time": _fmt(b.start_time),
                "end_time": _fmt(b.end_time),
                "status": b.status,
                "total_price": float(b.total_price),
            }
            for b, c in bookings
        ]


def cancel_booking(user_id: str, booking_id: str) -> dict:
    """Hủy booking của user theo booking_id."""
    with Session() as db:
        booking = db.get(Booking, booking_id)
        if not booking or booking.user_id != user_id:
            return {"error": "Booking không tồn tại"}
        if booking.status == "cancelled":
            return {"error": "Booking đã bị hủy rồi"}
        booking.status = "cancelled"
        db.commit()
        return {"booking_id": booking_id, "status": "cancelled"}


def cancel_booking_by_info(user_id: str, court_name: str, date_str: str, start_hour: int) -> dict:
    """
    Hủy booking theo tên sân, ngày và giờ bắt đầu — không cần booking_id.
    date_str: YYYY-MM-DD, start_hour: 6-21
    """
    with Session() as db:
        check_date = date.fromisoformat(date_str)
        start_dt = datetime.combine(check_date, time(start_hour, 0), tzinfo=VN_TZ)

        result = db.execute(
            select(Booking, Court)
            .join(Court, Booking.court_id == Court.id)
            .where(
                Booking.user_id == user_id,
                Booking.status != "cancelled",
                Booking.start_time == start_dt,
                Court.name.ilike(f"%{court_name}%"),
            )
        ).first()

        if not result:
            return {"error": f"Không tìm thấy booking sân '{court_name}' ngày {date_str} lúc {start_hour:02d}:00"}

        booking, court = result
        booking.status = "cancelled"
        db.commit()
        return {
            "booking_id": booking.id,
            "court": court.name,
            "start_time": _fmt(booking.start_time),
            "end_time": _fmt(booking.end_time),
            "status": "cancelled",
        }
