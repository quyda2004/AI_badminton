from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import Base, User, Court, Booking, Payment
from config import DATABASE_URL
from security import hash_password


def seed_users(session: Session) -> list[User]:
    users = [
        User(id="nguyen.vana",  email="nguyen.vana@gmail.com",  full_name="Nguyễn Văn A",  phone="0901111111", hashed_password=hash_password("123"),   role="user"),
        User(id="tran.thib",    email="tran.thib@gmail.com",    full_name="Trần Thị B",    phone="0902222222", hashed_password=hash_password("123"),   role="user"),
        User(id="le.vanc",      email="le.vanc@gmail.com",      full_name="Lê Văn C",      phone="0903333333", hashed_password=hash_password("123"),   role="user"),
        User(id="pham.thid",    email="pham.thid@gmail.com",    full_name="Phạm Thị D",    phone="0904444444", hashed_password=hash_password("123"),   role="user"),
        User(id="hoang.vane",   email="hoang.vane@gmail.com",   full_name="Hoàng Văn E",   phone="0905555555", hashed_password=hash_password("123"),   role="user"),
        User(id="vo.thif",      email="vo.thif@gmail.com",      full_name="Võ Thị F",      phone="0906666666", hashed_password=hash_password("123"),   role="user"),
        User(id="dang.vang",    email="dang.vang@gmail.com",    full_name="Đặng Văn G",    phone="0907777777", hashed_password=hash_password("123"),   role="user"),
        User(id="bui.thih",     email="bui.thih@gmail.com",     full_name="Bùi Thị H",     phone="0908888888", hashed_password=hash_password("123"),   role="user"),
        User(id="do.vani",      email="do.vani@gmail.com",      full_name="Đỗ Văn I",      phone="0909999999", hashed_password=hash_password("123"),   role="user"),
        User(id="admin",        email="admin@badminton.com",    full_name="Admin",          phone="0900000000", hashed_password=hash_password("admin"), role="admin"),
    ]
    session.add_all(users)
    session.flush()
    print(f"[OK] Seeded {len(users)} users")
    return users


def seed_courts(session: Session) -> list[Court]:
    courts = [
        Court(id="court_1",  name="Sân 1",  type="standard", price_per_hour=80000,  status="active",   description="Sân tiêu chuẩn khu A"),
        Court(id="court_2",  name="Sân 2",  type="standard", price_per_hour=80000,  status="active",   description="Sân tiêu chuẩn khu A"),
        Court(id="court_3",  name="Sân 3",  type="standard", price_per_hour=90000,  status="active",   description="Sân tiêu chuẩn khu B"),
        Court(id="court_4",  name="Sân 4",  type="standard", price_per_hour=90000,  status="active",   description="Sân tiêu chuẩn khu B"),
        Court(id="court_5",  name="Sân 5",  type="vip",      price_per_hour=150000, status="active",   description="Sân VIP có máy lạnh"),
        Court(id="court_6",  name="Sân 6",  type="vip",      price_per_hour=150000, status="active",   description="Sân VIP có máy lạnh"),
        Court(id="court_7",  name="Sân 7",  type="standard", price_per_hour=70000,  status="active",   description="Sân tiêu chuẩn khu C"),
        Court(id="court_8",  name="Sân 8",  type="standard", price_per_hour=70000,  status="active",   description="Sân tiêu chuẩn khu C"),
        Court(id="court_9",  name="Sân 9",  type="premium",  price_per_hour=120000, status="active",   description="Sân premium có khán đài"),
        Court(id="court_10", name="Sân 10", type="premium",  price_per_hour=120000, status="inactive", description="Đang bảo trì"),
    ]
    session.add_all(courts)
    session.flush()
    print(f"[OK] Seeded {len(courts)} courts")
    return courts


