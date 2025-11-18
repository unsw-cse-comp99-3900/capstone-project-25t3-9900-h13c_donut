# backend/app/services/diarization_matcher.py
"""
Diarization Matcher Service

核心功能：
1. 将 GPT 格式化的句子与 Whisper 时间戳对齐
2. 使用 Diarization 为每个句子分配说话人（基于时间重叠）
3. 保持 GPT 的分句，不被 diarization 的碎片化影响
"""

from typing import List, Dict, Optional
import re
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """
    归一化文本用于匹配（去除标点、大小写、多余空格）
    """
    # 转小写
    text = text.lower()
    # 移除标点
    text = re.sub(r'[^\w\s]', '', text)
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def text_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（0.0 - 1.0）
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    if not norm1 or not norm2:
        return 0.0
    
    return SequenceMatcher(None, norm1, norm2).ratio()


def align_sentences_with_whisper(
    gpt_sentences: List[Dict],  # [{"text": "...", "speaker": "A"}]
    whisper_segments: List[Dict]  # [{"start": 0.0, "end": 2.5, "text": "..."}]
) -> List[Dict]:
    """
    将 GPT 格式化的句子与 Whisper 的时间戳对齐
    
    策略：
    1. 按顺序匹配 GPT 句子和 Whisper segments
    2. 使用文本相似度找到最佳匹配
    3. 每个 GPT 句子可能跨越多个 Whisper segments
    
    返回：[{"start": 0.0, "end": 2.5, "text": "...", "gpt_speaker": "A"}]
    """
    if not gpt_sentences or not whisper_segments:
        return []
    
    aligned = []
    whisper_idx = 0
    
    for gpt_sent in gpt_sentences:
        gpt_text = gpt_sent.get("text", "")
        gpt_speaker = gpt_sent.get("speaker", "UNKNOWN")
        
        if not gpt_text.strip():
            continue
        
        # 收集可能匹配的 Whisper segments
        matched_segments = []
        best_start_idx = whisper_idx
        accumulated_text = ""
        
        # 向前查找匹配的 segments
        for i in range(whisper_idx, len(whisper_segments)):
            seg = whisper_segments[i]
            seg_text = seg.get("text", "")
            accumulated_text += " " + seg_text
            
            similarity = text_similarity(gpt_text, accumulated_text)
            
            # 如果相似度很高，或者已经覆盖了足够的内容
            if similarity > 0.7 or len(normalize_text(accumulated_text)) >= len(normalize_text(gpt_text)):
                matched_segments.append(seg)
                whisper_idx = i + 1
                break
            elif similarity > 0.3:  # 部分匹配，继续累积
                matched_segments.append(seg)
        
        # 如果没有找到好的匹配，使用当前 segment
        if not matched_segments and whisper_idx < len(whisper_segments):
            matched_segments = [whisper_segments[whisper_idx]]
            whisper_idx += 1
        
        # 计算时间范围
        if matched_segments:
            start_time = matched_segments[0].get("start", 0.0)
            end_time = matched_segments[-1].get("end", start_time + 2.0)
        else:
            # Fallback: 估算时间（每个字符 0.1 秒）
            if aligned:
                start_time = aligned[-1]["end"]
            else:
                start_time = 0.0
            duration = len(gpt_text) * 0.1
            end_time = start_time + duration
        
        aligned.append({
            "start": start_time,
            "end": end_time,
            "text": gpt_text,
            "gpt_speaker": gpt_speaker
        })
    
    return aligned


