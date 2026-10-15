from typing import Literal
from pydantic import BaseModel, Field
Status = Literal["CREATED", "ACCEPTED", "PREPARING", "READY_FOR_PICKUP", "PICKED_UP", "DELIVERED", "CANCELLED"]
class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
class NewOrder(Location):
    customer_id: int = Field(gt=0)
    merchant_id: int = Field(gt=0)
    prep_minutes: float = Field(default=8, ge=0, le=120)
class StateChange(BaseModel):
    status: Status
class NewDriver(Location):
    name: str = Field(min_length=1, max_length=100)
class DriverChange(Location):
    available: bool