def seed_bookings(session: Session, users: list[User], courts: list[Court]) -> list[Booking]:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    bookings = [
        Booking(id="booking_1",  user_id=users[0].id, court_id=courts[0].id, start_time=now - timedelta(days=5) + timedelta(hours=8),  end_time=now - timedelta(days=5) + timedelta(hours=10), status="confirmed", total_price=160000),
        Booking(id="booking_2",  user_id=users[1].id, court_id=courts[1].id, start_time=now - timedelta(days=4) + timedelta(hours=7),  end_time=now - timedelta(days=4) + timedelta(hours=9),  status="confirmed", total_price=160000),
        Booking(id="booking_3",  user_id=users[2].id, court_id=courts[2].id, start_time=now - timedelta(days=3) + timedelta(hours=9),  end_time=now - timedelta(days=3) + timedelta(hours=11), status="confirmed", total_price=180000),
        Booking(id="booking_4",  user_id=users[3].id, court_id=courts[4].id, start_time=now - timedelta(days=3) + timedelta(hours=14), end_time=now - timedelta(days=3) + timedelta(hours=16), status="cancelled", total_price=300000),
        Booking(id="booking_5",  user_id=users[4].id, court_id=courts[3].id, start_time=now - timedelta(days=2) + timedelta(hours=8),  end_time=now - timedelta(days=2) + timedelta(hours=10), status="confirmed", total_price=180000),
        Booking(id="booking_6",  user_id=users[5].id, court_id=courts[6].id, start_time=now - timedelta(days=2) + timedelta(hours=16), end_time=now - timedelta(days=2) + timedelta(hours=18), status="confirmed", total_price=140000),
        Booking(id="booking_7",  user_id=users[6].id, court_id=courts[8].id, start_time=now - timedelta(days=1) + timedelta(hours=7),  end_time=now - timedelta(days=1) + timedelta(hours=9),  status="confirmed", total_price=240000),
        Booking(id="booking_8",  user_id=users[7].id, court_id=courts[5].id, start_time=now - timedelta(days=1) + timedelta(hours=10), end_time=now - timedelta(days=1) + timedelta(hours=12), status="confirmed", total_price=300000),
        Booking(id="booking_9",  user_id=users[8].id, court_id=courts[7].id, start_time=now + timedelta(days=1) + timedelta(hours=8),  end_time=now + timedelta(days=1) + timedelta(hours=10),  status="confirmed", total_price=140000),
        Booking(id="booking_10", user_id=users[0].id, court_id=courts[4].id, start_time=now + timedelta(days=2) + timedelta(hours=14), end_time=now + timedelta(days=2) + timedelta(hours=16),  status="confirmed", total_price=300000),
    ]
    session.add_all(bookings)
    session.flush()
    print(f"[OK] Seeded {len(bookings)} bookings")
    return bookings


def seed_payments(session: Session, bookings: list[Booking]) -> None:
    payments = [
        Payment(id="payment_1",  booking_id=bookings[0].id, amount=160000, method="cash",    status="paid",    paid_at=bookings[0].start_time),
        Payment(id="payment_2",  booking_id=bookings[1].id, amount=160000, method="banking", status="paid",    paid_at=bookings[1].start_time),
        Payment(id="payment_3",  booking_id=bookings[2].id, amount=180000, method="cash",    status="paid",    paid_at=bookings[2].start_time),
        Payment(id="payment_4",  booking_id=bookings[3].id, amount=300000, method="banking", status="pending", paid_at=None),
        Payment(id="payment_5",  booking_id=bookings[4].id, amount=180000, method="cash",    status="paid",    paid_at=bookings[4].start_time),
        Payment(id="payment_6",  booking_id=bookings[5].id, amount=140000, method="momo",    status="paid",    paid_at=bookings[5].start_time),
        Payment(id="payment_7",  booking_id=bookings[6].id, amount=240000, method="banking", status="paid",    paid_at=bookings[6].start_time),
        Payment(id="payment_8",  booking_id=bookings[7].id, amount=300000, method="momo",    status="paid",    paid_at=bookings[7].start_time),
        Payment(id="payment_9",  booking_id=bookings[8].id, amount=140000, method="cash",    status="pending", paid_at=None),
        Payment(id="payment_10", booking_id=bookings[9].id, amount=300000, method="banking", status="pending", paid_at=None),
    ]
    session.add_all(payments)
    session.flush()
    print(f"[OK] Seeded {len(payments)} payments")


if __name__ == "__main__":
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        seed_users_data    = seed_users(session)
        seed_courts_data   = seed_courts(session)
        seed_bookings_data = seed_bookings(session, seed_users_data, seed_courts_data)
        seed_payments(session, seed_bookings_data)
        session.commit()

    engine.dispose()
    print("[DONE] Seed data hoàn tất!")
