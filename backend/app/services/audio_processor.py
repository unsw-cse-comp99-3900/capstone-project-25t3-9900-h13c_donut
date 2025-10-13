"""
Audio processing utilities
"""

import logging
import numpy as np
from typing import Optional, List
import tempfile
import os

from app.config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Audio processing utilities for WebSocket audio handling
    """
    
    def __init__(self):
        self.sample_rate = 16000  # Standard sample rate for speech processing
        
    def combine_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """
        Combine multiple audio chunks into a single audio buffer
        
        Args:
            audio_chunks: List of audio byte chunks
            
        Returns:
            Combined audio data
        """
        try:
            return b''.join(audio_chunks)
        except Exception as e:
            logger.error(f"Error combining audio chunks: {e}")
            return b''
    
    def save_audio_to_file(self, audio_data: bytes, file_path: str, format: str = "wav") -> bool:
        """
        Save audio data to file
        
        Args:
            audio_data: Audio data bytes
            file_path: Output file path
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'wb') as f:
                if format.lower() == "wav":
                    # Write simple WAV header for raw PCM data
                    self._write_wav_header(f, len(audio_data), self.sample_rate)
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return False
    
    def _write_wav_header(self, file, data_length: int, sample_rate: int):
        """
        Write WAV file header
        
        Args:
            file: File object to write to
            data_length: Length of audio data
            sample_rate: Sample rate
        """
        # WAV header for 16-bit mono PCM
        file.write(b'RIFF')
        file.write((data_length + 36).to_bytes(4, 'little'))
        file.write(b'WAVE')
        file.write(b'fmt ')
        file.write((16).to_bytes(4, 'little'))  # PCM format chunk size
        file.write((1).to_bytes(2, 'little'))   # PCM format
        file.write((1).to_bytes(2, 'little'))   # Mono
        file.write(sample_rate.to_bytes(4, 'little'))
        file.write((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
        file.write((2).to_bytes(2, 'little'))   # Block align
        file.write((16).to_bytes(2, 'little'))  # Bits per sample
        file.write(b'data')
        file.write(data_length.to_bytes(4, 'little'))
    
    def validate_audio_data(self, audio_data: bytes) -> bool:
        """
        Validate audio data
        
        Args:
            audio_data: Audio data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not audio_data:
            return False
        
        # Basic validation - check if data length is reasonable
        max_size = settings.MAX_AUDIO_DURATION_SECONDS * self.sample_rate * 2  # 16-bit
        if len(audio_data) > max_size:
            logger.warning(f"Audio data too large: {len(audio_data)} bytes")
            return False
        
        return True
    
    def estimate_duration(self, audio_data: bytes, sample_rate: Optional[int] = None) -> float:
        """
        Estimate audio duration in seconds
        
        Args:
            audio_data: Audio data bytes
            sample_rate: Sample rate (defaults to self.sample_rate)
            
        Returns:
            Estimated duration in seconds
        """
        if not sample_rate:
            sample_rate = self.sample_rate
        
        # Assume 16-bit mono PCM
        num_samples = len(audio_data) // 2
        return num_samples / sample_rate


