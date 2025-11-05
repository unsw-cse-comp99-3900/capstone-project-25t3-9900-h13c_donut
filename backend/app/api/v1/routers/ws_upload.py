import json
import tempfile
import os
import asyncio
from typing import Dict, Optional, List
from io import BytesIO

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.pubsub import channel
from app.services.asr_openai import webm_to_wav_16k_mono
from app.services import transcribe_audio  # ✅ 使用新的 ASR 接口（支持本地 Whisper）
from app.services.tts_elevenlabs import synth_and_stream_free, synth_and_stream_paid

router = APIRouter()

# ✅ 改用内存缓冲（BytesIO）代替临时文件
_sessions: Dict[str, dict] = {}  # conv_id -> {"audio_buffer": BytesIO, "accent": str, "model": str, "start_seq": int}

@router.websocket("/ws/upload-audio")
async def ws_upload(ws: WebSocket):
    await ws.accept()
    print("[ws_upload] connected")
    conv_id: Optional[str] = None
    audio_buffer: Optional[BytesIO] = None
    
    try:
        # 1. 接收 start 消息
        start_msg = await ws.receive_text()
        meta = json.loads(start_msg)
        assert meta.get("type") == "start"
        conv_id = meta.get("conversationId")
        accent = meta.get("accent") or "American English"
        model = (meta.get("model") or "free").lower()
        print(f"[ws_upload] start conv_id={conv_id}, accent={accent}, model={model}")

        # ✅ 记录当前对话已有的 transcript 数量（用于rebuild时只处理当前这次录音）
        from app.models.transcript import Transcript
        start_seq = await Transcript.filter(conversation_id=conv_id).count()
        print(f"[ws_upload] current transcript count: {start_seq}")

        # ✅ 使用 BytesIO 在内存中缓冲音频
        audio_buffer = BytesIO()
        _sessions[conv_id] = {
            "audio_buffer": audio_buffer,
            "accent": accent,
            "model": model,
            "start_seq": start_seq  # 记录起始 seq，rebuild 时用
        }

        # 2. 循环接收音频分片
        while True:
            pkt = await ws.receive()
            
            # 2.1 接收二进制音频数据
            if "bytes" in pkt and pkt["bytes"]:
                # ✅ 写入内存（不阻塞，极快）
                audio_buffer.write(pkt["bytes"])
                continue
            
            # 2.2 接收文本控制消息
            if "text" in pkt and pkt["text"]:
                try:
                    j = json.loads(pkt["text"])
                except Exception:
                    continue
                
                # 2.3 收到 stop，进入对话结束流程
                if j.get("type") == "stop":
                    print(f"[ws_upload] stop conv_id={conv_id}")
                    
                    # ⚠️ 复制 audio_buffer 内容，避免两个函数互相干扰
                    audio_buffer.seek(0)
                    audio_data_copy = audio_buffer.read()
                    audio_buffer.seek(0)  # 重置指针供 on_stop_and_publish 使用
                    
                    # ✅ 路径1：实时反馈（ASR + TTS，保持原逻辑）
                    await on_stop_and_publish(conv_id, audio_buffer)
                    
                    # ✅ 路径2：离线分析（Diarization，异步执行，不阻塞）
                    # 创建新的 BytesIO 对象，避免与路径1冲突
                    diarization_buffer = BytesIO(audio_data_copy)
                    asyncio.create_task(
                        on_conversation_end_diarization(conv_id, diarization_buffer)
                    )
                    
                    try:
                        await ws.close()
                    except Exception:
                        pass
                    break
    except WebSocketDisconnect:
        print(f"[ws_upload] disconnect conv_id={conv_id or 'unknown'}")
    except Exception as e:
        print(f"[ws_upload] error: {repr(e)}")
    finally:
        # ✅ 清理内存（注意：diarization 可能还在异步执行，所以不立即关闭 buffer）
        # 实际清理会在 diarization 完成后执行
        print(f"[ws_upload] closed conv_id={conv_id or 'unknown'}")

