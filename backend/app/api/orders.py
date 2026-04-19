# backend/app/api/orders.py

# ------------------------------------------------------------

# Orders API

# - BUY: fully implemented (commit/rollback pattern)

# - SELL: fully implemented (commit/rollback pattern)

# - CANCEL: placeholder (will implement next)

# ------------------------------------------------------------

 

from datetime import datetime, time

from typing import Generator

 

from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BaseModel, Field

from sqlalchemy import select, func

from sqlalchemy.orm import Session

 

# Relative imports within the "app" package

from ..db.session import SessionLocal, set_search_path_to_trading

from ..db.models import (

    User, CashAccount, Stock, Order, Transaction, MarketHours
)

from ..services.market_guard import require_market_open

from ..services.market_time import MarketSettings

 

router = APIRouter(prefix="/orders", tags=["orders"])

 

# ------------------------------------------------------------

# Request Models

# ------------------------------------------------------------



class BuyRequest(BaseModel):

    user_id: int = Field(gt=0)

    ticker: str = Field(min_length=1, max_length=10)

    shares: int = Field(gt=0)

 

class SellRequest(BaseModel):

    user_id: int = Field(gt=0)

    ticker: str = Field(min_length=1, max_length=10)

    shares: int = Field(gt=0)

 

# ------------------------------------------------------------

# DB Session Dependency

# ------------------------------------------------------------

 

def get_db() -> Generator[Session, None, None]:

    """

    Provides a SQLAlchemy Session and ensures search_path is set for the request.

    NOTE: Executing SET search_path will open a transaction (autobegin) in SA 2.0.

    That's fine because we explicitly commit/rollback in endpoints (no db.begin()).

    """

    db = SessionLocal()

    try:

        set_search_path_to_trading(db)

        yield db

    finally:

        db.close()

 

# ------------------------------------------------------------

# Helper functions

# ------------------------------------------------------------

 

def _market_settings(db: Session) -> MarketSettings:
    settings = db.query(MarketHours).first()

    if not settings:
        # fallback if nothing set yet
        return MarketSettings(open_time=time(9, 30), close_time=time(16, 0))

    return MarketSettings(
        open_time=settings.opens_at,
        close_time=settings.closes_at
    )

 

def _get_user_and_cash(db: Session, user_id: int) -> tuple[User, CashAccount]:

    user = db.scalar(select(User).where(User.id == user_id))

    if not user:

        raise HTTPException(status_code=404, detail="User not found.")

    cash = db.scalar(select(CashAccount).where(CashAccount.user_id == user_id))

    if not cash:

        raise HTTPException(status_code=409, detail="Cash account missing for user.")

    return user, cash

 

def _get_stock(db: Session, ticker: str) -> Stock:

    stock = db.scalar(select(Stock).where(Stock.ticker == ticker.upper()))

    if not stock:

        raise HTTPException(status_code=404, detail="Stock not found.")

    return stock

 

def _get_shares_held(db: Session, user_id: int, stock_id: int) -> int:

    """shares_held = sum(buys) - sum(sells) using transactions table."""

    buy_sum = db.scalar(

        select(func.coalesce(func.sum(Transaction.shares), 0)).where(

            Transaction.user_id == user_id,

            Transaction.stock_id == stock_id,

            Transaction.transaction_type == "buy",

        )

    ) or 0

    sell_sum = db.scalar(

        select(func.coalesce(func.sum(Transaction.shares), 0)).where(

            Transaction.user_id == user_id,

            Transaction.stock_id == stock_id,

            Transaction.transaction_type == "sell",

        )

    ) or 0

    return int(buy_sum) - int(sell_sum)

 

# ------------------------------------------------------------

# BUY  (commit/rollback; no with db.begin())

# ------------------------------------------------------------

 

@router.post("/buy")

