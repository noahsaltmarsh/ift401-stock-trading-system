from fastapi import FastAPI
import threading
import time
import random

from app.api.market import router as market_router
from app.api.orders import router as orders_router
from app.api import portfolio
from app.api import transactions
from app.api import admin

from app.db.session import SessionLocal
from app.db.models import Stock

app = FastAPI(title="IFT 401 Stock Trading System API")

# Register API routers
app.include_router(market_router)
app.include_router(orders_router)
app.include_router(portfolio.router)
app.include_router(transactions.router)
app.include_router(admin.router)


def update_stock_prices():
    while True:
        db = SessionLocal()
        try:
            stocks = db.query(Stock).all()

            for stock in stocks:
                percent_change = random.uniform(-0.02, 0.02)

                current_price = stock.current_price_cents
                new_price = int(current_price * (1 + percent_change))

                if new_price < 1:
                    new_price = 1

                stock.current_price_cents = new_price

                if new_price > stock.daily_high_cents:
                    stock.daily_high_cents = new_price

                if stock.daily_low_cents == 0 or new_price < stock.daily_low_cents:
                    stock.daily_low_cents = new_price

            db.commit()

        except Exception as e:
            print("Price generator error:", e)
            db.rollback()

        finally:
            db.close()

        time.sleep(15)


@app.on_event("startup")
def start_price_generator():
    thread = threading.Thread(target=update_stock_prices, daemon=True)
    thread.start()


@app.get("/health")
def health():
    return {"status": "ok"}