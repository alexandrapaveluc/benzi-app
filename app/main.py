from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.station_router import router as station_router


app = FastAPI(
    title="Fuel Finder API",
    description="Backend pentru gasirea benzinariilor din apropiere si compararea preturilor carburantilor.",
    version="1.0.0",
)

# Permite apelarea API-ului din browser, de pe alte domenii (ex. interfata web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
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