def buy_order(body: BuyRequest, db: Session = Depends(get_db)):

    # Market hours (dev bypass handled inside require_market_open via env)

    settings = _market_settings(db)

    require_market_open(datetime.now(), settings)

 

    # Basic validations

    if body.shares <= 0:

        raise HTTPException(status_code=422, detail="Shares must be > 0.")

 

    # Entities

    user, cash = _get_user_and_cash(db, body.user_id)

    stock = _get_stock(db, body.ticker)

 

    # Pricing / funds check

    price_cents = stock.current_price_cents

    cost_cents = price_cents * body.shares

    if cash.balance_cents < cost_cents:

        raise HTTPException(status_code=400, detail="Insufficient balance.")

 

    # Transactional work (autobegin already active after first execute)

    try:

        # Create order

        order = Order(

            user_id=user.id,

            stock_id=stock.id,

            order_type="buy",

            shares=body.shares,

            status="pending",

            created_at=datetime.utcnow(),

        )

        db.add(order)

        db.flush()  # populate order.id

 

        # Create buy transaction

        tx = Transaction(

            order_id=order.id,

            user_id=user.id,

            stock_id=stock.id,

            transaction_type="buy",

            amount_cents=cost_cents,

            shares=body.shares,

            created_at=datetime.utcnow(),

        )

        db.add(tx)

 

        # Deduct cash

        cash.balance_cents -= cost_cents

        cash.updated_at = datetime.utcnow()

 

        # Finalize order

        order.status = "executed"

        order.executed_at = datetime.utcnow()

 

        db.commit()  # ✅ commit the work

    except Exception:

        db.rollback()  # ✅ rollback on any failure

        raise

 

    return {

        "status": "executed",

        "orderId": order.id,

        "userId": user.id,

        "ticker": stock.ticker,

        "shares": body.shares,

        "fillPrice": float(price_cents) / 100.0,

        "cost": float(cost_cents) / 100.0,

        "cashBalance": float(cash.balance_cents) / 100.0,

    }

 

# ------------------------------------------------------------

# SELL (commit/rollback; no with db.begin())

# ------------------------------------------------------------

 

@router.post("/sell")

def sell_order(body: SellRequest, db: Session = Depends(get_db)):

    # Market hours (dev bypass handled inside require_market_open via env)

    settings = _market_settings(db)

    require_market_open(datetime.now(), settings)

 

    # Basic validations

    if body.shares <= 0:

        raise HTTPException(status_code=422, detail="Shares must be > 0.")

 

    # Entities

    user, cash = _get_user_and_cash(db, body.user_id)

    stock = _get_stock(db, body.ticker)

 

    # Check holdings

    shares_held = _get_shares_held(db, user.id, stock.id)

    if shares_held < body.shares:

        raise HTTPException(status_code=400, detail="Insufficient shares to sell.")

 

    # Pricing / proceeds

    price_cents = stock.current_price_cents

    proceeds_cents = price_cents * body.shares

 

    # Transactional work

    try:

        # Create order

        order = Order(

            user_id=user.id,

            stock_id=stock.id,

            order_type="sell",

            shares=body.shares,

            status="pending",

            created_at=datetime.utcnow(),

        )

        db.add(order)

        db.flush()

 

        # Create sell transaction

        tx = Transaction(

            order_id=order.id,

            user_id=user.id,

            stock_id=stock.id,

            transaction_type="sell",

            amount_cents=proceeds_cents,

            shares=body.shares,

            created_at=datetime.utcnow(),

        )

        db.add(tx)

 

        # Credit cash

        cash.balance_cents += proceeds_cents

        cash.updated_at = datetime.utcnow()

 

        # Finalize order

        order.status = "executed"

        order.executed_at = datetime.utcnow()

 

        db.commit()

    except Exception:

        db.rollback()

        raise

 

    return {

        "status": "executed",

        "orderId": order.id,

        "userId": user.id,

        "ticker": stock.ticker,

        "sharesSold": body.shares,

        "fillPrice": float(price_cents) / 100.0,

        "proceeds": float(proceeds_cents) / 100.0,

        "cashBalance": float(cash.balance_cents) / 100.0,

    }

 

# ------------------------------------------------------------
# CANCEL (simplified — pending → canceled, no reversals)
# ------------------------------------------------------------

@router.post("/cancel/{order_id}")
def cancel_order(
    order_id: int,
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    # Market hours (dev bypass handled inside require_market_open)
    settings = _market_settings(db)
    require_market_open(datetime.now(), settings)

    # Load order
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Ownership check
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Order does not belong to user.")

    # Only pending orders can be canceled
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be canceled.")

    # Transactional update
    try:
        order.status = "canceled"
        order.canceled_at = datetime.utcnow()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "canceled",
        "orderId": order.id,
        "userId": user_id,
        "message": "Order successfully canceled."
    }

@router.post("/debug/create-pending")
def create_pending_order(
    user_id: int = Query(..., gt=0),
    ticker: str = Query(..., min_length=1, max_length=10),
    shares: int = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    # Load user + stock
    user, _ = _get_user_and_cash(db, user_id)
    stock = _get_stock(db, ticker)

    # Create a pending order with NO execution
    try:
        order = Order(
            user_id=user.id,
            stock_id=stock.id,
            order_type="buy",   # or "sell" — doesn't matter for cancel testing
            shares=shares,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(order)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Pending order created for testing.",
        "orderId": order.id,
        "userId": user.id,
        "ticker": stock.ticker,
        "shares": shares,
        "status": "pending"
    }