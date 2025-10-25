# backend/app/routers/ws_tts.py
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
import json
from app.core.pubsub import channel

router = APIRouter()

@router.websocket("/ws/tts-audio")
async def ws_tts(ws: WebSocket):
    await ws.accept()                     # ← 由路由统一 accept
    print("[ws_tts] connected")
    conv_id = None
    try:
        while True:
            raw = await ws.receive_text() # 已 accept，才能 receive
            msg = json.loads(raw)
            if msg.get("type") == "start":
                conv_id = msg.get("conversationId")
                await channel.sub_tts(conv_id, ws)    # 这里只做登记
                print("[ws_tts] subscribed", conv_id)
                await ws.send_text(json.dumps({"type": "ready", "conversationId": conv_id}))
    except WebSocketDisconnect:
        if conv_id:
            channel.unsub_tts(conv_id, ws)
        print("[ws_tts] disconnected")
    except Exception as e:
        if conv_id:
            channel.unsub_tts(conv_id, ws)
        print("[ws_tts] error:", repr(e))
