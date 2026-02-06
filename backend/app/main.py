from fastapi import FastAPI

from app.api.market import router as market_router
from app.api.orders import router as orders_router

app = FastAPI(title="IFT 401 Stock Trading System API")

# Register API routers
app.include_router(market_router)
app.include_router(orders_router)


@app.get("/health")
def health():
    return {"status": "ok"}
