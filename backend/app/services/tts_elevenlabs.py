import httpx
import asyncio
from typing import AsyncGenerator
from app.core.pubsub import channel
from app.config import settings  # ✅ 统一使用 config.py 配置

def _pick_voice_id_by_accent(accent: str) -> str:
    """
    根据口音选择对应的 Voice ID
    
    配置优先级：
    1. .env 文件中的 VOICE_ID_AMERICAN 等
    2. config.py 中的硬编码默认值
    """
    a = (accent or "").lower()
    if "australia" in a: 
        return settings.voice_id_australia
    if "british" in a: 
        return settings.voice_id_british
    if "chinese" in a: 
        return settings.voice_id_chinese
    if "india" in a: 
        return settings.voice_id_india
    # 默认美式英语
    return settings.voice_id_american

async def _stream_elevenlabs(
    text: str, 
    voice_id: str,
    stability: float = 0.88,
    similarity_boost: float = 0.73,
    style: float = 0.73,
    use_speaker_boost: bool = True
) -> AsyncGenerator[bytes, None]:
    """
    调用 ElevenLabs API 进行流式 TTS
    
    参数：
    - text: 要合成的文本
    - voice_id: ElevenLabs 声音 ID
    - stability: 稳定性 (0-1)，越高越稳定，越低越富有表现力
    - similarity_boost: 相似度增强 (0-1)，与原始声音的相似度
    - style: 风格夸张度 (0-1)，语音的表现力
    - use_speaker_boost: 是否启用说话者增强
    
    配置来源：app.config.settings
    - eleven_api_base: API 基础 URL
    - eleven_api_key: API 密钥
    """
    if not text or not text.strip():
        print("[tts] skip empty text")
        return
    if not settings.eleven_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is missing")

    url = f"{settings.eleven_api_base}/text-to-speech/{voice_id}/stream?optimize_streaming_latency=4"
    headers = {
        "xi-api-key": settings.eleven_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",  # ⚡ Turbo 模型：更低延迟
        "output_format": "mp3_44100_64",  # 🔧 64kbps：平衡音质和速度
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        },
    }

    print(f"[tts] HTTP POST {url} voice={voice_id}, stability={stability}, similarity={similarity_boost}, style={style}")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                if chunk:
                    yield chunk
                await asyncio.sleep(0)

async def _synth_and_stream_common(conv_id: str, text: str, accent: str):
    voice_id = _pick_voice_id_by_accent(accent)
    # 1) 通知前端开始
    await channel.pub_tts_json(conv_id, {"type": "start", "mime": "audio/mpeg"})
    print(f"[tts→ws] start -> {conv_id}")

    try:
        # 2) 流式分片（使用优化后的声音参数）
        got_any = False
        async for chunk in _stream_elevenlabs(
            text=text,
            voice_id=voice_id,
            stability=0.88,
            similarity_boost=0.73,
            style=0.73,
            use_speaker_boost=True
        ):
            got_any = True
            await channel.pub_tts_bytes(conv_id, chunk)
        print(f"[tts] stream done, got_any={got_any}")
    finally:
        # 3) 通知前端结束
        await channel.pub_tts_json(conv_id, {"type": "stop"})
        print(f"[tts→ws] stop  -> {conv_id}")


# ================================ MeloTTS 本地模型相关 =====================================
# 全局模型实例（懒加载，避免重复加载模型）
_melotts_model_cache = {}  # 按语言缓存: {'EN': model, 'ZH': model}
_melotts_executor = None

def _get_melotts_executor():
    """获取线程池执行器"""
    global _melotts_executor
    if _melotts_executor is None:
        from concurrent.futures import ThreadPoolExecutor
        _melotts_executor = ThreadPoolExecutor(max_workers=2)
    return _melotts_executor

