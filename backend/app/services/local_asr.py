"""
本地 Whisper 适配器

使用本地部署的 Whisper 模型进行 ASR
"""
import asyncio
from typing import Optional
from .asr_base import ASRService, TranscriptionResult, TranscriptSegment, WordTimestamp


class LocalWhisperService(ASRService):
    """本地 Whisper 服务（延迟加载）"""
    
    def __init__(self, model_name: str = "small", lazy_load: bool = True):
        """
        初始化本地 Whisper
        
        参数：
        - model_name: Whisper 模型名称 ("tiny", "base", "small", "medium", "large")
        - lazy_load: 是否延迟加载（默认 True，只有实际使用时才加载模型）
        """
        self.model = None
        self.model_name = model_name
        self._available = False
        self._lazy_load = lazy_load
        
        # 如果不延迟加载，立即加载模型
        if not lazy_load:
            self._load_model()
    
    def _load_model(self):
        """加载 Whisper 模型"""
        if self.model is not None:
            return  # 已经加载
        
        try:
            import whisper
            print(f"[Local Whisper] Loading {self.model_name} model...")
            self.model = whisper.load_model(self.model_name)
            self._available = True
            print(f"[Local Whisper] Model loaded successfully!")
        except ImportError:
            print("[Local Whisper] WARNING: 'whisper' package not installed. Run: pip install openai-whisper")
        except Exception as e:
            print(f"[Local Whisper] Failed to load model: {e}")
    
    @property
    def name(self) -> str:
        return f"Local Whisper ({self.model_name})"
    
    def is_available(self) -> bool:
        """检查本地 Whisper 是否可用"""
        return self._available and self.model is not None

    def _transcribe_sync(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptionResult:
        """同步转录（在线程池中运行）"""
        # ✅ 延迟加载：首次使用时加载模型
        if self._lazy_load and self.model is None:
            self._load_model()
        
        if not self.is_available():
            raise RuntimeError(f"{self.name}: Model not available")
        
        # 构建 Whisper 参数
        kwargs = {
            "verbose": False,
        }
        if language:
            kwargs["language"] = language
        
        # word_timestamps 是 whisper 的原生功能
        if word_timestamps:
            kwargs["word_timestamps"] = True
        
        # 执行转录
        result = self.model.transcribe(audio_path, **kwargs)
        
        # 解析结果
        full_text = (result.get("text") or "").strip()
        language_detected = result.get("language")
        
        # 解析 segments
        segments = []
        raw_segments = result.get("segments", [])
        
        if not raw_segments and full_text:
            # 如果没有分段，创建单一分段
            segments.append(TranscriptSegment(
                text=full_text,
                start_sec=0.0,
                end_sec=0.0,
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
        
        # 获取 duration，如果为 None 则从最后一个 segment 计算
        duration_sec = result.get("duration")
        if duration_sec is None and segments:
            duration_sec = max(seg.end_sec for seg in segments)
        
        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=language_detected,
            duration_sec=duration_sec
        )
    
    async def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptionResult:
        """
        异步转录音频文件
        
        注意：Whisper 模型推理是 CPU/GPU 密集型操作，
        所以在线程池中运行避免阻塞事件循环
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_path,
            language,
            word_timestamps
        )


# 全局单例（延迟加载模型）
def _get_model_name():
    """延迟导入 settings 以避免循环导入"""
    from ..config import settings
    return settings.local_whisper_model

# ✅ lazy_load=True（默认）: 只有在实际调用 transcribe() 时才加载模型
local_whisper_service = LocalWhisperService(model_name=_get_model_name(), lazy_load=True)
