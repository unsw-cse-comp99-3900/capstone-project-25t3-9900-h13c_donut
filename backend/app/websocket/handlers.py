"""
WebSocket message handlers
Handles different types of WebSocket messages and coordinates with ASR/TTS services
"""

from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging
import base64
import uuid
from typing import Dict, Optional, List
from datetime import datetime
import tempfile
import os

from app.websocket.manager import WebSocketManager
from app.models.responses import (
    InitMessage, AudioMessage, StopMessage, ErrorMessage,
    PartialTranscriptMessage, FinalTranscriptMessage, 
    TTSChunkMessage, DoneMessage, HeartbeatResponse
)
from app.services.asr_service import ASRService
from app.services.tts_service import TTSService
from app.services.audio_processor import AudioProcessor
from app.config import settings

# 导入TTS模块
from tts.services.synthesis_service import create_synthesis_service
from tts.utils.exceptions import (
    TTSError, 
    ValidationError as TTSValidationError, 
    NetworkError, 
    AuthenticationError,
    RateLimitError,
    QuotaExceededError
)

logger = logging.getLogger(__name__)

class SessionState:
    """State for a WebSocket session"""
    
    def __init__(self, session_id: str, user_id: str, accent: str, model: str):
        self.session_id = session_id
        self.user_id = user_id
        self.accent = accent
        self.model = model
        self.created_at = datetime.utcnow()
        self.is_recording = False
        self.audio_buffer = []
        self.sequence_number = 0
        self.temp_audio_file: Optional[str] = None

