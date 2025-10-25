from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
import json
from app.core.pubsub import channel

router = APIRouter()

@router.websocket("/ws/asr-text")
async def ws_asr_text(ws: WebSocket):
    await ws.accept()
    print("[ws_text] connected")
    conv_id = None
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "subscribe":
                conv_id = msg.get("conversationId")
                await channel.sub_text(conv_id, ws)
                print("[ws_text] subscribed", conv_id)
                # 回 ready（可选）
                await ws.send_text(json.dumps({"type": "ready", "conversationId": conv_id}))
                # 立刻发一条 ping，验证前端 onmessage 正常
                await ws.send_text(json.dumps({"type":"interim","text":"__ping__","ts":0}))
    except WebSocketDisconnect:
        if conv_id:
            channel.unsub_text(conv_id, ws)
        print("[ws_text] disconnected")
    except Exception as e:
        if conv_id:
            channel.unsub_text(conv_id, ws)
        print("[ws_text] error:", repr(e))
