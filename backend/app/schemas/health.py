from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Schema for service health status."""

    status: str
    environment: str
    version: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

