# app/main.py（只显示关键片段）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers.ws_text import router as text_router
from .routers.ws_upload import router as upload_router
from .routers.ws_tts import router as tts_router   # ← 新增

app = FastAPI(title="Accent Translator Backend (Modular)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text_router)
app.include_router(upload_router)
app.include_router(tts_router)   # ← 新增

@app.get("/health")
def health():
    return {"ok": True}
