"""
OpenAI Whisper API 适配器

适配现有的 OpenAI Whisper API 调用到新的 ASR 接口
"""
import httpx
from typing import Optional
from .asr_base import ASRService, TranscriptionResult, TranscriptSegment, WordTimestamp
from ..config import settings


class OpenAIWhisperService(ASRService):
    """OpenAI Whisper API 服务"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.api_url = settings.whisper_api_url
        self.model = settings.whisper_model
    
    @property
    def name(self) -> str:
        return "OpenAI Whisper API"
    
    def is_available(self) -> bool:
        """检查 API key 是否配置"""
        return bool(self.api_key)
    
    async def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptionResult:
        """
        调用 OpenAI Whisper API 进行转录
        
        使用 verbose_json 格式，返回 segment 级别时间戳
        
        注意：不使用 timestamp_granularities 参数，因为它会导致 segments 被合并，
        影响与 diarization 的匹配准确度
        """
        if not self.is_available():
            raise RuntimeError(f"{self.name}: API key not configured")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # 构建请求参数（✅ 优化准确度）
        data = {
            "model": self.model,
            "response_format": "verbose_json",
            # ✅ 高精度参数
            "temperature": 0.0,  # 0 = 最确定性（最准确，无随机性）
            "prompt": "Hello, hi, hey, good morning, how are you, I'm fine, thank you, and you, see you, bye.",  # ✅ 常见对话短语示例，帮助 Whisper 理解上下文
        }
        
        if language:
            data["language"] = language
        
        # ❌ 不使用 timestamp_granularities，因为它会合并 segments，导致与 diarization 匹配失败
        # if word_timestamps:
        #     data["timestamp_granularities"] = ["word", "segment"]
        
        # 发送请求
        async with httpx.AsyncClient(timeout=120) as client:
            with open(audio_path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                resp = await client.post(self.api_url, headers=headers, data=data, files=files)
            resp.raise_for_status()
            result = resp.json()
        
        # 解析结果
        full_text = (result.get("text") or "").strip()
        language_detected = result.get("language")
        duration = result.get("duration")
        
        # 解析分段信息
        segments = []
        raw_segments = result.get("segments", [])
        
        if not raw_segments and full_text:
            # 如果没有分段信息，创建一个单一分段
            segments.append(TranscriptSegment(
                text=full_text,
                start_sec=0.0,
                end_sec=duration or 0.0,
                words=None
            ))
        else:
            for seg in raw_segments:
                seg_text = seg.get("text", "").strip()
                seg_start = seg.get("start", 0.0)
                seg_end = seg.get("end", 0.0)
                
                # 解析词级别时间戳（如果有）
                words = None
                if word_timestamps and "words" in seg:
                    words = [
                        WordTimestamp(
                            word=w.get("word", ""),
                            start_sec=w.get("start", 0.0),
                            end_sec=w.get("end", 0.0)
                        )
                        for w in seg.get("words", [])
                    ]
                
                segments.append(TranscriptSegment(
                    text=seg_text,
                    start_sec=seg_start,
                    end_sec=seg_end,
                    words=words
                ))
        
        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=language_detected,
            duration_sec=duration
        )


# 全局单例（可选）
openai_whisper_service = OpenAIWhisperService()



