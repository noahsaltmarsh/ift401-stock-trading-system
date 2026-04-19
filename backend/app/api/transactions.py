# backend/app/api/transactions.py

# ------------------------------------------------------------

# Transaction History API

# ------------------------------------------------------------

 

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select, desc

from sqlalchemy.orm import Session

 

from ..db.session import SessionLocal, set_search_path_to_trading

from ..db.models import User, Transaction, Stock

 

router = APIRouter(prefix="/transactions", tags=["transactions"])

 

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

# GET /transactions/{user_id}

# ------------------------------------------------------------

 

@router.get("/{user_id}")

def get_transaction_history(user_id: int, db: Session = Depends(get_db)):

    # Validate user exists

    user = db.scalar(select(User).where(User.id == user_id))

    if not user:

        raise HTTPException(status_code=404, detail="User not found.")

 

    tx_rows = db.execute(

        select(Transaction)

        .where(Transaction.user_id == user_id)

        .order_by(desc(Transaction.created_at))

    ).scalars().all()

 

    results = []

 

    for tx in tx_rows:

        stock_ticker = None

        if tx.stock_id:

            stock = db.scalar(select(Stock).where(Stock.id == tx.stock_id))

            stock_ticker = stock.ticker if stock else None

 

        results.append({

            "transactionId": tx.id,

            "type": tx.transaction_type,

            "ticker": stock_ticker,

            "shares": tx.shares,

            "amount": tx.amount_cents / 100,

            "createdAt": tx.created_at.isoformat(),

        })

 

    return {

        "userId": user_id,

        "transactions": results,

    }