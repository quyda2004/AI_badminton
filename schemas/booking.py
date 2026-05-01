from datetime import datetime
from pydantic import BaseModel


class BookingCreate(BaseModel):
    court_id: str
    start_time: datetime
    end_time: datetime


class RescheduleRequest(BaseModel):
    new_start_time: datetime
    new_end_time: datetime


class BookingResponse(BaseModel):
    id: str
    user_id: str
    court_id: str
    start_time: datetime
    end_time: datetime
    status: str
    total_price: float
    created_at: datetime
