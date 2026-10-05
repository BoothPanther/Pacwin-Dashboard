from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from reports import router as reports_router
from seats import router as seats_router
from booths import router as booths_router


app = FastAPI(
    title="Pacwin Political Intelligence API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(reports_router)
app.include_router(seats_router)
app.include_router(booths_router)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": "Pacwin",
        "message": "Pacwin backend is running"
    }