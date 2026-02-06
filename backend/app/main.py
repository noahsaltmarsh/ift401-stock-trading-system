from fastapi import FastAPI

from app.api.market import router as market_router

app = FastAPI(title="IFT 401 Stock Trading System API")

app.include_router(market_router)

@app.get("/health")
def health():
    return {"status": "ok"}
