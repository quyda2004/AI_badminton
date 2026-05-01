import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.deps import get_db, get_current_user
from models import User, Court, Booking
from schemas.booking import BookingCreate, RescheduleRequest, BookingResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _to_response(b: Booking) -> BookingResponse:
    return BookingResponse(
        id=b.id, user_id=b.user_id, court_id=b.court_id,
        start_time=b.start_time, end_time=b.end_time,
        status=b.status, total_price=float(b.total_price),
        created_at=b.created_at,
    )


@router.get("", response_model=list[BookingResponse])
def list_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bookings = db.execute(
        select(Booking).where(Booking.user_id == user.id).order_by(Booking.start_time.desc())
    ).scalars().all()
    return [_to_response(b) for b in bookings]


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(req: BookingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    court = db.get(Court, req.court_id)
    if not court or court.status != "active":
        raise HTTPException(status_code=404, detail="Sân không tồn tại")

    conflict = db.execute(
        select(Booking).where(
            Booking.court_id   == req.court_id,
            Booking.status     != "cancelled",
            Booking.start_time <  req.end_time,
            Booking.end_time   >  req.start_time,
        )
    ).first()
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Khung giờ đã bị đặt")

    hours       = (req.end_time - req.start_time).total_seconds() / 3600
    total_price = float(court.price_per_hour) * hours

    booking = Booking(
        id=str(uuid.uuid4()), user_id=user.id, court_id=req.court_id,
        start_time=req.start_time, end_time=req.end_time, total_price=total_price,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _to_response(booking)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking không tồn tại")
    return _to_response(booking)


@router.put("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking không tồn tại")
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking đã bị hủy rồi")
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return _to_response(booking)


@router.put("/{booking_id}/reschedule", response_model=BookingResponse)
def reschedule_booking(
    booking_id: str, req: RescheduleRequest,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking không tồn tại")

    court = db.get(Court, booking.court_id)
    hours = (req.new_end_time - req.new_start_time).total_seconds() / 3600

    booking.status = "cancelled"
    db.flush()

    booking.start_time  = req.new_start_time
    booking.end_time    = req.new_end_time
    booking.total_price = float(court.price_per_hour) * hours
    booking.status      = "confirmed"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Khung giờ mới đã bị đặt")
    db.refresh(booking)
    return _to_response(booking)
