# backend/app/core/pubsub.py
from typing import Dict, Set
from starlette.websockets import WebSocket
import json

class Channel:
    """
    简单 PubSub：
      - text：发 JSON 文本
      - tts ：发 JSON 控制 + 二进制音频分片
    由路由负责 ws.accept()；这里不再 accept。
    """
    def __init__(self):
        # topic -> conv_id -> set(WebSocket)
        self._topics: Dict[str, Dict[str, Set[WebSocket]]] = {
            "text": {},
            "tts": {},
        }

    # -------- subscribe / unsubscribe（不 accept，仅登记） --------
    async def sub_text(self, conv_id: str, ws: WebSocket):
        self._topics["text"].setdefault(conv_id, set()).add(ws)

    def unsub_text(self, conv_id: str, ws: WebSocket):
        self._topics["text"].get(conv_id, set()).discard(ws)

    async def sub_tts(self, conv_id: str, ws: WebSocket):
        self._topics["tts"].setdefault(conv_id, set()).add(ws)

    def unsub_tts(self, conv_id: str, ws: WebSocket):
        self._topics["tts"].get(conv_id, set()).discard(ws)

    # -------- publish --------
    async def pub_text(self, conv_id: str, payload: dict):
        conns = list(self._topics["text"].get(conv_id, set()))
        msg = json.dumps(payload)
        for s in conns:
            try:
                await s.send_text(msg)
            except Exception:
                pass

    async def pub_tts_json(self, conv_id: str, payload: dict):
        conns = list(self._topics["tts"].get(conv_id, set()))
        msg = json.dumps(payload)
        for s in conns:
            try:
                await s.send_text(msg)
            except Exception:
                pass

    async def pub_tts_bytes(self, conv_id: str, chunk: bytes):
        conns = list(self._topics["tts"].get(conv_id, set()))
        for s in conns:
            try:
                await s.send_bytes(chunk)
            except Exception:
                pass

channel = Channel()
