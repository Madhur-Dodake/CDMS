import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VenueBase(BaseModel):
    venue_name: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, ge=0)


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    venue_name: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, ge=0)


class VenueResponse(VenueBase):
    venue_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
