from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ActivityItem(BaseModel):
    id: str
    type: str
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    tournaments_count: int
    teams_count: int
    players_count: int
    scheduled_matches_count: int
    recent_activities: List[ActivityItem]

    model_config = ConfigDict(from_attributes=True)
