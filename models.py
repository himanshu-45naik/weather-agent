from pydantic import BaseModel
from datetime import datetime

class ForecastInput(BaseModel):
    place: str
    start_date: datetime
    end_date: datetime