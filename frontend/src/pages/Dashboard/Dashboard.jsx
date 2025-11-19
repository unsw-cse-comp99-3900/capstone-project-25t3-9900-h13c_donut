import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Dashboard.module.css";

import { verifyUpgradeKey } from "../../api/dashboard";
import {
  listConversations,
  createConversation,
  loadConversation,
  renameConversation,
  appendSegment,
  deleteConversation,
} from "../../api/conversations";
import { createStreamClient } from "../../api/streamClient";
import { changePassword } from "../../api/auth";

/** ===== Constants ===== */
const ACCENTS = [
  "American English",
  "Australia English",
  "British English",
  "Chinese English",
  "India English",
];
const USE_LOCAL_SPEECH = (import.meta.env.VITE_USE_LOCAL_SPEECH || "0") === "1";

// ✅ 说话人颜色映射
const SPEAKER_COLORS = {
  "SPEAKER_00": "#FF6B6B",  // 红色
  "SPEAKER_01": "#4ECDC4",  // 青色
  "SPEAKER_02": "#FFD93D",  // 黄色
};

const SPEAKER_NAMES = {
  "SPEAKER_00": "Speaker 1",
  "SPEAKER_01": "Speaker 2",
  "SPEAKER_02": "Speaker 3",
};

/** Simple eye icon */
function EyeIcon({ open = false }) {
  return open ? (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z" fill="none" stroke="currentColor" strokeWidth="1.8"/>
      <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8"/>
    </svg>
  ) : (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 3l18 18" fill="none" stroke="currentColor" strokeWidth="1.8"/>
      <path d="M10.58 10.58a3 3 0 104.24 4.24M9.88 5.09A10.7 10.7 0 0112 5c7 0 11 7 11 7a17.2 17.2 0 01-3.11 3.88M6.11 7.11A17.2 17.2 0 001 12s4 7 11 7a10.7 10.7 0 003.04-.43" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

/** Generate default title for new conversations */
function generateDefaultTitle() {
  const ts = new Date();
  return `New Chat ${ts.toLocaleDateString()}/${ts.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })}`;
}

/** Title helper */
function titleFrom(text) {
  if (!text) {
    return generateDefaultTitle();
  }
  const first = (text.split(/(?<=[.!?])\s+/)[0] || text).slice(0, 60);
  const cleaned = first
    .replace(/\s+/g, " ")
    .replace(/[^\p{L}\p{N}\s'',-]/gu, "")
    .trim();
  if (!cleaned) return generateDefaultTitle();
  const titleCased = cleaned.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1));
  return titleCased;
}