class WebSocketHandler:
    """
    Handles WebSocket connections and message processing
    """
    
    def __init__(self, websocket_manager: WebSocketManager, tts_synthesis_service=None):
        self.websocket_manager = websocket_manager
        self.asr_service = ASRService()
        self.tts_service = TTSService()  # 保留原有的TTS服务作为备用
        self.audio_processor = AudioProcessor()
        
        # 使用真正的TTS模块
        self.tts_synthesis_service = tts_synthesis_service
        
        # Active sessions: websocket -> SessionState
        self.active_sessions: Dict[WebSocket, SessionState] = {}

    async def handle_connection(self, websocket: WebSocket, user: Dict, session_id: Optional[str] = None):
        """
        Handle a WebSocket connection and message loop
        
        Args:
            websocket: WebSocket connection
            user: User information from authentication
            session_id: Optional existing session ID
        """
        user_id = user["user_id"]
        
        # Register connection with manager
        success = await self.websocket_manager.connect(websocket, user_id, session_id)
        if not success:
            return
        
        try:
            # Message processing loop
            while True:
                # Receive message
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await self._send_error(websocket, "Invalid JSON format", "INVALID_JSON")
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
                
                # Process message based on type
                message_type = message.get("type")
                
                if message_type == "init":
                    await self._handle_init_message(websocket, message, user_id)
                elif message_type == "audio":
                    await self._handle_audio_message(websocket, message)
                elif message_type == "stop":
                    await self._handle_stop_message(websocket, message)
                elif message_type == "pong":
                    await self._handle_heartbeat_response(websocket)
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await self._send_error(websocket, f"Unknown message type: {message_type}", "UNKNOWN_MESSAGE_TYPE")
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client")
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            # Cleanup
            await self._cleanup_session(websocket)

    async def _handle_init_message(self, websocket: WebSocket, message: Dict, user_id: str):
        """
        Handle session initialization message
        
        Args:
            websocket: WebSocket connection
            message: Init message data
            user_id: User identifier
        """
        try:
            # Parse init message
            session_id = message.get("sessionId") or str(uuid.uuid4())
            accent = message.get("accent", "us")
            model = message.get("model", "free")
            
            # Validate accent and model
            if accent not in ["us", "uk", "au", "ca", "in"]:  # Add more accents as needed
                await self._send_error(websocket, f"Unsupported accent: {accent}", "INVALID_ACCENT")
                return
            
            if model not in ["free", "paid"]:
                await self._send_error(websocket, f"Invalid model: {model}", "INVALID_MODEL")
                return
            
            # Create session state
            session_state = SessionState(session_id, user_id, accent, model)
            self.active_sessions[websocket] = session_state
            
            # Create temporary audio file
            temp_fd, temp_path = tempfile.mkstemp(suffix=".wav", dir=settings.TEMP_AUDIO_DIR)
            os.close(temp_fd)
            session_state.temp_audio_file = temp_path
            
            logger.info(f"Session initialized: {session_id}, accent: {accent}, model: {model}")
            
            # Send success response
            await websocket.send_json({
                "type": "init_success",
                "sessionId": session_id,
                "accent": accent,
                "model": model,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling init message: {e}")
            await self._send_error(websocket, "Failed to initialize session", "INIT_ERROR")

    async def _handle_audio_message(self, websocket: WebSocket, message: Dict):
        """
        Handle audio data message
        
        Args:
            websocket: WebSocket connection
            message: Audio message data
        """
        try:
            if websocket not in self.active_sessions:
                await self._send_error(websocket, "Session not initialized", "NO_SESSION")
                return
            
            session_state = self.active_sessions[websocket]
            
            # Decode audio data
            audio_data_b64 = message.get("data")
            if not audio_data_b64:
                await self._send_error(websocket, "Missing audio data", "MISSING_AUDIO_DATA")
                return
            
            try:
                audio_bytes = base64.b64decode(audio_data_b64)
            except Exception as e:
                logger.error(f"Error decoding audio data: {e}")
                await self._send_error(websocket, "Invalid audio data encoding", "INVALID_AUDIO_DATA")
                return
            
            # Add to audio buffer
            session_state.audio_buffer.append(audio_bytes)
            session_state.is_recording = True
            
            # Optional: Send acknowledgment
            await websocket.send_json({
                "type": "audio_received",
                "sequence": message.get("sequence", 0),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.debug(f"Audio chunk received: {len(audio_bytes)} bytes")
            
        except Exception as e:
            logger.error(f"Error handling audio message: {e}")
            await self._send_error(websocket, "Failed to process audio", "AUDIO_ERROR")

    async def _handle_stop_message(self, websocket: WebSocket, message: Dict):
        """
        Handle stop recording message and trigger pseudo-streaming processing
        
        Args:
            websocket: WebSocket connection
            message: Stop message data
        """
        try:
            if websocket not in self.active_sessions:
                await self._send_error(websocket, "Session not initialized", "NO_SESSION")
                return
            
            session_state = self.active_sessions[websocket]
            
            if not session_state.is_recording or not session_state.audio_buffer:
                await self._send_error(websocket, "No audio data to process", "NO_AUDIO_DATA")
                return
            
            logger.info(f"Processing audio for session: {session_state.session_id}")
            
            # Process audio in background task to avoid blocking
            asyncio.create_task(self._process_audio_pseudo_streaming(websocket, session_state))
            
        except Exception as e:
            logger.error(f"Error handling stop message: {e}")
            await self._send_error(websocket, "Failed to stop recording", "STOP_ERROR")

    async def _process_audio_pseudo_streaming(self, websocket: WebSocket, session_state: SessionState):
        """
        Process audio with pseudo-streaming (batch processing with chunked delivery)
        
        Args:
            websocket: WebSocket connection
            session_state: Session state
        """
        try:
            # Combine all audio chunks
            combined_audio = b''.join(session_state.audio_buffer)
            
            # Save to temporary file as WebM (frontend sends WebM/Opus format)
            # Whisper API supports webm format directly, no need to convert
            webm_file = session_state.temp_audio_file.replace('.wav', '.webm')
            try:
                with open(webm_file, 'wb') as f:
                    f.write(combined_audio)
                session_state.temp_audio_file = webm_file
                logger.info(f"✅ Saved WebM audio: {webm_file}, size: {len(combined_audio)} bytes")
            except Exception as e:
                logger.error(f"Failed to save audio file: {e}")
                await self._send_error(websocket, "Failed to save audio file", "AUDIO_SAVE_ERROR")
                return
            
            # Step 1: Call ASR service (batch processing)
            logger.info("Starting ASR processing...")
            asr_result = await self.asr_service.transcribe_audio(
                session_state.temp_audio_file,
                model=session_state.model
            )
            
            if not asr_result or not asr_result.get("text"):
                await self._send_error(websocket, "ASR processing failed", "ASR_ERROR")
                return
            
            # Log the recognized text for debugging
            logger.info(f"🎤 ASR recognized: '{asr_result['text']}'")
            
            # Step 2: Send partial transcripts (simulate streaming)
            await self._send_partial_transcripts(websocket, asr_result, session_state)
            
            # Step 3: Send final transcript
            final_message = FinalTranscriptMessage(
                text=asr_result["text"],
                segments=asr_result.get("segments", []),
                confidence=asr_result.get("confidence")
            )
            await websocket.send_json(final_message.dict())
            
            # Step 4: Call TTS service using the real TTS module
            logger.info("Starting TTS processing...")
            
            try:
                # 使用真正的TTS模块进行流式合成
                if self.tts_synthesis_service:
                    await self._handle_tts_streaming(websocket, asr_result["text"], session_state)
                else:
                    # 降级到原有TTS服务
                    logger.warning("TTS synthesis service not available, using fallback")
                    tts_result = await self.tts_service.synthesize_speech(
                        asr_result["text"],
                        accent=session_state.accent,
                        model=session_state.model
                    )
                    
                    if not tts_result or not tts_result.get("audio_data"):
                        await self._send_error(websocket, "TTS processing failed", "TTS_ERROR")
                        return
                    
                    # Send TTS chunks (simulate streaming)
                    await self._send_tts_chunks(websocket, tts_result, session_state)
                    
                    # Send done message
                    done_message = DoneMessage(
                        sessionId=session_state.session_id,
                        totalDuration=tts_result.get("duration"),
                        audioUrl=tts_result.get("audio_url")
                    )
                    await websocket.send_json(done_message.dict())
                
            except TTSValidationError as e:
                logger.error(f"TTS validation error: {e}")
                await self._send_error(websocket, str(e), "VALIDATION_ERROR")
                return
            except AuthenticationError as e:
                logger.error(f"TTS authentication error: {e}")
                await self._send_error(websocket, "TTS服务认证失败，请联系管理员", "AUTH_ERROR")
                return
            except RateLimitError as e:
                logger.warning(f"TTS rate limit: {e}")
                retry_after = getattr(e, 'retry_after', 60)
                await self._send_error(websocket, f"请求过于频繁，请{retry_after}秒后重试", "RATE_LIMIT")
                return
            except QuotaExceededError as e:
                logger.error(f"TTS quota exceeded: {e}")
                await self._send_error(websocket, "TTS配额已用完，请联系管理员", "QUOTA_EXCEEDED")
                return
            except NetworkError as e:
                logger.error(f"TTS network error: {e}")
                await self._send_error(websocket, "TTS服务暂时不可用，请稍后重试", "NETWORK_ERROR")
                return
            except TTSError as e:
                logger.error(f"TTS error: {e}")
                await self._send_error(websocket, str(e), getattr(e, 'error_code', 'TTS_ERROR'))
                return
            
            logger.info(f"Audio processing completed for session: {session_state.session_id}")
            
        except Exception as e:
            logger.error(f"Error in pseudo-streaming processing: {e}")
            await self._send_error(websocket, "Audio processing failed", "PROCESSING_ERROR")

    async def _send_partial_transcripts(self, websocket: WebSocket, asr_result: Dict, session_state: SessionState):
        """
        Send partial transcripts by chunking the full transcript
        
        Args:
            websocket: WebSocket connection
            asr_result: ASR result with segments
            session_state: Session state
        """
        segments = asr_result.get("segments", [])
        
        if not segments:
            # If no segments, split text by sentences
            text = asr_result["text"]
            sentences = text.split('. ')
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    partial_message = PartialTranscriptMessage(
                        text=sentence.strip() + ('.' if i < len(sentences) - 1 else ''),
                        sequence=i
                    )
                    await websocket.send_json(partial_message.dict())
                    await asyncio.sleep(0.1)  # Small delay to simulate streaming
        else:
            # Use actual segments from ASR
            for i, segment in enumerate(segments):
                partial_message = PartialTranscriptMessage(
                    text=segment.get("text", ""),
                    sequence=i,
                    startMs=int(segment.get("start", 0) * 1000),
                    endMs=int(segment.get("end", 0) * 1000)
                )
                await websocket.send_json(partial_message.dict())
                await asyncio.sleep(0.1)  # Small delay to simulate streaming

    async def _send_tts_chunks(self, websocket: WebSocket, tts_result: Dict, session_state: SessionState):
        """
        Send TTS audio in chunks to simulate streaming
        
        Args:
            websocket: WebSocket connection
            tts_result: TTS result with audio data
            session_state: Session state
        """
        audio_data = tts_result["audio_data"]
        chunk_size = settings.AUDIO_CHUNK_SIZE_BYTES
        
        # Split audio into chunks
        chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            
            chunk_message = TTSChunkMessage(
                bytes_b64=chunk_b64,
                seq=i,
                size=len(chunk),
                isLast=(i == len(chunks) - 1)
            )
            
            await websocket.send_json(chunk_message.dict())
            await asyncio.sleep(0.05)  # Small delay to simulate streaming

    async def _handle_heartbeat_response(self, websocket: WebSocket):
        """
        Handle heartbeat response (pong)
        
        Args:
            websocket: WebSocket connection
        """
        await self.websocket_manager.update_heartbeat(websocket)

    async def _send_error(self, websocket: WebSocket, error: str, code: str):
        """
        Send error message to WebSocket
        
        Args:
            websocket: WebSocket connection
            error: Error message
            code: Error code
        """
        try:
            error_message = ErrorMessage(error=error, code=code)
            await websocket.send_json(error_message.dict())
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def _handle_tts_streaming(self, websocket: WebSocket, text: str, session_state: SessionState):
        """
        使用TTS模块进行真正的流式合成
        
        Args:
            websocket: WebSocket连接
            text: 要合成的文本
            session_state: 会话状态
        """
        try:
            # 根据会话模式选择语音ID
            voice_mapping = {
                "us": "EXAVITQu4vr4xnSDxMaL",    # Sarah - 美国口音
                "uk": "Xb7hH8MSUJpSbSDYk0k2",    # Alice - 英国口音  
                "au": "IKne3meq5aSn9XLyUdCD",    # Charlie - 澳洲口音
                "ca": "EXAVITQu4vr4xnSDxMaL",    # 默认使用美国口音
                "in": "EXAVITQu4vr4xnSDxMaL"     # 默认使用美国口音
            }
            
            voice_id = voice_mapping.get(session_state.accent, "EXAVITQu4vr4xnSDxMaL")
            
            # 验证输入
            if not text or not text.strip():
                await self._send_error(websocket, "文本内容不能为空", "EMPTY_TEXT")
                return
            
            logger.info(f"Starting TTS streaming: text_length={len(text)}, voice_id={voice_id}")
            
            # 调用TTS模块的流式API
            chunk_count = 0
            async for chunk in self.tts_synthesis_service.synthesize_chunked_base64(
                text=text,
                voice_id=voice_id,
                chunk_bytes=settings.TTS_CHUNK_SIZE_BYTES,
                mime="audio/mpeg"
            ):
                chunk_count += 1
                # 检查WebSocket是否仍然连接
                from starlette.websockets import WebSocketState
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.warning("WebSocket已断开，停止发送TTS分块")
                    break
                
                # 直接转发给前端
                await websocket.send_json(chunk)
                
                # 日志记录（改为INFO级别以便调试）
                logger.info(
                    f"✅ 发送TTS分块: seq={chunk['seq']}, "
                    f"size={chunk['size']}, "
                    f"isLast={chunk['isLast']}"
                )
            
            # 发送完成消息
            done_message = DoneMessage(
                sessionId=session_state.session_id,
                totalDuration=None,  # TTS模块暂时不提供时长信息
                audioUrl=None
            )
            await websocket.send_json(done_message.dict())
            
            logger.info(f"TTS流式合成完成: text_length={len(text)}, chunks_sent={chunk_count}")
            
        except Exception as e:
            logger.error(f"TTS streaming error: {e}", exc_info=True)
            await self._send_error(websocket, "TTS流式处理失败", "TTS_STREAMING_ERROR")
            raise

    async def _cleanup_session(self, websocket: WebSocket):
        """
        Cleanup session resources
        
        Args:
            websocket: WebSocket connection
        """
        try:
            if websocket in self.active_sessions:
                session_state = self.active_sessions[websocket]
                
                # Clean up temporary audio file
                if session_state.temp_audio_file and os.path.exists(session_state.temp_audio_file):
                    try:
                        os.remove(session_state.temp_audio_file)
                        logger.debug(f"Cleaned up temp file: {session_state.temp_audio_file}")
                    except Exception as e:
                        logger.error(f"Error cleaning up temp file: {e}")
                
                # Remove from active sessions
                del self.active_sessions[websocket]
                
                logger.info(f"Session cleaned up: {session_state.session_id}")
            
            # Disconnect from manager
            await self.websocket_manager.disconnect(websocket)
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")


