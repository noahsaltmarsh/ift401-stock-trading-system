from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, date
from typing import Set
import os


@dataclass
class MarketSettings:
    open_time: time = time(6, 30)   # default example (can change later)
    close_time: time = time(13, 0)  # default example (can change later)
    holidays: Set[date] = field(default_factory=set)
    
    


def is_market_open(now: datetime, settings: MarketSettings) -> bool:
    if os.getenv("DEV_ALWAYS_OPEN", "false").lower() == "true":
        return True
    # Closed on weekends
    if now.weekday() >= 5:
        return False
    # Closed on holidays
    if now.date() in settings.holidays:
        return False
    t = now.time()
    return settings.open_time <= t < settings.close_time

