from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import employees, recordings, clients, analytics, auth, settings
from app.database import supabase
from app.config import ADMIN_PASSWORD

app = FastAPI(title="Beethoven API", version="1.0.0")


@app.on_event("startup")
async def sync_admin_password():
    """Синхронизирует пароль из .env в БД при запуске."""
    if ADMIN_PASSWORD and ADMIN_PASSWORD != "changeme":
        supabase.table("settings").update(
            {"value": ADMIN_PASSWORD}
        ).eq("key", "admin_password").execute()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(recordings.router)
app.include_router(clients.router)
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(settings.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