async def on_stop_and_publish(conv_id: str, audio_buffer: BytesIO):
    """
    实时反馈：ASR + TTS（保持原逻辑）
    这个函数处理用户即时看到的结果
    """
    ses = _sessions.get(conv_id, {})
    accent = ses.get("accent", "American English")
    model = (ses.get("model") or "free").lower()

    print(f"[on_stop] begin conv_id={conv_id}, audio_size={audio_buffer.tell()} bytes")
    
    # 准备临时文件（用于 ffmpeg 转码）
    audio_buffer.seek(0)  # 回到开头
    webm_bytes = audio_buffer.read()
    
    if len(webm_bytes) == 0:
        print(f"[on_stop] No audio data for conv_id={conv_id}")
        return
    
    tmp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    tmp_webm.write(webm_bytes)
    tmp_webm.flush()
    tmp_webm.close()
    
    wav_path = None
    text = ""
    try:
        # ASR 转录（✅ 使用新接口，自动选择本地 Whisper 或 OpenAI API）
        wav_path = webm_to_wav_16k_mono(tmp_webm.name)
        asr_result = await transcribe_audio(
            wav_path,
            word_timestamps=False  # 实时 ASR 不需要词级别时间戳
        )
        text = asr_result.full_text
        print(f"[on_stop] ASR done, text_len={len(text)}, using {asr_result.language or 'auto'}")
    except Exception as e:
        text = f"[ASR error] {e}"
        print(f"[on_stop] ASR error: {e}")
    finally:
        # 清理临时文件
        try:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
        try:
            if os.path.exists(tmp_webm.name):
                os.remove(tmp_webm.name)
        except Exception:
            pass

    # 1) 推送 final 文本给前端
    try:
        await channel.pub_text(conv_id, {"type": "final", "text": text})
        print(f"[on_stop] pushed final text to conv_id={conv_id}")
    except Exception as e:
        print(f"[on_stop] failed to push text: {e}")

    # 2) TTS 合成并推送音频 - ❌ 已禁用（流式传译中已实时播放，无需重复）
    # try:
    #     print(f"[on_stop] TTS begin model={model}, accent={accent}")
    #     if model == "free":
    #         await synth_and_stream_free(conv_id, text, accent)
    #     else:
    #         await synth_and_stream_paid(conv_id, text, accent)
    #     print(f"[on_stop] TTS done")
    # except Exception as e:
    #     print(f"[on_stop] TTS error: {e}")
    
    print(f"[on_stop] Skipping TTS (streaming translation is active)")


