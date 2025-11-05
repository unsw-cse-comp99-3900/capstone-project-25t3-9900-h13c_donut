# backend/app/services/diarization.py
"""
说话人识别服务（Speaker Diarization）
使用 pyannote.audio 预训练模型，无需自己训练
"""
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    说话人识别服务
    
    功能：
    - 自动识别音频中的不同说话人
    - 返回时间戳 + 说话人 ID
    - 支持 3 人场景（可配置）
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_DIARIZATION", "true").lower() == "true"
        self.model_name = os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1")
        self.pipeline = None
        
        if self.enabled:
            try:
                hf_token = os.getenv("HF_TOKEN")
                if not hf_token:
                    logger.warning(
                        "[Diarization] HF_TOKEN not set. "
                        "Get one from https://huggingface.co/settings/tokens"
                    )
                    self.enabled = False
                    return
                
                logger.info(f"[Diarization] Loading model: {self.model_name}")
                
                # 延迟导入（避免启动时必须安装 pyannote）
                from pyannote.audio import Pipeline
                
                # ✅ 新版 huggingface_hub 使用 token 参数（兼容旧版 use_auth_token）
                try:
                    # 优先尝试新 API (token)
                    self.pipeline = Pipeline.from_pretrained(
                        self.model_name,
                        token=hf_token
                    )
                except TypeError:
                    # 降级到旧 API (use_auth_token)
                    self.pipeline = Pipeline.from_pretrained(
                        self.model_name,
                        use_auth_token=hf_token
                    )
                
                logger.info("[Diarization] Model loaded successfully ✓")
                
            except ImportError as e:
                logger.error(
                    "[Diarization] pyannote.audio not installed. "
                    "Run: pip install pyannote.audio torch torchaudio"
                )
                self.enabled = False
            except Exception as e:
                logger.error(f"[Diarization] Failed to load model: {e}")
                self.enabled = False
        else:
            logger.info("[Diarization] Service disabled by config")
    
    async def analyze_speakers(
        self, 
        audio_path: str, 
        num_speakers: Optional[int] = None
    ) -> List[Dict]:
        """
        分析音频中的说话人
        
        参数：
        - audio_path: WAV 文件路径（16kHz 单声道）
        - num_speakers: 预期说话人数（None=自动检测，建议传 3）
        
        返回：
        [
            {"start_ms": 0, "end_ms": 3200, "speaker_id": "SPEAKER_00"},
            {"start_ms": 3200, "end_ms": 6100, "speaker_id": "SPEAKER_01"},
            ...
        ]
        """
        if not self.enabled or not self.pipeline:
            logger.warning("[Diarization] Service not available, returning empty segments")
            return []
        
        try:
            logger.info(
                f"[Diarization] Analyzing {audio_path}, "
                f"num_speakers={num_speakers if num_speakers else 'auto-detect'}"
            )
            
            # 执行 diarization（可能需要几秒到几十秒）
            diarization = self.pipeline(
                audio_path,
                num_speakers=num_speakers
            )
            
            # 转换为我们需要的格式
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start_ms": int(turn.start * 1000),  # 秒 → 毫秒
                    "end_ms": int(turn.end * 1000),
                    "speaker_id": speaker  # "SPEAKER_00", "SPEAKER_01", ...
                })
            
            # 统计说话人数量
            speaker_count = len(set(s["speaker_id"] for s in segments))
            logger.info(
                f"[Diarization] ✓ Detected {speaker_count} speakers, "
                f"{len(segments)} segments"
            )
            
            return segments
        
        except Exception as e:
            logger.error(f"[Diarization] Analysis failed: {e}", exc_info=True)
            return []
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.enabled and self.pipeline is not None


# 全局单例
diarization_service = DiarizationService()

