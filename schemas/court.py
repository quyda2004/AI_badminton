from pydantic import BaseModel


class CourtCreate(BaseModel):
    name: str
    type: str = "standard"
    price_per_hour: float
    status: str = "active"
    description: str | None = None


class CourtResponse(BaseModel):
    id: str
    name: str
    type: str
    price_per_hour: float
    status: str
    description: str | None


class TimeSlot(BaseModel):
    start: str
    end: str
    available: bool