async def on_conversation_end_diarization(conv_id: str, audio_buffer: BytesIO):
    """
    离线分析：Diarization + 重新拆分 Transcripts（异步执行，不阻塞用户）
    
    改进流程：
    1. 从内存读取完整音频
    2. 转码为 WAV
    3. 使用新 ASR 接口获取带时间戳的分段（等本地 Whisper 后效果更好）
    4. 执行 diarization 分析
    5. 合并 ASR 和 Diarization 结果
    6. 删除旧的 Transcripts，创建新的（按说话人拆分）
    7. 清理内存
    """
    ses = _sessions.get(conv_id, {})
    
    try:
        print(f"[rebuild] start for conv_id={conv_id}")
        
        # 1. 准备音频数据
        audio_buffer.seek(0)
        webm_bytes = audio_buffer.read()
        
        if len(webm_bytes) == 0:
            print(f"[rebuild] no audio data, skipping")
            return
        
        print(f"[rebuild] audio size: {len(webm_bytes)} bytes")
        
        # 2. 写入临时文件（用于 ffmpeg 转码）
        tmp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        tmp_webm.write(webm_bytes)
        tmp_webm.flush()
        tmp_webm.close()
        
        # 3. 转码为 WAV
        wav_path = webm_to_wav_16k_mono(tmp_webm.name)
        print(f"[rebuild] converted to WAV: {wav_path}")
        
        # 4. ✨ 使用新 ASR 接口获取带时间戳的分段
        from app.services import transcribe_audio
        from app.services.diarization import diarization_service
        from app.models.transcript import Transcript
        from app.models.conversation import Conversation
        
        try:
            asr_result = await transcribe_audio(
                wav_path,
                word_timestamps=True  # ✅ 启用词级别时间戳（本地 Whisper 支持）
            )
            duration_str = f"{asr_result.duration_sec:.2f}s" if asr_result.duration_sec else "unknown"
            print(f"[rebuild] ASR: {len(asr_result.segments)} segments, duration={duration_str}")
        except Exception as e:
            print(f"[rebuild] ASR failed: {e}, fallback to simple speaker assignment")
            # 如果新 ASR 失败，回退到旧逻辑
            diar_segments = await diarization_service.analyze_speakers(wav_path, num_speakers=None)
            if diar_segments:
                await assign_speakers_to_transcripts(conv_id, diar_segments)
            return
        
        # 5. 执行 diarization
        diar_segments = await diarization_service.analyze_speakers(
            wav_path,
            num_speakers=None
        )
        
        if not diar_segments:
            print(f"[rebuild] no diarization segments, keeping original transcripts")
            return
        
        print(f"[rebuild] Diarization: {len(diar_segments)} segments")
        
        # 6. ✨ 合并 ASR 和 Diarization 结果
        merged = merge_asr_and_diarization(asr_result.segments, diar_segments)
        print(f"[rebuild] Merged: {len(merged)} segments")
        
        if not merged:
            print(f"[rebuild] merge failed, using diarization only")
            # 回退：使用完整文本 + diarization 分段
            merged = fallback_merge_with_full_text(asr_result.full_text, diar_segments)
            if not merged:
                print(f"[rebuild] fallback also failed, keeping original transcripts")
                return
        
        # 7. ✨ 只删除当前这次录音的 Transcripts
        start_seq = ses.get("start_seq", 0)
        old_transcripts = await Transcript.filter(
            conversation_id=conv_id,
            seq__gt=start_seq  # 只删除 seq > start_seq 的（当前这次录音的）
        ).all()
        old_count = len(old_transcripts)
        print(f"[rebuild] Deleting {old_count} transcripts (seq > {start_seq})")
        await Transcript.filter(conversation_id=conv_id, seq__gt=start_seq).delete()
        
        # 8. ✨ 创建新的 Transcripts（按说话人拆分，从 start_seq+1 开始）
        conv = await Conversation.get(id=conv_id)
        conv_start_time = int(conv.started_at.timestamp() * 1000)  # Unix 毫秒
        
        # ⚠️ 注意：这里计算当前这段录音的时间偏移
        # 如果这是第二次录音，需要加上之前录音的总时长
        existing_transcripts = await Transcript.filter(conversation_id=conv_id).order_by("-end_ms").first()
        time_offset = 0
        if existing_transcripts and existing_transcripts.end_ms:
            # 计算相对于 conversation 开始的偏移量
            time_offset = existing_transcripts.end_ms - conv_start_time
            print(f"[rebuild] time_offset from previous recordings: {time_offset}ms")
        
        for i, seg in enumerate(merged, start=start_seq + 1):
            # 相对时间 + 偏移量 → 绝对时间
            absolute_start_ms = conv_start_time + time_offset + seg["start_ms"]
            absolute_end_ms = conv_start_time + time_offset + seg["end_ms"]
            
            await Transcript.create(
                conversation_id=conv_id,
                seq=i,
                is_final=True,
                start_ms=absolute_start_ms,
                end_ms=absolute_end_ms,
                text=seg["text"],
                audio_url=None,
                speaker_id=seg["speaker_id"]
            )
            print(f"[rebuild] Created transcript #{i}: {seg['speaker_id']}, {seg['text'][:50]}")
        
        print(f"[rebuild] ✅ Successfully rebuilt {len(merged)} transcripts (seq {start_seq+1} to {start_seq+len(merged)})")
        
        # 9. 清理临时文件
        try:
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
        try:
            if os.path.exists(tmp_webm.name):
                os.remove(tmp_webm.name)
        except Exception:
            pass
        
        print(f"[rebuild] completed for conv_id={conv_id}")
        
    except Exception as e:
        print(f"[rebuild] error for conv_id={conv_id}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 10. 清理内存和 session
        try:
            audio_buffer.close()
        except Exception:
            pass
        
        _sessions.pop(conv_id, None)
        print(f"[rebuild] cleaned up memory for conv_id={conv_id}")


def merge_asr_and_diarization(asr_segments: List, diar_segments: List[Dict]) -> List[Dict]:
    """
    ✨ 合并 ASR 和 Diarization 结果（改进版，避免文字丢失）
    
    策略：
    1. 遍历每个 diarization segment（说话人片段）
    2. 找到与之重叠的所有 ASR segments
    3. 合并这些 ASR segments 的文本，形成一个新的 transcript
    4. 对于重叠度低的 ASR segment，降低阈值或分配给最接近的说话人
    
    参数：
    - asr_segments: List[TranscriptSegment] from ASR service
    - diar_segments: [{"speaker_id": "SPEAKER_00", "start_ms": 0, "end_ms": 1000}, ...]
    
    返回：
    [
        {"speaker_id": "SPEAKER_00", "start_ms": 0, "end_ms": 2000, "text": "Hello world"},
        {"speaker_id": "SPEAKER_01", "start_ms": 2000, "end_ms": 5000, "text": "Hi there"},
        ...
    ]
    """
    if not asr_segments or not diar_segments:
        return []
    
    merged = []
    used_asr_indices = set()  # 记录已使用的 ASR segment
    
    # 策略：匹配重叠度高的 ASR segments
    # 使用 40% 阈值（平衡准确性和完整性）
    OVERLAP_THRESHOLD = 0.45  # 可以调整：0.3（宽松）到 0.6（严格）
    
    for diar_seg in diar_segments:
        diar_start = diar_seg["start_ms"]
        diar_end = diar_seg["end_ms"]
        speaker_id = diar_seg["speaker_id"]
        
        overlapping_texts = []
        
        for idx, asr_seg in enumerate(asr_segments):
            if idx in used_asr_indices:
                continue
                
            asr_start = asr_seg.start_ms
            asr_end = asr_seg.end_ms
            
            # 计算重叠度
            overlap_start = max(diar_start, asr_start)
            overlap_end = min(diar_end, asr_end)
            overlap = overlap_end - overlap_start
            
            asr_duration = asr_end - asr_start
            if asr_duration > 0 and overlap > 0:
                overlap_ratio = overlap / asr_duration
                
                # 主要匹配：重叠度 >= 40%
                if overlap_ratio >= OVERLAP_THRESHOLD:
                    overlapping_texts.append(asr_seg.text.strip())
                    used_asr_indices.add(idx)
                    print(f"[merge] Matched ASR seg (overlap={overlap_ratio:.1%}): {asr_seg.text[:30]}")
        
        if overlapping_texts:
            merged.append({
                "speaker_id": speaker_id,
                "start_ms": diar_start,
                "end_ms": diar_end,
                "text": " ".join(overlapping_texts).strip()
            })
    
    # 处理未匹配的 ASR segments
    unmatched_asr = [(idx, seg) for idx, seg in enumerate(asr_segments) if idx not in used_asr_indices]
    
    if unmatched_asr:
        print(f"[merge] Warning: {len(unmatched_asr)} ASR segments not matched (may lose some text)")
        # ⚠️ 不自动分配未匹配的文本，以保证说话人识别的准确性
        # 如果需要更高的文本完整性，可以调低 OVERLAP_THRESHOLD
        for idx, seg in unmatched_asr:
            print(f"[merge]   Unmatched: {seg.text[:50]}")
    
    # 按时间排序
    merged.sort(key=lambda x: x["start_ms"])
    
    return merged


def fallback_merge_with_full_text(full_text: str, diar_segments: List[Dict]) -> List[Dict]:
    """
    回退方案：使用完整文本 + diarization 时间段
    
    当 ASR segments 不可用或匹配失败时，将完整文本按 diarization 段落数量平均分配
    
    参数：
    - full_text: 完整转录文本
    - diar_segments: diarization 结果
    
    返回：
    - List[Dict]: merged segments
    """
    if not full_text.strip() or not diar_segments:
        return []
    
    # 简单策略：按字符数比例分配文本
    words = full_text.split()
    if not words:
        return []
    
    total_duration = sum(d["end_ms"] - d["start_ms"] for d in diar_segments)
    if total_duration == 0:
        return []
    
    merged = []
    word_idx = 0
    
    for diar_seg in diar_segments:
        seg_duration = diar_seg["end_ms"] - diar_seg["start_ms"]
        seg_word_count = max(1, int(len(words) * (seg_duration / total_duration)))
        
        seg_words = words[word_idx:word_idx + seg_word_count]
        word_idx += seg_word_count
        
        if seg_words:
            merged.append({
                "speaker_id": diar_seg["speaker_id"],
                "start_ms": diar_seg["start_ms"],
                "end_ms": diar_seg["end_ms"],
                "text": " ".join(seg_words)
            })
    
    # 如果有剩余的词，添加到最后一个 segment
    if word_idx < len(words) and merged:
        merged[-1]["text"] += " " + " ".join(words[word_idx:])
    
    print(f"[fallback_merge] Created {len(merged)} segments from full text")
    return merged


async def assign_speakers_to_transcripts(conv_id: str, diar_segments: List[Dict]):
    """
    将 diarization 结果分配给已有的 transcripts（旧方法，作为回退）
    
    策略（已修复时间戳不匹配问题）：
    1. 如果只有 1 个说话人 → 所有 transcripts 标记为同一个
    2. 如果有多个说话人 → 按序号轮流分配（简化版）
    
    参数：
    - conv_id: 会话 ID
    - diar_segments: [{"start_ms": 0, "end_ms": 3000, "speaker_id": "SPEAKER_00"}, ...]
    """
    from app.models.transcript import Transcript
    
    # 1. 获取该会话的所有 transcripts
    transcripts = await Transcript.filter(conversation_id=conv_id).order_by("seq")
    
    if not transcripts:
        print(f"[assign_speakers] no transcripts found for conv_id={conv_id}")
        return
    
    if not diar_segments:
        print(f"[assign_speakers] no diarization segments")
        return
    
    print(f"[assign_speakers] processing {len(transcripts)} transcripts")
    
    # 2. 提取所有不同的 speaker_id
    unique_speakers = sorted(set(seg["speaker_id"] for seg in diar_segments))
    print(f"[assign_speakers] detected {len(unique_speakers)} unique speakers: {unique_speakers}")
    
    # 3. 分配策略
    updated_count = 0
    
    if len(unique_speakers) == 1:
        # 策略 A：只有 1 个说话人 → 全部标记为同一个
        speaker_id = unique_speakers[0]
        for t in transcripts:
            t.speaker_id = speaker_id
            await t.save()
            updated_count += 1
        print(f"[assign_speakers] single speaker mode: all transcripts → {speaker_id}")
    
    else:
        # 策略 B：多个说话人 → 按 diarization 时间段匹配
        # 为每个 transcript 找出最接近的 speaker
        for t in transcripts:
            # 由于时间戳是 Unix 时间戳，无法直接匹配
            # 改用简化策略：按序号循环分配（假设轮流说话）
            speaker_index = (t.seq - 1) % len(unique_speakers)
            t.speaker_id = unique_speakers[speaker_index]
            await t.save()
            updated_count += 1
    
    print(f"[assign_speakers] updated {updated_count}/{len(transcripts)} transcripts")
