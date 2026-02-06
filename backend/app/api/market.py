from datetime import datetime, time

from fastapi import APIRouter

from app.services.market_time import MarketSettings, is_market_open

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/status")
def market_status():
    # Temporary defaults (we'll replace with DB/admin settings later)
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    now = datetime.now()
    return {
        "market_open": is_market_open(now, settings),
        "server_time": now.isoformat(),
    }
