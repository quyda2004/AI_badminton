import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from models import Base
from config import DATABASE_URL
from scripts.seed import seed_users, seed_courts, seed_bookings, seed_payments
from sqlalchemy.orm import Session

engine = create_engine(DATABASE_URL, echo=False)

print("[...] Xóa toàn bộ tables...")
Base.metadata.drop_all(engine)

print("[...] Tạo lại tables...")
Base.metadata.create_all(engine)

print("[...] Seed data...")
with Session(engine) as session:
    users    = seed_users(session)
    courts   = seed_courts(session)
    bookings = seed_bookings(session, users, courts)
    seed_payments(session, bookings)
    session.commit()

engine.dispose()
print("[DONE] Reset DB hoàn tất!")
