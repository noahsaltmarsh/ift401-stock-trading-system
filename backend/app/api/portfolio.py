# backend/app/api/portfolio.py

# ------------------------------------------------------------

# Portfolio API

# ------------------------------------------------------------

 

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select, func, case 

from sqlalchemy.orm import Session

 

from ..db.session import SessionLocal, set_search_path_to_trading

from ..db.models import User, CashAccount, Stock, Transaction

 

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

 

# ------------------------------------------------------------

# DB session dependency

# ------------------------------------------------------------

 

def get_db():

    db = SessionLocal()

    try:

        set_search_path_to_trading(db)

        yield db

    finally:

        db.close()

 

# ------------------------------------------------------------

# Helper: calculate shares owned per stock

# ------------------------------------------------------------

 

def _get_positions(db: Session, user_id: int) -> dict[int, int]:

    """

    Returns { stock_id: shares_owned }

    shares_owned = sum(buys) - sum(sells)

    """

 

    results = db.execute(

        select(

            Transaction.stock_id,

            func.coalesce(

                func.sum(

                    case(

                        (

                            Transaction.transaction_type == "buy",

                            Transaction.shares,

                        ),

                        (

                            Transaction.transaction_type == "sell",

                            -Transaction.shares,

                        ),

                        else_=0,

                    )

                ),

                0,

            ).label("shares"),

        )

        .where(

            Transaction.user_id == user_id,

            Transaction.stock_id.is_not(None),

        )

        .group_by(Transaction.stock_id)

    ).all()

 

    return {

        row.stock_id: int(row.shares)

        for row in results

        if row.shares > 0

    }

 

# ------------------------------------------------------------

# GET /portfolio/{user_id}

# ------------------------------------------------------------

 

@router.get("/{user_id}")

def get_portfolio(user_id: int, db: Session = Depends(get_db)):

    # Validate user

    user = db.scalar(select(User).where(User.id == user_id))

    if not user:

        raise HTTPException(status_code=404, detail="User not found.")

 

    # Get cash balance

    cash = db.scalar(select(CashAccount).where(CashAccount.user_id == user_id))

    cash_balance_cents = cash.balance_cents if cash else 0

 

    # Get positions

    positions = _get_positions(db, user_id)

 

    portfolio_positions: List[Dict] = []

    total_market_value_cents = 0

 

    for stock_id, shares in positions.items():

        stock = db.scalar(select(Stock).where(Stock.id == stock_id))

        if not stock:

            continue

 

        market_value_cents = shares * stock.current_price_cents

        total_market_value_cents += market_value_cents

 

        portfolio_positions.append({

            "ticker": stock.ticker,

            "shares": shares,

            "currentPrice": stock.current_price_cents / 100,

            "marketValue": market_value_cents / 100,

        })

 

    total_portfolio_value = (cash_balance_cents + total_market_value_cents) / 100

 

    return {

        "userId": user_id,

        "cashBalance": cash_balance_cents / 100,

        "positions": portfolio_positions,

        "totalValue": total_portfolio_value,

    }