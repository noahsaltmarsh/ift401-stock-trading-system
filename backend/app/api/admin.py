from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, set_search_path_to_trading
from app.db.models import Stock, MarketHours

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        set_search_path_to_trading(db)
        yield db
    finally:
        db.close()


def dollars_to_cents(amount: float) -> int:
    return int(round(amount * 100))


@router.post("/admin/stocks/create")
def create_stock(
    ticker: str,
    company_name: str,
    volume: int,
    initial_price: float,
    db: Session = Depends(get_db)
):
    ticker = ticker.strip().upper()

    existing = db.query(Stock).filter(Stock.ticker == ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ticker already exists")

    price_cents = dollars_to_cents(initial_price)

    new_stock = Stock(
        ticker=ticker,
        company_name=company_name,
        volume=volume,
        current_price_cents=price_cents,
        opening_price_cents=price_cents,
        daily_high_cents=price_cents,
        daily_low_cents=price_cents
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return {
        "id": new_stock.id,
        "ticker": new_stock.ticker,
        "company_name": new_stock.company_name,
        "volume": new_stock.volume,
        "price": new_stock.current_price_cents / 100
    }

from app.db.models import MarketHours
from datetime import time


@router.post("/admin/market-hours")
def set_market_hours(
    open_time: str,
    close_time: str,
    db: Session = Depends(get_db)
):
    try:
        open_parsed = time.fromisoformat(open_time)
        close_parsed = time.fromisoformat(close_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Time must be HH:MM format")

    settings = db.query(MarketHours).first()

    if not settings:
        settings = MarketHours(
            opens_at=open_parsed,
            closes_at=close_parsed
        )
        db.add(settings)
    else:
        settings.opens_at = open_parsed
        settings.closes_at = close_parsed

    db.commit()
    db.refresh(settings)

    return {
        "message": "Market hours updated",
        "open_time": str(settings.opens_at),
        "close_time": str(settings.closes_at)
    }