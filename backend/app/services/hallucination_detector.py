# backend/app/services/hallucination_detector.py
"""
幻觉检测服务（用于 ASR 转录结果验证）

功能：
1. Whisper 置信度分析
2. 重复内容检测
3. 语义连贯性检查
"""
import re
from typing import List, Dict, Optional


class HallucinationDetector:
    """
    ASR 幻觉检测器
    
    使用多种策略检测和过滤 ASR 转录中的幻觉内容
    """
    
    def __init__(self):
        self.history_texts = []  # 保存最近的转录文本（用于连贯性检查）
        self.max_history = 5
    
    def detect_from_whisper(
        self, 
        text: str, 
        segments: List[Dict] = None
    ) -> Dict:
        """
        综合检测函数（集成所有检测策略）
        
        参数:
            text: 完整转录文本
            segments: Whisper 分段结果（包含时间戳和置信度）
                     格式: [{"text": "...", "start": 0.0, "end": 2.0, "avg_logprob": -0.3}, ...]
        
        返回:
            {
                "is_hallucination": bool,
                "reason": str,
                "confidence": float,
                "details": dict
            }
        """
        if not text or not text.strip():
            return {
                "is_hallucination": True,
                "reason": "empty_text",
                "confidence": 0.0,
                "details": {}
            }
        
        # 1. Whisper 置信度分析
        confidence_check = self._check_whisper_confidence(text, segments)
        if confidence_check["is_hallucination"]:
            return confidence_check
        
        # 2. 重复内容检测
        repetition_check = self._check_repetition(text)
        if repetition_check["is_hallucination"]:
            return repetition_check
        
        # 3. 语义连贯性检查
        coherence_check = self._check_semantic_coherence(text)
        if coherence_check["is_hallucination"]:
            return coherence_check
        
        # 4. 可疑模式检测
        pattern_check = self._check_suspicious_patterns(text)
        if pattern_check["is_hallucination"]:
            return pattern_check
        
        # 通过所有检查
        return {
            "is_hallucination": False,
            "reason": "valid",
            "confidence": confidence_check.get("confidence", 0.8),
            "details": {
                "text_length": len(text),
                "word_count": len(text.split())
            }
        }
    
    def _check_whisper_confidence(
        self, 
        text: str, 
        segments: List[Dict] = None
    ) -> Dict:
        """
        检测 1：Whisper 置信度分析
        
        检查项：
        1. 平均 log probability（对数概率）
        2. 低置信度片段的比例
        3. 语速异常（过快/过慢）
        """
        if not segments:
            # 没有分段信息，使用默认置信度
            return {
                "is_hallucination": False,
                "reason": "no_segments",
                "confidence": 0.7
            }
        
        # 提取置信度指标
        confidences = []
        durations = []
        
        for seg in segments:
            # avg_logprob: 接近 0 = 高置信度，接近 -1 或更低 = 低置信度
            # 支持字典和对象两种格式
            if isinstance(seg, dict):
                avg_logprob = seg.get('avg_logprob', seg.get('avg_log_prob', -0.5))
                start = seg.get('start', 0)
                end = seg.get('end', 0)
            else:
                # Whisper 对象格式
                avg_logprob = getattr(seg, 'avg_logprob', getattr(seg, 'avg_log_prob', -0.5))
                start = getattr(seg, 'start', 0)
                end = getattr(seg, 'end', 0)
            
            # 转换为 0-1 置信度分数
            # Whisper 的 avg_logprob 通常在 -1.0 到 0.0 之间
            confidence = max(0, min(1, (avg_logprob + 1.0)))
            confidences.append(confidence)
            
            # 计算时长
            duration = end - start
            if duration > 0:
                durations.append(duration)
        
        if not confidences:
            return {
                "is_hallucination": False,
                "reason": "no_confidence_data",
                "confidence": 0.7
            }
        
        # 1. 计算平均置信度
        avg_confidence = sum(confidences) / len(confidences)
        
        # 2. 计算低置信度比例
        low_confidence_count = sum(1 for c in confidences if c < 0.5)
        low_confidence_ratio = low_confidence_count / len(confidences)
        
        # 3. 检查语速（词/秒）
        if durations:
            total_duration = sum(durations)
            words = text.split()
            words_per_second = len(words) / max(total_duration, 0.1)
            
            # 正常语速：1.5-4.5 词/秒（英文）
            speed_abnormal = words_per_second < 0.5 or words_per_second > 6.0
        else:
            speed_abnormal = False
            words_per_second = 0
        
        # 判断是否为幻觉（✅ 放宽阈值以减少误判）
        if avg_confidence < 0.3:  # 从 0.4 降低到 0.3
            return {
                "is_hallucination": True,
                "reason": f"low_avg_confidence: {avg_confidence:.2f}",
                "confidence": avg_confidence,
                "details": {
                    "avg_confidence": avg_confidence,
                    "low_confidence_ratio": low_confidence_ratio
                }
            }
        
        if low_confidence_ratio > 0.7:  # 从 0.6 提高到 0.7
            return {
                "is_hallucination": True,
                "reason": f"high_low_confidence_ratio: {low_confidence_ratio:.2f}",
                "confidence": avg_confidence,
                "details": {
                    "low_confidence_ratio": low_confidence_ratio,
                    "low_segments": low_confidence_count
                }
            }
        
        if speed_abnormal:
            return {
                "is_hallucination": True,
                "reason": f"abnormal_speech_rate: {words_per_second:.2f} words/sec",
                "confidence": avg_confidence,
                "details": {
                    "words_per_second": words_per_second
                }
            }
        
        # 通过检查
        return {
            "is_hallucination": False,
            "reason": "valid_confidence",
            "confidence": avg_confidence,
            "details": {
                "avg_confidence": avg_confidence,
                "low_confidence_ratio": low_confidence_ratio
            }
        }
    
    def _check_repetition(self, text: str) -> Dict:
        """
        检测 2：重复内容检测
        
        检查项：
        1. 连续重复的单词
        2. 短语级别的重复
        3. 整句重复
        """
        words = text.lower().split()
        
        if len(words) < 2:
            return {"is_hallucination": False, "reason": "too_short", "confidence": 0.7}
        
        # 1. 检测连续重复的单词
        max_word_repeat = 0
        current_repeat = 1
        
        for i in range(1, len(words)):
            if words[i] == words[i-1]:
                current_repeat += 1
                max_word_repeat = max(max_word_repeat, current_repeat)
            else:
                current_repeat = 1
        
        # 连续重复 4 次以上 → 幻觉（✅ 从 3 提高到 4 以减少误判）
        if max_word_repeat >= 4:
            return {
                "is_hallucination": True,
                "reason": f"repeated_word: {max_word_repeat} times",
                "confidence": 0.3,
                "details": {"max_repeat": max_word_repeat}
            }
        
        # 2. 检测短语重复（2-5 个词的组合）
        for phrase_len in [2, 3, 4, 5]:
            if len(words) < phrase_len * 2:
                continue
            
            for i in range(len(words) - phrase_len * 2 + 1):
                phrase = ' '.join(words[i:i+phrase_len])
                rest_text = ' '.join(words[i+phrase_len:])
                
                # 检查短语是否在后面重复出现
                if phrase in rest_text:
                    # 计算重复次数
                    repeat_count = text.lower().count(phrase)
                    if repeat_count >= 3:
                        return {
                            "is_hallucination": True,
                            "reason": f"repeated_phrase: '{phrase}' ({repeat_count} times)",
                            "confidence": 0.4,
                            "details": {
                                "phrase": phrase,
                                "repeat_count": repeat_count
                            }
                        }
        
        # 3. 检测句子级别重复（通过标点分割）
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().lower() for s in sentences if s.strip()]
        
        if len(sentences) >= 2:
            seen = set()
            for sent in sentences:
                if sent in seen and len(sent) > 10:  # 至少 10 个字符
                    return {
                        "is_hallucination": True,
                        "reason": f"repeated_sentence: '{sent[:30]}...'",
                        "confidence": 0.4,
                        "details": {"sentence": sent}
                    }
                seen.add(sent)
        
        # 通过检查
        return {
            "is_hallucination": False,
            "reason": "no_repetition",
            "confidence": 0.8
        }
    
    def _check_semantic_coherence(self, text: str) -> Dict:
        """
        检测 3：语义连贯性检查
        
        检查项：
        1. 与历史文本的主题相关性（关键词重叠）
        2. 突然的主题转换
        3. 跨文本的重复
        """
        if not self.history_texts:
            # 第一次转录，无历史记录
            self.history_texts.append(text)
            return {
                "is_hallucination": False,
                "reason": "no_history",
                "confidence": 0.7
            }
        
        # 提取关键词（简化版：去除停用词）
        def extract_keywords(t: str) -> set:
            # 英文停用词
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'this',
                'that', 'these', 'those', 'have', 'has', 'had', 'do', 'does', 'did'
            }
            words = re.findall(r'\w+', t.lower())
            return set(w for w in words if w not in stopwords and len(w) > 2)
        
        current_keywords = extract_keywords(text)
        
        # 计算与最近几次转录的关键词重叠度
        recent_texts = self.history_texts[-3:]  # 只看最近 3 次
        overlaps = []
        
        for hist_text in recent_texts:
            hist_keywords = extract_keywords(hist_text)
            if hist_keywords:
                overlap = len(current_keywords & hist_keywords)
                overlap_ratio = overlap / max(len(current_keywords), 1)
                overlaps.append(overlap_ratio)
        
        # 如果与所有历史文本的重叠度都很低 → 可能主题突变
        if overlaps:
            max_overlap = max(overlaps)
            
            # 只有在有足够历史（>= 2 次）且重叠度极低时才报警
            if len(self.history_texts) >= 2 and max_overlap < 0.05:
                return {
                    "is_hallucination": True,
                    "reason": f"topic_shift: overlap={max_overlap:.2%}",
                    "confidence": 0.5,
                    "details": {
                        "overlap_ratio": max_overlap,
                        "current_keywords": list(current_keywords)[:10]
                    }
                }
        
        # 检测跨文本重复（同一句话在不同转录中出现）
        normalized_text = text.lower().strip()
        for hist_text in recent_texts:
            if normalized_text == hist_text.lower().strip() and len(normalized_text) > 20:
                return {
                    "is_hallucination": True,
                    "reason": "duplicate_across_transcripts",
                    "confidence": 0.4,
                    "details": {"text": normalized_text[:50]}
                }
        
        # 通过检查，更新历史
        self.history_texts.append(text)
        if len(self.history_texts) > self.max_history:
            self.history_texts.pop(0)
        
        return {
            "is_hallucination": False,
            "reason": "coherent",
            "confidence": 0.8,
            "details": {
                "overlap_ratio": max(overlaps) if overlaps else 0
            }
        }
    
    def _check_suspicious_patterns(self, text: str) -> Dict:
        """
        检测 4：可疑文本模式
        
        检查项：
        1. 纯标点
        2. 重复字符模式
        3. 异常长度
        """
        # 1. 纯标点或空白
        if re.match(r'^[\s\.\,\!\?\;\:]+$', text):
            return {
                "is_hallucination": True,
                "reason": "only_punctuation",
                "confidence": 0.0
            }
        
        # 2. 重复字符模式（如 "aaaaaaa"）
        if re.search(r'(.)\1{6,}', text):
            return {
                "is_hallucination": True,
                "reason": "repeated_characters",
                "confidence": 0.2
            }
        
        # 3. 过短（< 3 字符）
        if len(text.strip()) < 3:
            return {
                "is_hallucination": True,
                "reason": "text_too_short",
                "confidence": 0.3
            }
        
        # 4. 过多特殊字符（> 30%）
        special_char_count = len(re.findall(r'[^\w\s]', text))
        char_count = len(text.replace(' ', ''))
        if char_count > 0:
            special_ratio = special_char_count / char_count
            if special_ratio > 0.3:
                return {
                    "is_hallucination": True,
                    "reason": f"too_many_special_chars: {special_ratio:.1%}",
                    "confidence": 0.4,
                    "details": {"special_ratio": special_ratio}
                }
        
        # 通过检查
        return {
            "is_hallucination": False,
            "reason": "normal_pattern",
            "confidence": 0.8
        }
    
    def reset_history(self):
        """重置历史记录（新会话开始时调用）"""
        self.history_texts.clear()


# 全局单例
hallucination_detector = HallucinationDetector()

