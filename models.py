from pydantic import BaseModel
from datetime import datetime
from enum import IntEnum

class ForecastInput(BaseModel):
    place: str
    start_date: datetime
    end_date: datetime

class WeatherCodes(IntEnum):
    CLEAR_SKY = 0
    MAINLY_CLEAR = 1
    PARTLY_CLOUDY = 2
    OVERCAST = 3

    FOG = 45
    ICY_FOG = 48

    LIGHT_DRIZZLE = 51
    MODERATE_DRIZZLE = 53
    DENSE_DRIZZLE = 55

    SLIGHT_RAIN = 61
    MODERATE_RAIN = 63
    HEAVY_RAIN = 65

    SLIGHT_SNOW = 71
    MODERATE_SNOW = 73
    HEAVY_SNOW = 75
    SNOW_GRAINS = 77

    SLIGHT_SHOWERS = 80
    MODERATE_SHOWERS = 81
    VIOLENT_SHOWERS = 82

    SLIGHT_SNOW_SHOWERS = 85
    HEAVY_SNOW_SHOWERS = 86

    THUNDERSTORM = 95
    THUNDERSTORM_HAIL = 96
    THUNDERSTORM_HEAVY_HAIL = 99