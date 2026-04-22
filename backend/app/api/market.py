from datetime import datetime, time
from typing import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.market_time import MarketSettings, is_market_open
from app.db.session import SessionLocal, set_search_path_to_trading
from app.db.models import MarketHours, Stock

router = APIRouter(prefix="/market", tags=["market"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        set_search_path_to_trading(db)
        yield db
    finally:
        db.close()


@router.get("/status")
def market_status(db: Session = Depends(get_db)):
    settings_row = db.query(MarketHours).first()

    if settings_row:
        settings = MarketSettings(
            open_time=settings_row.opens_at,
            close_time=settings_row.closes_at
        )
    else:
        settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0))

    now = datetime.now()
    return {
        "market_open": is_market_open(now, settings),
        "server_time": now.isoformat(),
        "open_time": str(settings.open_time),
        "close_time": str(settings.close_time),
    }


@router.get("/stocks")
def get_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()

    result = []
    for s in stocks:
        result.append({
            "id": s.id,
            "ticker": s.ticker,
            "company_name": s.company_name,
            "volume": s.volume,
            "current_price_cents": s.current_price_cents,
            "opening_price_cents": s.opening_price_cents,
            "daily_high_cents": s.daily_high_cents,
            "daily_low_cents": s.daily_low_cents,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        })

    return result