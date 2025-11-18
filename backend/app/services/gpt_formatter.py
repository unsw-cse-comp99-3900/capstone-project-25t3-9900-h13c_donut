"""
GPT 文本整理服务

使用 OpenAI GPT API 对转录文本进行：
1. 分句（按说话意图分割）
2. 标点符号修正
3. 语法优化
4. 去除重复和无意义的语气词
"""
import httpx
import json
from typing import List, Dict
from ..config import settings


class GPTFormatterService:
    """GPT 文本格式化服务"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.gpt_model
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def is_available(self) -> bool:
        """检查 API key 是否配置"""
        return bool(self.api_key) and settings.enable_gpt_formatting
    
    async def format_conversation(self, raw_text: str, language: str = "en") -> List[Dict]:
        """
        使用 GPT 整理对话文本
        
        参数:
            raw_text: 原始转录文本
            language: 语言代码 (en, zh, etc.)
        
        返回:
            [
                {"text": "句子1", "speaker": "A"},
                {"text": "句子2", "speaker": "B"},
                ...
            ]
        """
        if not self.is_available():
            # 如果 GPT 不可用，返回简单分句
            return self._simple_split(raw_text)
        
        try:
            # 构建 prompt
            system_prompt = self._build_system_prompt(language)
            user_prompt = f"""This is the COMPLETE raw transcript from ONE recording session. Format ONLY this text:

Raw transcript:
{raw_text}

(End of transcript - this is all the text from this recording)"""
            
            # 调用 GPT API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,  # 最低温度，完全确定性，避免幻觉
                "response_format": {"type": "json_object"}  # 要求返回 JSON
            }
            
            print(f"[GPT Formatter] Calling {self.model} to format conversation...")
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.api_url, headers=headers, json=payload)
                resp.raise_for_status()
                result = resp.json()
            
            # 解析结果
            content = result["choices"][0]["message"]["content"]
            formatted_data = json.loads(content)
            
            sentences = formatted_data.get("sentences", [])
            print(f"[GPT Formatter] ✅ Formatted into {len(sentences)} sentences")
            
            return sentences
            
        except Exception as e:
            print(f"[GPT Formatter] ❌ Error: {e}")
            # 出错时回退到简单分句
            return self._simple_split(raw_text)
    
    def _build_system_prompt(self, language: str) -> str:
        """构建 GPT system prompt"""

        return """You are a conversation formatter. Your ONLY job is to format the EXACT text provided below.

🚨 CRITICAL: You are formatting a SINGLE, ISOLATED conversation recording. 

⛔ FORBIDDEN ACTIONS:
❌ Do NOT add content from previous conversations
❌ Do NOT add content from your memory
❌ Do NOT invent or imagine sentences
❌ Do NOT add context or background
❌ Do NOT expand or elaborate
❌ Do NOT add information not in the raw transcript
❌ Do NOT merge content from different recordings
❌ Do NOT remove repeated phrases (e.g., "good morning, good morning" should stay as is)
❌ Do NOT simplify or paraphrase what was said
❌ Do NOT remove words just because they seem redundant

✅ REQUIRED ACTIONS:
1. Split the PROVIDED text into sentences based on natural pauses or punctuation
2. Add minimal punctuation for readability (periods, commas, question marks)
3. Remove ONLY meaningless fillers like "uh", "um", "er" that don't affect meaning
4. Assign speaker labels (A, B, C) based on turn-taking in THIS conversation
5. Preserve EVERY word that carries meaning FROM THE PROVIDED TEXT
6. Keep repeated phrases if they appear in the transcript (e.g., "good morning, good morning")
7. Keep all questions and responses exactly as spoken

Output format (JSON):
{
  "sentences": [
    {"text": "Hey, good morning, good morning.", "speaker": "A"},
    {"text": "How are you?", "speaker": "B"},
    {"text": "I'm fine, thank you. And you?", "speaker": "A"}
  ]
}

⚠️ REMEMBER: 
- Format ONLY what is in the raw transcript below
- If someone said "good morning" twice, keep it twice
- If a sentence seems incomplete, leave it incomplete
- Preserve the exact meaning and all meaningful words
- Do NOT add anything extra or remove meaningful content"""
    
    async def format_conversation_with_comparison(
        self,
        webspeech_text: str,
        whisper_text: str,
        language: str = "en"
    ) -> Dict:
        """
        比较并合并 Web Speech 和 Whisper 的文本，返回最佳转录
        
        返回:
        {
            "sentences": [
                {"text": "...", "speaker": "A"},
                ...
            ]
        }
        """
        if not self.is_available():
            # Fallback: 使用 Whisper 文本
            sentences = self._simple_split(whisper_text)
            return {
                "sentences": sentences
            }
        
        try:
            system_prompt = """You are a conversation formatter. You will receive TWO transcriptions of the same conversation:
1. Web Speech API transcription (real-time, may be more accurate for some words)
2. Whisper API transcription (offline, may be more accurate for other words)

Your task:
1. Compare both transcriptions word by word
2. For each sentence, choose the MORE ACCURATE words from either source
3. Merge them into the best possible transcription
4. Format into clear sentences with proper punctuation
5. Identify speakers (A, B, C)

Output format (JSON):
{
  "sentences": [
    {"text": "Hey, good morning, good morning.", "speaker": "A"},
    {"text": "How are you?", "speaker": "B"}
  ]
}

Rules:
- If Web Speech says "I'm fine" and Whisper says "I'm find", use "I'm fine" (Web Speech is correct)
- If Web Speech says "good morning" and Whisper says "good morning, good morning", keep "good morning, good morning" (if it was actually said twice)
- Preserve all meaningful words from BOTH sources
- Only remove meaningless fillers (uh, um)"""

            user_prompt = f"""Web Speech transcription:
{webspeech_text}

Whisper transcription:
{whisper_text}

Please compare both and create the best possible transcription by choosing the most accurate words from either source."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            
            print(f"[GPT Formatter] Calling {self.model} to compare and merge transcriptions...")
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(self.api_url, headers=headers, json=payload)
                resp.raise_for_status()
                result = resp.json()
            
            content = result["choices"][0]["message"]["content"]
            formatted_data = json.loads(content)
            
            sentences = formatted_data.get("sentences", [])
            
            print(f"[GPT Formatter] ✅ Merged into {len(sentences)} sentences")
            
            return {
                "sentences": sentences
            }
            
        except Exception as e:
            print(f"[GPT Formatter] ❌ Comparison error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: 使用 Whisper 文本
            sentences = self._simple_split(whisper_text)
            return {
                "sentences": sentences
            }
    
    def _simple_split(self, text: str) -> List[Dict]:
        """简单分句（fallback）"""
        import re
        
        # 按标点符号分句
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 简单分配说话人（交替）
        result = []
        for i, sent in enumerate(sentences):
            speaker = "A" if i % 2 == 0 else "B"
            result.append({"text": sent, "speaker": speaker})
        
        return result


# 全局单例
gpt_formatter = GPTFormatterService()

