"""
ASR 服务抽象接口

为不同的 ASR 供应商（OpenAI Whisper API / 本地 Whisper / 其他）提供统一接口。
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class WordTimestamp:
    """词级别时间戳"""
    word: str
    start_sec: float  # 相对时间（秒），从音频开始算起
    end_sec: float
    
    @property
    def start_ms(self) -> int:
        """转换为毫秒"""
        return int(self.start_sec * 1000)
    
    @property
    def end_ms(self) -> int:
        return int(self.end_sec * 1000)


@dataclass
class TranscriptSegment:
    """
    转录片段（sentence/segment 级别）
    
    注意：这里的时间戳是相对时间（从音频开始），不是 Unix 时间戳
    """
    text: str
    start_sec: float  # 相对时间（秒）
    end_sec: float
    words: Optional[List[WordTimestamp]] = None  # 可选的词级别时间戳
    
    @property
    def start_ms(self) -> int:
        """转换为毫秒"""
        return int(self.start_sec * 1000)
    
    @property
    def end_ms(self) -> int:
        return int(self.end_sec * 1000)
    
    def __repr__(self):
        return f"TranscriptSegment(text='{self.text[:30]}...', start={self.start_sec:.2f}s, end={self.end_sec:.2f}s)"


@dataclass
class TranscriptionResult:
    """完整的转录结果"""
    full_text: str  # 完整文本（用于 TTS）
    segments: List[TranscriptSegment]  # 分段文本（用于显示和说话人匹配）
    language: Optional[str] = None  # 检测到的语言
    duration_sec: Optional[float] = None  # 音频总时长


class ASRService(ABC):
    """ASR 服务抽象基类"""
    
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptionResult:
        """
        转录音频文件
        
        参数：
        - audio_path: WAV 文件路径（16kHz 单声道）
        - language: 可选的语言提示（如 "en", "zh"）
        - word_timestamps: 是否返回词级别时间戳
        
        返回：
        - TranscriptionResult: 包含完整文本和分段信息
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """服务名称（如 "OpenAI Whisper API", "Local Whisper"）"""
        pass



