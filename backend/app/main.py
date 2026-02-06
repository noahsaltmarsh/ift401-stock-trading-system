from fastapi import FastAPI

app = FastAPI(title="IFT 401 Stock Trading System API")

@app.get("/health")
def health():
    return {"status": "ok"}
