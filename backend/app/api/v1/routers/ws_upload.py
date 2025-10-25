import json
import tempfile
import os
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.pubsub import channel
from app.services.asr_openai import webm_to_wav_16k_mono, transcribe_wav_via_url
from app.services.tts_elevenlabs import synth_and_stream_free, synth_and_stream_paid

router = APIRouter()

_sessions: Dict[str, dict] = {}  # conv_id -> {"tmp": file, "accent": str, "model": str}

@router.websocket("/ws/upload-audio")
async def ws_upload(ws: WebSocket):
    await ws.accept()
    print("[ws_upload] connected")
    conv_id: Optional[str] = None
    tmp = None
    try:
        start_msg = await ws.receive_text()
        meta = json.loads(start_msg)
        assert meta.get("type") == "start"
        conv_id = meta.get("conversationId")
        accent = meta.get("accent") or "American English"
        model  = (meta.get("model") or "free").lower()
        print("[ws_upload] start", conv_id, "accent=", accent, "model=", model)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        _sessions[conv_id] = {"tmp": tmp, "accent": accent, "model": model}

        while True:
            pkt = await ws.receive()
            if "bytes" in pkt and pkt["bytes"]:
                tmp.write(pkt["bytes"])
                continue
            if "text" in pkt and pkt["text"]:
                try:
                    j = json.loads(pkt["text"])
                except Exception:
                    continue
                if j.get("type") == "stop":
                    print("[ws_upload] stop", conv_id)
                    try:
                        tmp.flush()
                        tmp.close()
                    except Exception:
                        pass
                    await on_stop_and_publish(conv_id, tmp.name)
                    try:
                        await ws.close()
                    except Exception:
                        pass
                    break
    except WebSocketDisconnect:
        print("[ws_upload] disconnect", conv_id or "")
    except Exception as e:
        print("[ws_upload] error:", repr(e))
    finally:
        ses = _sessions.pop(conv_id or "", None)
        if ses:
            try:
                if ses.get("tmp") and os.path.exists(ses["tmp"].name):
                    os.remove(ses["tmp"].name)
            except Exception:
                pass
        print("[ws_upload] closed", conv_id or "")

async def on_stop_and_publish(conv_id: str, webm_path: str):
    ses = _sessions.get(conv_id, {})
    accent = ses.get("accent", "American English")
    model  = (ses.get("model") or "free").lower()

    print("[on_stop] begin", conv_id)
    wav_path = None
    text = ""
    try:
        wav_path = webm_to_wav_16k_mono(webm_path)
        text = await transcribe_wav_via_url(wav_path)
    except Exception as e:
        text = f"[ASR error] {e}"
    finally:
        try:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
        try:
            if webm_path and os.path.exists(webm_path):
                os.remove(webm_path)
        except Exception:
            pass

    print("[on_stop] asr done text len=", len(text))
    print("[on_stop] ASR text:", text)

    # 1) final 文本推给 /ws/asr-text
    try:
        await channel.pub_text(conv_id, {"type": "final", "text": text})
        print(f"[push] final -> {conv_id}")
    except Exception as e:
        print("[push] final error:", repr(e))

    # 2) TTS（按模型分流；目前 free/paid 等价，实现由 services 负责）
    try:
        print(f"[tts] begin {model=} {accent=}")
        if model == "free":
            await synth_and_stream_free(conv_id, text, accent)
        else:
            await synth_and_stream_paid(conv_id, text, accent)
        print("[tts] done")
    except Exception as e:
        print("[push][tts] error:", repr(e))
