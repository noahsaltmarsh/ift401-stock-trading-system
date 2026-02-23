from datetime import datetime, time

from fastapi import APIRouter
from pydantic import BaseModel, Field

class BuyRequest(BaseModel):
    user_id: int = Field(gt=0)
    ticker: str = Field(min_length=1, max_length=10)
    shares: int = Field(gt=0)

class SellRequest(BaseModel):
    user_id: int = Field(gt=0)
    ticker: str = Field(min_length=1, max_length=10)
    shares: int = Field(gt=0)
    


from app.services.market_guard import require_market_open
from app.services.market_time import MarketSettings

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/buy")
def buy_order():
    # Temporary defaults (we'll replace with DB/admin settings later)
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    require_market_open(datetime.now(), settings)

    # Placeholder until DB is wired
    return {
        "status": "accepted",
        "action": "buy",
        "ticker": body.ticker,
        "shares": body.shares,
        "user_id": body.user_id,
    }
@router.post("/sell")
def sell_order():
    # Temporary defaults (we'll replace with DB/admin settings later)
    settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))
    require_market_open(datetime.now(), settings)

    return {
        "status": "accepted",
        "action": "sell",
        "ticker": body.ticker,
        "shares": body.shares,
        "user_id": body.user_id,
    }

