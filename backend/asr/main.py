from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from openai import OpenAI
import tempfile, os
import asyncio

app = FastAPI(title="BE-5 ASR Sprint1 - WAV Only (Online Whisper)")

# 初始化 OpenAI 客户端（读取环境变量中的 API Key）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(file_path: str):
    """调用 OpenAI Whisper API 识别整段 WAV 音频"""
    try:
        with open(file_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )

        # segments 可能不存在，使用 getattr 安全访问
        segments = getattr(result, "segments", [])

        return {
            "success": True,
            "data": {
                "text": result.text.strip(),
                "segments": [
                    {
                        "startMs": int(seg.start * 1000),
                        "endMs": int(seg.end * 1000),
                        "text": seg.text.strip()
                    }
                    for seg in segments
                ]
            }
        }
    except Exception as e:
        return {"success": False, "error": {"message": str(e)}}

async def transcribe_audio_async(file_path: str):
    """异步调用同步转写函数，避免阻塞事件循环"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, transcribe_audio, file_path)

@app.post("/internal/asr")
async def asr_endpoint(file: UploadFile):
    # 只允许 WAV 文件
    if file.content_type != "audio/wav":
        return JSONResponse(
            {"success": False, "error": {"message": "Only WAV files allowed"}},
            status_code=400
        )

    data = await file.read()

    # 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(data)
        tmp_file_path = tmp.name

    try:
        result = await transcribe_audio_async(tmp_file_path)
    finally:
        os.remove(tmp_file_path)  # 确保删除临时文件

    return JSONResponse(result)
