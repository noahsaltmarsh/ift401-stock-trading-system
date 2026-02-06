from datetime import datetime, time

from fastapi import APIRouter

from app.services.market_guard import require_market_open
from app.services.market_time import MarketSettings

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/buy")
def buy_order():
    # Temporary defaults (we'll replace with DB/admin settings later)
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    require_market_open(datetime.now(), settings)

    # Placeholder until DB is wired
    return {"status": "accepted"}
