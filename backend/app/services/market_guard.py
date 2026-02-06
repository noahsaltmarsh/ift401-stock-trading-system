from datetime import datetime
from fastapi import HTTPException, status

from app.services.market_time import MarketSettings, is_market_open


def require_market_open(now: datetime, settings: MarketSettings) -> None:
    if not is_market_open(now, settings):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Market is closed",
        )
