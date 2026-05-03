from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .deps import get_db, get_admin_user
from ..models import User, Court, Booking, Payment

router = APIRouter(prefix="/admin", tags=["admin"])

VN_TZ = timezone(timedelta(hours=7))


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    today_start = datetime.now(VN_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end   = today_start + timedelta(days=1)

    total_bookings  = db.execute(select(func.count()).select_from(Booking)).scalar()
    bookings_today  = db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.start_time >= today_start,
            Booking.start_time <  today_end,
        )
    ).scalar()
    total_revenue   = db.execute(
        select(func.coalesce(func.sum(Booking.total_price), 0)).where(Booking.status != "cancelled")
    ).scalar()
    active_courts   = db.execute(select(func.count()).select_from(Court).where(Court.status == "active")).scalar()
    total_users     = db.execute(select(func.count()).select_from(User)).scalar()

    return {
        "total_bookings":  total_bookings,
        "bookings_today":  bookings_today,
        "total_revenue":   float(total_revenue),
        "active_courts":   active_courts,
        "total_users":     total_users,
    }


@router.get("/bookings")
def get_all_bookings(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    rows = db.execute(
        select(Booking, Court)
        .join(Court, Booking.court_id == Court.id)
        .order_by(Booking.created_at.desc())
    ).all()
    return [
        {
            "id":          b.id,
            "user_id":     b.user_id,
            "court_name":  c.name,
            "start_time":  b.start_time.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M"),
            "status":      b.status,
            "total_price": float(b.total_price),
        }
        for b, c in rows
    ]
