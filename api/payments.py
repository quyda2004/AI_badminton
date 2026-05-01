from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.deps import get_db, get_current_user
from models import User, Booking, Payment
from schemas.payment import PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/{booking_id}", response_model=list[PaymentResponse])
def get_payments(booking_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking không tồn tại")

    payments = db.execute(select(Payment).where(Payment.booking_id == booking_id)).scalars().all()
    return [
        PaymentResponse(
            id=p.id, booking_id=p.booking_id, amount=float(p.amount),
            method=p.method, status=p.status, paid_at=p.paid_at, created_at=p.created_at,
        )
        for p in payments
    ]