def _get_melotts_model(language: str):
    """
    获取或初始化 MeloTTS 模型（带缓存）
    
    Args:
        language: 语言代码 'EN' 或 'ZH'
    
    Returns:
        tuple: (model, speaker_ids)
    """
    import os
    import sys
    
    # 检查缓存
    if language in _melotts_model_cache:
        model = _melotts_model_cache[language]
        speaker_ids = model.hps.data.spk2id
        # 确保返回字典类型
        if not isinstance(speaker_ids, dict):
            speaker_ids = dict(speaker_ids)
        return model, speaker_ids
    
    # 设置离线模式（避免自动下载）
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    
    # 添加 MeloTTS 路径到 sys.path
    services_dir = os.path.dirname(os.path.abspath(__file__))
    melo_dir = os.path.join(services_dir, 'melo')
    
    if os.path.exists(melo_dir) and services_dir not in sys.path:
        sys.path.insert(0, services_dir)
    
    # 导入 MeloTTS
    try:
        from melo.api import TTS
    except ImportError as e:
        raise ImportError(
            f"无法导入 MeloTTS: {e}\n"
            "请确保 melo/ 目录位于 app/services/melo/"
        )
    
    # 确定模型文件路径
    app_dir = os.path.dirname(services_dir)
    models_dir = os.path.join(app_dir, 'models', 'tts_models')
    lang_dir = os.path.join(models_dir, language)
    local_ckpt = os.path.join(lang_dir, 'checkpoint.pth')
    local_config = os.path.join(lang_dir, 'config.json')
    
    # 设备选择（自动选择 GPU/CPU）
    device = 'auto'
    
    # 加载模型
    if os.path.exists(local_ckpt) and os.path.exists(local_config):
        print(f"[melotts] 加载本地模型: {language}")
        print(f"  - checkpoint: {local_ckpt}")
        print(f"  - config: {local_config}")
        model = TTS(
            language=language,
            device=device,
            use_hf=False,  # 使用本地文件
            config_path=local_config,
            ckpt_path=local_ckpt
        )
    else:
        raise FileNotFoundError(
            f"找不到 {language} 模型文件:\n"
            f"  - {local_ckpt}\n"
            f"  - {local_config}\n"
            f"请确保模型文件已复制到 app/models/tts_models/{language}/"
        )
    
    # 缓存模型
    _melotts_model_cache[language] = model
    speaker_ids = model.hps.data.spk2id
    
    # 确保返回字典类型
    if not isinstance(speaker_ids, dict):
        speaker_ids = dict(speaker_ids)
    
    print(f"[melotts] 模型加载成功: {language}, 可用说话者: {list(speaker_ids.keys())}")
    return model, speaker_ids

def _accent_to_speaker_id(accent: str, speaker_ids, language: str) -> int:
    """
    将口音字符串映射到 speaker_id
    
    Args:
        accent: 口音类型（如 "australia", "british", "india", "american"）
        speaker_ids: 模型的 speaker_ids（可能是字典或 HParams 对象）
        language: 语言代码
    
    Returns:
        int: speaker_id
    """
    # 确保 speaker_ids 是字典
    if not isinstance(speaker_ids, dict):
        speaker_ids = dict(speaker_ids)
    
    a = (accent or "").lower()
    
    if language == 'ZH':
        # 中文模型只有一个说话者
        return speaker_ids.get('ZH', list(speaker_ids.values())[0])
    
    # 英文模型有多个口音
    # 注意：模型使用连字符 (EN-INDIA)，不是下划线 (EN_INDIA)
    if "australia" in a or "au" in a:
        return speaker_ids.get('EN-AU', speaker_ids.get('EN-Default', list(speaker_ids.values())[0]))
    elif "british" in a or "br" in a or "uk" in a:
        return speaker_ids.get('EN-BR', speaker_ids.get('EN-Default', list(speaker_ids.values())[0]))
    elif "india" in a or "indian" in a:
        # 修复：使用连字符 EN-INDIA 而不是下划线 EN_INDIA
        return speaker_ids.get('EN-INDIA', speaker_ids.get('EN-Default', list(speaker_ids.values())[0]))
    elif "american" in a or "us" in a:
        return speaker_ids.get('EN-US', speaker_ids.get('EN-Default', list(speaker_ids.values())[0]))
    else:
        # 默认使用 EN-Default 或第一个可用的
        return speaker_ids.get('EN-Default', list(speaker_ids.values())[0])

