# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db, close_db
from app.api.v1.routers import auth, accents, session as session_router
from app.api.v1.routers import conversations
app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()

@app.on_event("shutdown")
async def on_shutdown():
    await close_db()

@app.get("/healthz")
def healthz():
    return {"ok": True}

app.include_router(auth.router, prefix="/api/v1")
app.include_router(accents.router, prefix="/api/v1")
app.include_router(session_router.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")