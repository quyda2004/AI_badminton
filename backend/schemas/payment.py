from datetime import datetime
from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    amount: float
    method: str
    status: str
    paid_at: datetime | None
    created_at: datetime