async def _synth_and_stream_local(conv_id: str, text: str, accent: str):
    """
    本地部署的 MeloTTS 模型版本
    输入输出与 _synth_and_stream_common 完全相同
    
    Args:
        conv_id: 会话 ID
        text: 要合成的文本
        accent: 口音类型（australia/british/india/american/chinese）
    """
    print(f"[DEBUG][melotts] ========== TTS 开始 ==========")
    print(f"[DEBUG][melotts] conv_id: {conv_id}")
    print(f"[DEBUG][melotts] text: '{text}'")
    print(f"[DEBUG][melotts] accent: {accent}")
    print(f"[DEBUG][melotts] text length: {len(text) if text else 0}")
    
    import io
    import numpy as np
    
    # 检查空文本
    if not text or not text.strip():
        print("[melotts] 跳过空文本")
        return
    
    try:
        import soundfile as sf
        print("[DEBUG][melotts] soundfile 导入成功")
    except ImportError as e:
        print(f"[DEBUG][melotts] soundfile 导入失败: {e}")
        raise ImportError("需要安装 soundfile: pip install soundfile")
    
    # 根据口音确定语言模型
    accent_lower = (accent or "").lower()
    if "chinese" in accent_lower or "china" in accent_lower:
        language = 'ZH'
    else:
        language = 'EN'  # 美式、英式、澳洲、印度都使用 EN 模型
    
    print(f"[DEBUG][melotts] 选择语言模型: {language}")
    
    # 1) 通知前端开始
    print(f"[DEBUG][melotts] 准备发送 start 消息到 channel")
    await channel.pub_tts_json(conv_id, {"type": "start", "mime": "audio/mpeg"})
    print(f"[DEBUG][melotts→ws] start 消息已发送 -> {conv_id}")
    
    try:
        # 2) 获取模型（使用缓存）
        print(f"[DEBUG][melotts] 开始加载模型...")
        model, speaker_ids = _get_melotts_model(language)
        print(f"[DEBUG][melotts] 模型加载成功，speaker_ids: {speaker_ids}")
        
        speaker_id = _accent_to_speaker_id(accent, speaker_ids, language)
        print(f"[DEBUG][melotts] 选择的 speaker_id: {speaker_id}")
        
        print(f"[melotts] 合成语音: text='{text[:50]}...', accent={accent}, speaker_id={speaker_id}, language={language}")
        
        # 3) 在线程池中生成音频（避免阻塞事件循环）
        print(f"[DEBUG][melotts] 准备在线程池中合成音频...")
        executor = _get_melotts_executor()
        loop = asyncio.get_event_loop()
        
        def synthesize():
            """在线程池中执行的同步合成函数"""
            print(f"[DEBUG][melotts] 线程池：开始调用 model.tts_to_file")
            audio = model.tts_to_file(
                text=text,
                speaker_id=speaker_id,
                output_path=None,  # 返回 numpy 数组而不是保存文件
                speed=1.0,
                quiet=True  # 不显示进度条
            )
            sample_rate = model.hps.data.sampling_rate
            print(f"[DEBUG][melotts] 线程池：音频合成完成，sample_rate={sample_rate}")
            return audio, sample_rate
        
        audio, sample_rate = await loop.run_in_executor(executor, synthesize)
        print(f"[DEBUG][melotts] 音频数据接收完成，shape={audio.shape if hasattr(audio, 'shape') else 'N/A'}")
        
        # 4) 转换为 MP3 字节（使用 pydub + ffmpeg）
        print(f"[DEBUG][melotts] 开始转换为 MP3 字节...")
        audio = np.clip(audio, -1.0, 1.0)
        
        try:
            from pydub import AudioSegment
            
            # 转换为 16-bit PCM
            audio_int16 = (audio * 32767.0).astype(np.int16)
            
            # 创建 AudioSegment
            audio_segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,  # 16-bit = 2 bytes
                channels=1
            )
            
            # 导出为 MP3
            mp3_buffer = io.BytesIO()
            audio_segment.export(mp3_buffer, format="mp3", bitrate="128k")
            mp3_buffer.seek(0)
            audio_bytes = mp3_buffer.read()
            print(f"[DEBUG][melotts] MP3 转换完成，总大小: {len(audio_bytes)} bytes")
        except ImportError:
            # 如果 pydub 不可用，退化到 WAV
            print(f"[DEBUG][melotts] pydub 不可用，退化到 WAV 格式...")
            audio = audio.astype(np.float32)
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, audio, sample_rate, format='WAV', subtype='PCM_16')
            wav_buffer.seek(0)
            audio_bytes = wav_buffer.read()
            print(f"[DEBUG][melotts] WAV 转换完成，总大小: {len(audio_bytes)} bytes")
        
        # 5) 分块发送音频数据
        chunk_size = 8192
        got_any = False
        chunk_count = 0
        
        print(f"[DEBUG][melotts] 开始分块发送音频数据，chunk_size={chunk_size}")
        for offset in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[offset:offset + chunk_size]
            if chunk:
                got_any = True
                chunk_count += 1
                await channel.pub_tts_bytes(conv_id, chunk)
                if chunk_count <= 3 or chunk_count % 10 == 0:  # 只打印前几个和每10个
                    print(f"[DEBUG][melotts] 已发送 chunk #{chunk_count}, size={len(chunk)}")
            await asyncio.sleep(0)  # 让出控制权
        
        print(f"[DEBUG][melotts] 音频数据发送完成！")
        print(f"[melotts] stream done, got_any={got_any}, total_chunks={chunk_count}, total_size={len(audio_bytes)} bytes")
        
    except Exception as e:
        print(f"[DEBUG][melotts] ❌ 发生错误: {e}")
        print(f"[DEBUG][melotts] 错误类型: {type(e).__name__}")
        import traceback
        print(f"[DEBUG][melotts] 完整堆栈跟踪:")
        traceback.print_exc()
        raise
    finally:
        # 6) 通知前端结束
        print(f"[DEBUG][melotts] 准备发送 stop 消息")
        await channel.pub_tts_json(conv_id, {"type": "stop"})
        print(f"[DEBUG][melotts→ws] stop 消息已发送 -> {conv_id}")
        print(f"[DEBUG][melotts] ========== TTS 结束 ==========")

# =====================================================================


async def synth_and_stream_free(conv_id: str, text: str, accent: str):
    await _synth_and_stream_local(conv_id, text, accent)

async def synth_and_stream_paid(conv_id: str, text: str, accent: str):
    await _synth_and_stream_common(conv_id, text, accent)