export default function Dashboard() {
  const navigate = useNavigate();

  /** ===== user session ===== */
  const userId =
    localStorage.getItem("authUserId") || sessionStorage.getItem("authUserId");
  const username =
    localStorage.getItem("authUsername") ||
    sessionStorage.getItem("authUsername") ||
    "User";

  useEffect(() => {
    if (!userId) navigate("/login", { replace: true });
  }, [userId, navigate]);

  const ACTIVE_KEY = `activeId:${userId || "anon"}`;
  const PAID_UNLOCK_KEY = `paidUnlocked:${userId || "anon"}`;

  /** ===== settings menu ===== */
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  useEffect(() => {
    const onDocClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  /** ===== model / accent ===== */
  const [modelUnlocked, setModelUnlocked] = useState(() => {
    return localStorage.getItem(PAID_UNLOCK_KEY) === "1";
  });
  const [selectedModel, setSelectedModel] = useState(() => {
    return localStorage.getItem(PAID_UNLOCK_KEY) === "1" ? "paid" : "free";
  });
  const [selectedAccent, setSelectedAccent] = useState(ACCENTS[0]);

  useEffect(() => {
    if (!modelUnlocked && selectedModel === "paid") {
      setSelectedModel("free");
    }
  }, [modelUnlocked, selectedModel]);

  /** ===== conversations ===== */
  const [convos, setConvos] = useState([]);
  const [activeId, setActiveId] = useState(() => localStorage.getItem(ACTIVE_KEY));
  const activeConv = convos.find((c) => c.id === activeId) || null;

  useEffect(() => {
    if (!userId) return;
    (async () => {
      const list = await listConversations();
      if (list.length) {
        setConvos(list);
        const stored = localStorage.getItem(ACTIVE_KEY);
        const pick = stored && list.some((c) => c.id === stored) ? stored : list[0].id;
        setActiveId(pick);
        localStorage.setItem(ACTIVE_KEY, pick);
      } else {
        const c = await createConversation({ title: generateDefaultTitle() });
        setConvos([c]);
        setActiveId(c.id);
        localStorage.setItem(ACTIVE_KEY, c.id);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
  }, [activeId, ACTIVE_KEY]);

  // 防止 New 被连点导致重复
  const creatingRef = useRef(false);
  const handleNewConversation = async () => {
    if (creatingRef.current) return;
    creatingRef.current = true;
    try {
      const c = await createConversation({ title: generateDefaultTitle() });
      setConvos((prev) => (prev.some((x) => x.id === c.id) ? prev : [c, ...prev]));
      setActiveId(c.id);
      localStorage.setItem(ACTIVE_KEY, c.id);
    } finally {
      creatingRef.current = false;
    }
  };

  const activateConversation = async (id) => {
    if (id === activeId) return;
    setActiveId(id);
    const data = await loadConversation(id);
    if (data) setConvos((prev) => prev.map((c) => (c.id === id ? data : c)));
  };

  /** ===== dots + rename/delete ===== */
  const [hoverId, setHoverId] = useState(null);
  const [dotMenuFor, setDotMenuFor] = useState(null);
  const dotMenuRef = useRef(null);
  useEffect(() => {
    const onDocClick = (e) => {
      if (dotMenuRef.current && !dotMenuRef.current.contains(e.target)) setDotMenuFor(null);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [renameId, setRenameId] = useState(null);
  const openRename = (conv) => {
    setRenameId(conv.id);
    setRenameValue(conv.title || "");
    setRenameOpen(true);
    setDotMenuFor(null);
  };
  const commitRename = async () => {
    if (!renameId) return;
    const newTitle = renameValue || generateDefaultTitle();
    await renameConversation(renameId, newTitle);
    setConvos((prev) =>
      prev.map((c) => (c.id === renameId ? { ...c, title: newTitle } : c))
    );
    setRenameOpen(false);
    setRenameId(null);
  };
  const doDelete = async (id) => {
    await deleteConversation(id);
    setConvos((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) {
      const next = await listConversations();
      if (next.length) {
        setActiveId(next[0].id);
        localStorage.setItem(ACTIVE_KEY, next[0].id);
      } else {
        const c = await createConversation({ title: generateDefaultTitle() });
        setConvos([c]);
        setActiveId(c.id);
        localStorage.setItem(ACTIVE_KEY, c.id);
      }
    }
    setDotMenuFor(null);
  };

  /** ===== transcript / stream ===== */
  const [recording, setRecording] = useState(false);
  const [volumeOpen, setVolumeOpen] = useState(false);
  const [volume, setVolume] = useState(1);
  const transcriptBoxRef = useRef(null);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [interimText, setInterimText] = useState("");
  
  const [previewText, setPreviewText] = useState("");  // ✅ Web Speech API 预览文本
  const streamingTranslation = true;  // ✅ 流式传译默认开启（去掉开关）
  const currentSegIdRef = useRef(null);
  const currentConvIdRef = useRef(null);   // 当前段落对应的会话 ID（用于收尾）
  const segAudioUrlRef = useRef(null);
  const streamRef = useRef(null);
  const finishOnceRef = useRef(false);     // 保证每段只 finish 一次
  const speechRecognitionRef = useRef(null);  // ✅ Web Speech Recognition 实例
  const ttsQueueRef = useRef([]);  // ✅ TTS 音频播放队列
  const ttsPlayingRef = useRef(false);  // ✅ TTS 是否正在播放
  const ttsDebounceTimerRef = useRef(null);  // ✅ TTS 防抖计时器
  const lastSpokenTextRef = useRef('');  // ✅ 上一次已播放的文本（用于增量检测）
  const lastTtsTimeRef = useRef(0);  // ✅ 上次 TTS 触发时间（用于频率限制）

  const startSegment = async () => {
    if (!activeConv) return null;
    const segId = "s_" + Date.now();
    currentSegIdRef.current = segId;
    segAudioUrlRef.current = null;
    finishOnceRef.current = false;

    setConvos((prev) =>
      prev.map((c) =>
        c.id !== activeConv.id
          ? c
          : {
              ...c,
              segments: [
                ...(c.segments || []),
                { id: segId, start: Date.now(), end: null, transcript: "", audioUrl: null },
              ],
            }
      )
    );
    setLiveTranscript("");
    setInterimText("");
    setTimeout(() => {
      if (transcriptBoxRef.current)
        transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
    }, 0);
    return segId;
  };

  // —— 关键修复：允许把“最终文本”直接传进来，避免状态时序导致空白
  const finishSegment = async (finalText) => {
    if (finishOnceRef.current) return;
    finishOnceRef.current = true;

    const segId = currentSegIdRef.current;
    const convId = currentConvIdRef.current || activeId;
    if (!segId || !convId) return;

    const textToSave =
      (typeof finalText === "string" && finalText.length > 0)
        ? finalText
        : (liveTranscript || "");

    if (finalText && finalText !== liveTranscript) {
      setLiveTranscript(finalText);
    }

    // ✨ 先更新本地状态，确保 segment 被正确添加到 activeConv
    setConvos((prev) => {
      return prev.map((c) => {
        if (c.id !== convId) return c;
        // 检查 segment 是否已存在
        const existingSeg = (c.segments || []).find((s) => s.id === segId);
        const segs = existingSeg
          ? (c.segments || []).map((s) =>
              s.id === segId
                ? { ...s, end: Date.now(), transcript: textToSave, audioUrl: segAudioUrlRef.current }
                : s
            )
          : [
              ...(c.segments || []),
              {
                id: segId,
                start: Date.now() - 1,
                end: Date.now(),
                transcript: textToSave,
                audioUrl: segAudioUrlRef.current,
              },
            ];
        const next = { ...c, segments: segs };
        if ((c.segments?.length || 0) >= 1 && c.title?.startsWith("New Chat") && textToSave) {
          next.title = titleFrom(textToSave) || c.title;
        }
        return next;
      });
    });

    try {
      await appendSegment(convId, {
        id: segId,
        start: Date.now() - 1,
        end: Date.now(),
        transcript: textToSave,
        audioUrl: segAudioUrlRef.current,
      });
    } catch {}

    // ✨ 延迟清空 liveTranscript，确保 UI 已经更新显示 segment
    setTimeout(() => {
      setLiveTranscript("");
      setInterimText("");
    }, 100);
    currentSegIdRef.current = null;
    // 不清 currentConvIdRef，兜底还能读到
  };

  const micStart = async () => {
    // ✨ 自动创建新对话：
    // 1. 如果没有对话列表
    // 2. 没有活跃对话
    // 3. 当前活跃对话没有 segments（显示占位文本时）
    let convId = activeId;
    const hasNoSegments = activeConv && (!activeConv.segments || activeConv.segments.length === 0);
    
    if (convos.length === 0 || !activeConv || !activeId || hasNoSegments) {
      console.log(`[Dashboard] Auto-creating new conversation (convos.length=${convos.length}, activeConv=${!!activeConv}, activeId=${activeId}, hasNoSegments=${hasNoSegments})`);
      const c = await createConversation({ title: generateDefaultTitle() });
      // ✨ 同时更新 convos 和 activeId，确保 activeConv 能立即计算出来
      setConvos((prev) => (prev.some((x) => x.id === c.id) ? prev : [c, ...prev]));
      setActiveId(c.id);
      localStorage.setItem(ACTIVE_KEY, c.id);
      convId = c.id;
      console.log(`[Dashboard] ✅ Created new conversation: ${c.id}`);
    } else {
      console.log(`[Dashboard] Using existing conversation: ${convId}`);
    }
    currentConvIdRef.current = convId; // 记录本段的会话 ID
    await startSegment();

    streamRef.current = createStreamClient({
      conversationId: convId,
      model: selectedModel, // "free" | "paid"
      accent: selectedAccent,
      mode: USE_LOCAL_SPEECH ? "local" : "ws",
      onText: async (payload) => {
        if (typeof payload === "string") {
          setInterimText("");
          setLiveTranscript((prev) => (prev ? prev + payload : payload));
        } else if (payload.type === "transcripts_updated") {
          // ✨ 收到 GPT 格式化完成通知，自动刷新 Dashboard
          console.log(`[Dashboard] 📥 Received transcripts_updated, count=${payload.count}`);
          try {
            const data = await loadConversation(convId);
            if (data) {
              setConvos((prev) => prev.map((c) => (c.id === convId ? data : c)));
              console.log(`[Dashboard] ✅ Transcripts refreshed automatically`);
            }
          } catch (e) {
            console.error("[Dashboard] Failed to refresh transcripts:", e);
          }
        } else {
          const { interim, final } = payload;
          if (interim != null) setInterimText(interim);
          if (final) {
            setInterimText("");
            setLiveTranscript((prev) => (prev ? prev + final : final));
            // —— 收到最终文本后，直接携带 final 收尾，避免时序问题
            setTimeout(() => { finishSegment(final); }, 0);
          }
        }
        if (transcriptBoxRef.current) {
          transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
        }
      },
      onTtsStart: () => {
        segAudioUrlRef.current = null;
      },
      onTtsBlob: (blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        segAudioUrlRef.current = url;
      },
      onTtsEnded: () => {
        // 兜底：若未收尾，这里再收一次
        if (!finishOnceRef.current) {
          setTimeout(() => { finishSegment(); }, 0);
        }
      },
      outputVolume: volume,
    });

    await streamRef.current.open();
    await streamRef.current.startSegment();
    await streamRef.current.startMic?.();
    setRecording(true);
    
    // ✅ 启动 Web Speech API 实时预览
    startWebSpeechPreview();
  };

  const micStop = async () => {
    setRecording(false);
    
    // ✅ 停止 Web Speech API
    stopWebSpeechPreview();
    
    // ✨ 获取 Web Speech 文本并发送到后端
    const webspeechText = liveTranscript || "";
    
    try { 
      await streamRef.current?.stopMic?.(); 
    } catch {}
    
    try { 
      // ✨ 发送 Web Speech 文本到后端（用于 GPT 比较）
      await streamRef.current?.stopSegment?.(webspeechText);
    } catch {}
    
    // ✨ 使用 Web Speech 的文本完成当前 segment
    // Whisper 不再推送 final 文本，所以我们手动触发 finishSegment
    // 即使 webspeechText 为空，也要完成 segment（可能用户没有说话）
    setTimeout(() => {
      if (!finishOnceRef.current) {
        console.log(`[Dashboard] Finishing segment with Web Speech text (${webspeechText.length} chars)`);
        finishSegment(webspeechText || "");
      }
    }, 500);  // 延迟 500ms 确保 Web Speech 的最后结果已经累积
  };

  const onMicToggle = () => (recording ? micStop() : micStart());

  /** ===== 流式传译 TTS 请求 ===== */
  const requestStreamingTts = async (text) => {
    if (!text || !currentConvIdRef.current) return;
    
    try {
      console.log(`[Streaming TTS] Requesting for: "${text.substring(0, 50)}..."`);
      
      // 调用后端 TTS API（确保路径正确）
      const response = await fetch('http://localhost:8000/api/v1/tts/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          text: text,
          accent: selectedAccent,
          model: selectedModel,
        }),
      });
      
      if (!response.ok) {
        console.error('[Streaming TTS] Request failed:', response.status);
        return;
      }
      
      const audioBlob = await response.blob();
      console.log(`[Streaming TTS] Received audio: ${audioBlob.size} bytes`);
      
      // 加入播放队列
      enqueueTts(audioBlob);
      
    } catch (err) {
      console.error('[Streaming TTS] Error:', err);
    }
  };

  /** ===== TTS 音频队列播放 ===== */
  const playTtsAudio = async (audioBlob) => {
    return new Promise((resolve) => {
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.volume = volume;
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        resolve();
      };
      
      audio.onerror = () => {
        console.error('[TTS Queue] Audio playback error');
        URL.revokeObjectURL(audioUrl);
        resolve();
      };
      
      audio.play().catch((err) => {
        console.error('[TTS Queue] Play failed:', err);
        resolve();
      });
    });
  };
  
  const processTtsQueue = async () => {
    if (ttsPlayingRef.current) return;  // 已在播放
    if (ttsQueueRef.current.length === 0) return;  // 队列为空
    
    ttsPlayingRef.current = true;
    
    while (ttsQueueRef.current.length > 0) {
      const audioBlob = ttsQueueRef.current.shift();
      await playTtsAudio(audioBlob);
    }
    
    ttsPlayingRef.current = false;
  };
  
  const enqueueTts = (audioBlob) => {
    ttsQueueRef.current.push(audioBlob);
    processTtsQueue();  // 尝试开始播放
  };

  /** ===== Web Speech API 实时预览 ===== */
  const startWebSpeechPreview = () => {
    // 清除旧的防抖计时器
    if (ttsDebounceTimerRef.current) {
      clearTimeout(ttsDebounceTimerRef.current);
      ttsDebounceTimerRef.current = null;
    }
    // 重置已播放文本和触发时间（开始新的录音会话）
    lastSpokenTextRef.current = '';
    lastTtsTimeRef.current = 0;
    
    // 检查浏览器支持
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[Web Speech] Not supported in this browser");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;  // 持续识别
      recognition.interimResults = true;  // 返回临时结果
      recognition.lang = 'en-US';  // 可以根据 selectedAccent 动态设置
      
      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0].transcript;
          const confidence = result[0].confidence || 1.0;  // Web Speech API 置信度
          
          // ✅ 幻觉检测 1：置信度检查（0ms 延迟）
          if (confidence < 0.5) {
            console.warn(`[Hallucination Check] Low confidence (${confidence.toFixed(2)}): "${transcript}"`);
            continue;  // 跳过低置信度结果
          }
          
          // ✅ 幻觉检测 2：空文本和语气词过滤（< 2ms 延迟）
          const trimmedText = transcript.trim();
          
          // 检测空文本
          if (!trimmedText || trimmedText.length === 0) {
            continue;
          }
          
          // 检测纯语气词（单独出现时过滤）
          const fillerWords = /^(uh|um|hmm|ah|er|oh|mm|mhm|uh-huh|huh)$/i;
          if (fillerWords.test(trimmedText)) {
            console.warn(`[Hallucination Check] Filler word detected: "${trimmedText}"`);
            continue;
          }
          
          // 检测纯标点或特殊字符
          if (/^[^\w\s]+$/.test(trimmedText)) {
            console.warn(`[Hallucination Check] Only punctuation: "${trimmedText}"`);
            continue;
          }
          
          // ✅ 通过检查，正常处理
          if (result.isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        
        // ✅ 显示预览文本（淡色、斜体）
        if (interimTranscript) {
          setPreviewText(interimTranscript);
          
          // ✅ 流式传译优化：使用 interim 结果 + 防抖触发 TTS
          if (streamingTranslation) {
            // 清除之前的防抖计时器
            if (ttsDebounceTimerRef.current) {
              clearTimeout(ttsDebounceTimerRef.current);
            }
            
            // 设置新的防抖计时器（500ms 平衡响应速度和防重复）
            ttsDebounceTimerRef.current = setTimeout(() => {
              const fullText = interimTranscript.trim();
              
              // ✅ 检查文本长度（至少 8 字符，快速响应）
              if (!fullText || fullText.length < 8) return;
              
              // ✅ 频率限制：距离上次触发至少 1000ms
              const now = Date.now();
              if (now - lastTtsTimeRef.current < 1000) {
                console.log(`[Streaming TTS] Rate limited, waiting...`);
                return;
              }
              
              // ✅ 增量检测：只播放新增部分
              const lastSpoken = lastSpokenTextRef.current;
              
              // 文本归一化（去除标点和多余空格，用于比较）
              const normalize = (text) => text.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
              const normalizedFull = normalize(fullText);
              const normalizedLast = normalize(lastSpoken);
              
              if (normalizedFull.startsWith(normalizedLast) && fullText.length > lastSpoken.length) {
                // 新文本是旧文本的延续
                const newPart = fullText.slice(lastSpoken.length).trim();
                
                // 新增部分至少 8 个字符才播放（更保守）
                if (newPart.length >= 8) {
                  console.log(`[Streaming TTS] Incremental: "${newPart.substring(0, 30)}..." (was: "${lastSpoken.substring(0, 20)}...")`);
                  lastSpokenTextRef.current = fullText;
                  lastTtsTimeRef.current = now;
                  requestStreamingTts(newPart);
                } else {
                  console.log(`[Streaming TTS] Incremental too short (${newPart.length} chars), skipping`);
                }
              } else if (normalizedFull !== normalizedLast && fullText.length >= 8) {
                // 完全不同的文本，且足够长
                console.log(`[Streaming TTS] Full: "${fullText.substring(0, 30)}..."`);
                lastSpokenTextRef.current = fullText;
                lastTtsTimeRef.current = now;
                requestStreamingTts(fullText);
              }
            }, 500);  // 500ms 防抖延迟（平衡速度和准确性）
          }
        }
        
        // ✅ 最终识别结果累积到 liveTranscript
        if (finalTranscript) {
          setPreviewText('');  // 清除预览
          
          // 清除防抖计时器（final 结果已到达）
          if (ttsDebounceTimerRef.current) {
            clearTimeout(ttsDebounceTimerRef.current);
            ttsDebounceTimerRef.current = null;
          }
          
          setLiveTranscript((prev) => {
            const newText = prev + finalTranscript;
            return newText;
          });
          
          // ✅ Final 结果：智能处理剩余文本
          if (streamingTranslation && finalTranscript.trim()) {
            const fullFinalText = finalTranscript.trim();
            const lastSpoken = lastSpokenTextRef.current;
            const now = Date.now();
            const timeSinceLastTts = now - lastTtsTimeRef.current;
            
            // 文本归一化比较
            const normalize = (text) => text.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
            const normalizedFinal = normalize(fullFinalText);
            const normalizedLast = normalize(lastSpoken);
            
            // 计算实际未播放的部分
            let remaining = '';
            if (normalizedFinal.startsWith(normalizedLast)) {
              // final 是 lastSpoken 的延续
              remaining = fullFinalText.slice(lastSpoken.length).trim();
            } else if (normalizedFinal !== normalizedLast) {
              // 完全不同，播放全部
              remaining = fullFinalText;
            }
            
            // ⚠️ 如果有未播放的文本（哪怕只有几个字），都应该播放
            if (remaining.length >= 3) {  // 降低阈值到3个字符（如 "me", "you" 等）
              // 检查是否最近刚播放过（1秒内）
              if (timeSinceLastTts < 1000) {
                console.log(`[Streaming TTS] Final部分播放: "${remaining}" (补充遗漏，${timeSinceLastTts}ms前触发过)`);
              } else {
                console.log(`[Streaming TTS] Final播放: "${remaining.substring(0, 30)}..." (${remaining.length} chars)`);
              }
              lastSpokenTextRef.current = fullFinalText;
              lastTtsTimeRef.current = now;
              requestStreamingTts(remaining);
            } else {
              console.log(`[Streaming TTS] Final完成，无新内容 (last: "${lastSpoken.substring(0, 30)}...", final: "${fullFinalText.substring(0, 30)}...")`);
              lastSpokenTextRef.current = fullFinalText;
            }
          }
        }
      };
      
      recognition.onerror = (event) => {
        console.error('[Web Speech] Error:', event.error);
        if (event.error === 'no-speech') {
          // 用户没说话，忽略
          return;
        }
        // 其他错误尝试重启
        setTimeout(() => {
          if (recording && speechRecognitionRef.current) {
            try { recognition.start(); } catch {}
          }
        }, 1000);
      };
      
      recognition.onend = () => {
        // 如果还在录音，自动重启（连续识别）
        if (recording && speechRecognitionRef.current === recognition) {
          try {
            recognition.start();
          } catch (e) {
            console.warn('[Web Speech] Restart failed:', e);
          }
        }
      };
      
      speechRecognitionRef.current = recognition;
      recognition.start();
      console.log('[Web Speech] Started');
    } catch (err) {
      console.error('[Web Speech] Failed to start:', err);
    }
  };
  
  const stopWebSpeechPreview = () => {
    // 清除防抖计时器
    if (ttsDebounceTimerRef.current) {
      clearTimeout(ttsDebounceTimerRef.current);
      ttsDebounceTimerRef.current = null;
    }
    
    // 重置已播放文本和触发时间（停止录音，准备下次新会话）
    lastSpokenTextRef.current = '';
    lastTtsTimeRef.current = 0;
    
    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
        speechRecognitionRef.current = null;
        setPreviewText('');  // 清除预览文本
        console.log('[Web Speech] Stopped');
      } catch (err) {
        console.error('[Web Speech] Failed to stop:', err);
      }
    }
  };

  /** ===== upgrade / logout / change password ===== */
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const upgradeKeyRef = useRef(null);

  const [pwdOpen, setPwdOpen] = useState(false);
  const [newPwd, setNewPwd] = useState("");
  const [showNewPwd, setShowNewPwd] = useState(false);

  const confirmUpgrade = async () => {
    const key = upgradeKeyRef.current?.value?.trim();
    if (!key) return;
    const r = await verifyUpgradeKey(key);
    if (r?.ok) {
      setModelUnlocked(true);
      localStorage.setItem(PAID_UNLOCK_KEY, "1");
      setUpgradeOpen(false);
      alert("Upgrade successful! Paid model unlocked.");
    } else alert("Invalid key!");
  };

  const confirmChangePassword = async () => {
    if (!newPwd) { alert("Please enter a new password."); return; }
    try {
      const res = await changePassword({ newPassword: newPwd });
      if (res?.ok) {
        setPwdOpen(false);
        setNewPwd("");
        setShowNewPwd(false);
        alert("Password updated. It will take effect next login.");
      } else {
        alert(res?.message || "Failed to update password.");
      }
    } catch (e) {
      alert(e?.message || "Unexpected error.");
    }
  };

  const confirmLogout = () => {
    if (recording) micStop();
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUserId");
    localStorage.removeItem("authUsername");
    sessionStorage.removeItem("authToken");
    sessionStorage.removeItem("authUserId");
    sessionStorage.removeItem("authUsername");
    navigate("/login", { replace: true });
  };

  return (
    <div className={styles.container}>
      {/* ===== Sidebar ===== */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTop} ref={menuRef}>
          <button
            className={styles.settingsButton}
            onClick={() => setMenuOpen((v) => !v)}
            title="Settings"
          >
            ⚙️
          </button>
          <span className={styles.hiText}>Hi, {username}!</span>
          {menuOpen && (
            <div className={styles.dropdown}>
              <button onClick={() => { setMenuOpen(false); setUpgradeOpen(true); }}>
                <span className={styles.icon}>🌐</span> Update Model
              </button>
              <button onClick={() => { setMenuOpen(false); setPwdOpen(true); }}>
                <span className={styles.icon}>🛠️</span> Change Password
              </button>
              <button onClick={() => { setMenuOpen(false); confirmLogout(); }}>
                <span className={styles.icon}>📤</span> Log Out
              </button>
            </div>
          )}
        </div>

        <div className={styles.convoHeader}>
          <span>Conversations</span>
          <button className={styles.newBtn} onClick={handleNewConversation}>New</button>
        </div>

        <ul className={styles.convoList}>
          {convos.map((c) => {
            const lastSeg = (c.segments || [])[ (c.segments || []).length - 1 ];
            const preview = lastSeg?.transcript?.slice(0, 38) || "";
            return (
              <li
                key={c.id}
                onMouseEnter={() => setHoverId(c.id)}
                onMouseLeave={() => setHoverId(null)}
                className={`${styles.convoItem} ${c.id === activeId ? styles.convoActive : ""}`}
                onClick={() => activateConversation(c.id)}
              >
                <div className={styles.convoRow}>
                  <div className={styles.convoTitle}>{c.title || "Untitled"}</div>
                  <button
                    className={`${styles.dotBtn} ${hoverId === c.id ? styles.dotBtnVisible : ""}`}
                    onClick={(e) => { e.stopPropagation(); setDotMenuFor(c.id === dotMenuFor ? null : c.id); }}
                    title="More"
                  >
                    ⋯
                  </button>
                </div>
                {preview ? <div className={styles.convoPreview}>{preview}</div> : null}

                {dotMenuFor === c.id && (
                  <div ref={dotMenuRef} className={styles.dotMenu} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.dotMenuItem} onClick={() => openRename(c)}>✏️ Rename</div>
                    <div className={styles.dotMenuItemDanger} onClick={() => doDelete(c.id)}>🗑️ Delete</div>
                  </div>
                )}
              </li>
            );
          })}
          {!convos.length && <li className={styles.convoEmpty}>No conversations yet</li>}
        </ul>
      </aside>

      {/* ===== Main ===== */}
      <main className={styles.main}>
        <div className={styles.modelBox}>
          <label className={styles.accentLabel}>Model </label>
          <select
            className={styles.select}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="free">Free</option>
            <option value="paid" disabled={!modelUnlocked}>Paid</option>
          </select>
        </div>

        <div className={styles.transcript} ref={transcriptBoxRef}>
          {activeConv?.segments?.map((s) => {
            // ✅ 获取说话人信息
            const speakerId = s.speakerId || null;
            const speakerColor = speakerId ? SPEAKER_COLORS[speakerId] : null;
            const speakerName = speakerId ? SPEAKER_NAMES[speakerId] : null;
            
            return (
              <div 
                key={s.id} 
                className={styles.segment}
                data-speaker={speakerId}
              >
                <div className={styles.segmentMeta}>
                  {/* ✅ 显示说话人标签 */}
                  {speakerId && (
                    <span 
                      className={styles.speakerTag}
                      style={{ backgroundColor: speakerColor }}
                    >
                      {speakerName}
                    </span>
                  )}
                  <span>
                    {new Date(s.start).toLocaleTimeString()} — {s.end ? new Date(s.end).toLocaleTimeString() : "…"}
                  </span>
                  {s.audioUrl && <audio controls autoPlay src={s.audioUrl} className={styles.segmentAudio} />}
                </div>
                {s.transcript ? <div className={styles.segmentText}>{s.transcript}</div> : null}
              </div>
            );
          })}
          {recording ? (
            <div className={`${styles.segment} ${styles.segmentLive}`}>
              <div className={styles.segmentMeta}>
                <span>Recording…</span>
                {previewText && <span className={styles.previewBadge}>Preview</span>}
              </div>
              <div className={styles.segmentText}>
                {liveTranscript}
                {previewText && <span className={styles.previewText}>{previewText}</span>}
                {interimText && <span style={{ opacity: 0.5 }}>{interimText}</span>}
              </div>
            </div>
          ) : !activeConv?.segments?.length ? (
            <span className={styles.placeholder}>Transcription will appear here…</span>
          ) : null}
        </div>

        <div className={styles.accentBox}>
          <label className={styles.accentLabel}>Accent</label>
          <select className={styles.select} value={selectedAccent} onChange={(e) => setSelectedAccent(e.target.value)}>
            {ACCENTS.map((a) => <option key={a}>{a}</option>)}
          </select>
        </div>

        <div className={styles.centerControls}>
          <button
            className={`${styles.iconBtn} ${styles.micBtn} ${recording ? styles.micActive : ""}`}
            onClick={onMicToggle}
            title={recording ? "Stop" : "Start"}
          >
            🎙️
          </button>
          <div className={styles.volumeWrap}>
            <button className={styles.iconBtn} title="Volume" onClick={() => setVolumeOpen((v) => !v)}>
              🔊
            </button>
            {volumeOpen && (
              <div className={styles.volumePopover} onMouseLeave={() => setVolumeOpen(false)}>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={volume}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value);
                    setVolume(v);
                    streamRef.current?.setOutputVolume?.(v);
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ===== rename modal ===== */}
      {renameOpen && (
        <div className={styles.backdrop} onClick={() => setRenameOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Rename Conversation</div>
            <div className={styles.modalBody}>
              <input
                className={styles.input}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && commitRename()}
                autoFocus
                placeholder="Enter a new title"
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setRenameOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={commitRename}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* ===== upgrade modal ===== */}
      {upgradeOpen && (
        <div className={styles.backdrop} onClick={() => setUpgradeOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Enter upgrade key</div>
            <div className={styles.modalBody}>
              <input
                className={styles.input}
                ref={upgradeKeyRef}
                placeholder="Enter key (e.g., SECRET123)"
                autoFocus
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setUpgradeOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={confirmUpgrade}>Confirm</button>
            </div>
          </div>
        </div>
      )}

      {/* ===== change password modal ===== */}
      {pwdOpen && (
        <div className={styles.backdrop} onClick={() => setPwdOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Change Password</div>
            <div className={styles.modalBody}>
              <label className={styles.modalLabel}>New Password</label>
              <div className={styles.field}>
                <input
                  className={`${styles.input} ${styles.inputWithEye}`}
                  type={showNewPwd ? "text" : "password"}
                  placeholder="Enter a new password"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                />
                <button
                  type="button"
                  className={styles.eyeBtn}
                  onClick={() => setShowNewPwd((v) => !v)}
                  aria-label={showNewPwd ? "Hide password" : "Show password"}
                  title={showNewPwd ? "Hide password" : "Show password"}
                >
                  <EyeIcon open={showNewPwd} />
                </button>
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setPwdOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={confirmChangePassword}>Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