def assign_speakers_to_sentences(
    sentences: List[Dict],  # [{"start": 0.0, "end": 2.5, "text": "...", "gpt_speaker": "A"}]
    diar_segments: List[Dict]  # [{"start": 0.0, "end": 1.5, "speaker_id": "SPEAKER_00"}]
) -> List[Dict]:
    """
    为每个 GPT 句子分配说话人（基于与 diarization segments 的时间重叠）
    
    算法：
    1. 对每个句子，找到所有时间重叠的 diarization segments
    2. 计算每个说话人的总重叠时长
    3. 选择重叠时长最大的说话人
    
    返回：[{"start": 0.0, "end": 2.5, "text": "...", "speaker_id": "SPEAKER_00"}]
    """
    labeled = []
    
    for i, sent in enumerate(sentences):
        sent_start = sent.get("start", 0.0)
        sent_end = sent.get("end", sent_start + 1.0)
        sent_text = sent.get("text", "")
        gpt_speaker = sent.get("gpt_speaker", "UNKNOWN")
        
        # 收集所有重叠的 diarization segments
        overlaps = {}  # {speaker_id: total_overlap_duration}
        
        for diar in diar_segments:
            diar_start = diar.get("start", 0.0)
            diar_end = diar.get("end", diar_start)
            diar_speaker = diar.get("speaker_id", "SPEAKER_00")
            
            # 检查时间重叠
            if diar_start < sent_end and diar_end > sent_start:
                # 计算重叠时长
                overlap_start = max(sent_start, diar_start)
                overlap_end = min(sent_end, diar_end)
                overlap_dur = max(0, overlap_end - overlap_start)
                
                # 累加该说话人的重叠时长
                overlaps[diar_speaker] = overlaps.get(diar_speaker, 0.0) + overlap_dur
        
        # 选择重叠时长最大的说话人
        if overlaps:
            best_speaker = max(overlaps, key=overlaps.get)
            total_overlap = sum(overlaps.values())
            confidence = overlaps[best_speaker] / total_overlap if total_overlap > 0 else 0.0
            
            # 如果重叠太小（< 0.1 秒），使用 fallback
            if total_overlap < 0.1:
                print(f"[diar_matcher] Warning: Very small overlap ({total_overlap:.2f}s) for sentence: '{sent_text[:30]}...'")
                best_speaker = labeled[-1]["speaker_id"] if labeled else "SPEAKER_00"
                confidence = 0.0
        else:
            # Fallback 策略
            if labeled:
                # 使用上一句的说话人
                best_speaker = labeled[-1]["speaker_id"]
                print(f"[diar_matcher] No overlap, using previous speaker {best_speaker} for: '{sent_text[:30]}...'")
            else:
                # 使用默认说话人
                best_speaker = "SPEAKER_00"
                print(f"[diar_matcher] No overlap, using default SPEAKER_00 for: '{sent_text[:30]}...'")
            confidence = 0.0
        
        labeled.append({
            "start": sent_start,
            "end": sent_end,
            "text": sent_text,
            "speaker_id": best_speaker,
            "gpt_speaker": gpt_speaker,  # 保留 GPT 的识别结果作为参考
            "confidence": confidence
        })
    
    return labeled


def merge_consecutive_same_speaker(
    sentences: List[Dict]
) -> List[Dict]:
    """
    可选：合并连续的相同说话人句子（用于 UI 展示）
    
    注意：这会改变句子数量，可能影响其他逻辑，建议谨慎使用
    """
    if not sentences:
        return []
    
    merged = []
    current = sentences[0].copy()
    
    for sent in sentences[1:]:
        if sent["speaker_id"] == current["speaker_id"]:
            # 同一说话人，合并
            current["text"] += " " + sent["text"]
            current["end"] = sent["end"]
        else:
            # 不同说话人，保存当前并开始新的
            merged.append(current)
            current = sent.copy()
    
    # 添加最后一个
    merged.append(current)
    
    return merged


def analyze_speaker_changes(sentences: List[Dict]) -> Dict:
    """
    分析说话人切换情况（用于调试和质量评估）
    """
    if not sentences:
        return {
            "total_sentences": 0,
            "speaker_changes": 0,
            "speakers": []
        }
    
    speakers = set()
    changes = 0
    
    for i, sent in enumerate(sentences):
        speaker = sent.get("speaker_id", "UNKNOWN")
        speakers.add(speaker)
        
        if i > 0 and sent.get("speaker_id") != sentences[i-1].get("speaker_id"):
            changes += 1
    
    return {
        "total_sentences": len(sentences),
        "speaker_changes": changes,
        "speakers": sorted(list(speakers)),
        "avg_sentences_per_turn": len(sentences) / (changes + 1) if changes >= 0 else 0
    }

