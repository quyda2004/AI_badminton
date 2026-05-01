import uuid
from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.deps import get_db, get_current_user, get_admin_user
from models import User, Court, Booking
from schemas.court import CourtCreate, CourtResponse, TimeSlot

router = APIRouter(prefix="/courts", tags=["courts"])

OPEN_HOUR  = 6
CLOSE_HOUR = 22


@router.get("", response_model=list[CourtResponse])
def list_courts(db: Session = Depends(get_db)):
    courts = db.execute(select(Court).where(Court.status == "active")).scalars().all()
    return [CourtResponse(**c.__dict__) for c in courts]


@router.post("", response_model=CourtResponse, status_code=201)
def create_court(data: CourtCreate, db: Session = Depends(get_db), _: User = Depends(get_admin_user)):
    court = Court(id=str(uuid.uuid4()), **data.model_dump())
    db.add(court)
    db.commit()
    db.refresh(court)
    return CourtResponse(**court.__dict__)


@router.get("/{court_id}/availability", response_model=list[TimeSlot])
def get_availability(court_id: str, date: date, db: Session = Depends(get_db)):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Sân không tồn tại")

    slots = []
    for hour in range(OPEN_HOUR, CLOSE_HOUR):
        start_dt = datetime.combine(date, time(hour, 0), tzinfo=timezone.utc)
        end_dt   = start_dt + timedelta(hours=1)

        conflict = db.execute(
            select(Booking).where(
                Booking.court_id == court_id,
                Booking.status   != "cancelled",
                Booking.start_time < end_dt,
                Booking.end_time   > start_dt,
            )
        ).first()

        slots.append(TimeSlot(start=f"{hour:02d}:00", end=f"{hour+1:02d}:00", available=conflict is None))
    return slots
