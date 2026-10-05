from fastapi import FastAPI

from app.routers.station_router import router as station_router


app = FastAPI(
    title="Fuel Finder API",
    description="Backend pentru gasirea benzinariilor din apropiere si compararea preturilor carburantilor.",
    version="1.0.0",
)

app.include_router(station_router)


@app.get("/")
def root():
    return {
        "application": "Fuel Finder API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}