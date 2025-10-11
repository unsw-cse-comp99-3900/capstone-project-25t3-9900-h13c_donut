/**
 * StreamClient — 本地占位实现（实时字幕 + 实时TTS，不重复），或 WS 接后端
 * 变更：
 * 1) 新增去重差分：只朗读/上屏“真正新增的后缀”，不会重复。
 * 2) 录音期自动压低 TTS 音量（ducking）防回声；停止后恢复。
 */

export function createStreamClient(opts) {
  const {
    conversationId,
    model = "modelI",
    accent = "American English",
    mode = "local", // "local" | "ws"
    onText = () => {},
    onTtsStart = () => {},
    onTtsBlob = () => {},
    onTtsEnded = () => {},
    outputVolume = 1,
  } = opts || {};

  const USE_LOCAL = mode === "local";

  const AUDIO_WS = import.meta.env.VITE_AUDIO_WS_URL || "";
  const TEXT_WS  = import.meta.env.VITE_TRANSCRIPT_WS_URL || "";

  let wsAudio = null;
  let wsText  = null;

  let _outputVolume = outputVolume;
  function setOutputVolume(v){ _outputVolume = Math.max(0, Math.min(1, v)); }

  // ===== Local 状态 =====
  let recog = null;
  let accumFinal = "";      // 我们维护的“已确认文本”
  let lastInterim = "";
  let lastSpokenIndex = 0;  // 已朗读到的字符位置
  let isRecording = false;  // 录音期 -> TTS 音量压低以防回声

  // 将整段TTS录成Blob
  let pageCaptureStream = null;
  let pageRecorder = null;
  let pageChunks = [];
  let ttsPending = 0;

  /** ---------- 工具：只取真正新增后缀 ---------- */
  function normalize(s){ return (s || "").replace(/\s+/g, " ").trimStart(); }

  // 从 nextFinal 中扣掉 prevFinal，考虑部分重叠（例如引擎把最后几个词重复拼接）
  function diffSuffix(prevFinal, nextFinal){
    prevFinal = normalize(prevFinal);
    nextFinal = normalize(nextFinal);
    if (!nextFinal) return "";

    // 1) 完全包含：next 以 prev 为前缀
    if (nextFinal.startsWith(prevFinal)) {
      return nextFinal.slice(prevFinal.length);
    }

    // 2) 存在重叠：prev 的某个后缀 == next 的前缀
    const maxOverlap = Math.min(prevFinal.length, nextFinal.length);
    for (let k = maxOverlap; k > 0; k--) {
      if (prevFinal.slice(prevFinal.length - k) === nextFinal.slice(0, k)) {
        return nextFinal.slice(k);
      }
    }

    // 3) 没有公共前缀：认为 next 全部是新增（极少发生）
    return nextFinal;
  }

  /** ---------- Voice 选择（占位） ---------- */
  function pickVoiceForAccent(accentName){
    const langMap = {
      "American English":  "en-US",
      "Australia English": "en-AU",
      "British English":   "en-GB",
      "Chinese English":   "en-US", // 没有“中式英语”voice，用美式+轻微pitch模拟
      "India English":     "en-IN",
    };
    const target = langMap[accentName] || "en-US";
    const voices = window.speechSynthesis?.getVoices?.() || [];
    const exact = voices.find(v => (v.lang||"").toLowerCase() === target.toLowerCase());
    if (exact) return exact;
    const anyEn = voices.find(v => /^en[-_]/i.test(v.lang||""));
    return anyEn || null;
  }

  /** ---------- 朗读“新增 delta”并加入队列（录音期 ducking） ---------- */
  function speakDelta(deltaText){
    if (!deltaText || !("speechSynthesis" in window)) return;

    let voice = pickVoiceForAccent(accent);
    if (!voice) setTimeout(() => { voice = pickVoiceForAccent(accent); }, 120);

    const u = new SpeechSynthesisUtterance(deltaText);

    // 录音期自动压低音量以防回声（可调 0.15）
    const duckFactor = isRecording ? 0.15 : 1.0;
    u.volume = Math.max(0, Math.min(1, _outputVolume * duckFactor));

    u.rate   = 1.0;
    u.pitch  = 1.0;
    if (voice) u.voice = voice;

    if (accent === "British English")   u.pitch = 1.05;
    if (accent === "Australia English") u.pitch = 1.02;
    if (accent === "Chinese English")   u.pitch = 0.95;
    if (accent === "India English")     u.pitch = 1.08;

    ttsPending++;
    if (ttsPending === 1) onTtsStart();

    u.onend = () => { ttsPending = Math.max(0, ttsPending - 1); };
    u.onerror = () => { ttsPending = Math.max(0, ttsPending - 1); };

    window.speechSynthesis.speak(u);
  }

  // 新的 final 到达时：只朗读真正新增部分
  function handleNewFinal(nextFinalAll){
    const delta = diffSuffix(accumFinal, nextFinalAll);
    if (!delta || !delta.trim()) return;
    accumFinal = normalize(accumFinal + delta);
    speakDelta(delta);
    onText({ final: delta }); // 上层只接收新增片段，避免重复拼接
  }

  /* =======================
   *        Local 模式
   * ======================= */
  async function openLocal(){ /* no-op */ }

  async function closeLocal(){
    try { recog?.stop?.(); } catch {}
    recog = null;
    try { pageRecorder?.stop?.(); } catch {}
    if (pageCaptureStream) pageCaptureStream.getTracks().forEach(t => t.stop());
    pageCaptureStream = null;
    pageRecorder = null;
    pageChunks = [];
    accumFinal = "";
    lastInterim = "";
    lastSpokenIndex = 0;
    ttsPending = 0;
    isRecording = false;
  }

  async function startSegmentLocal(){
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      console.warn("This browser does not support SpeechRecognition.");
      return;
    }

    // 清状态
    accumFinal = "";
    lastInterim = "";
    lastSpokenIndex = 0;
    ttsPending = 0;
    isRecording = true;

    // 捕获页面音频（录TTS）
    pageChunks = [];
    try {
      pageCaptureStream = await navigator.mediaDevices.getDisplayMedia({ audio: true, video: false });
      pageRecorder = new MediaRecorder(pageCaptureStream, { mimeType: "audio/webm;codecs=opus" });
      pageRecorder.ondataavailable = (e)=>{ if (e.data && e.data.size>0) pageChunks.push(e.data); };
      pageRecorder.start(200);
    } catch {
      pageRecorder = null;
      pageCaptureStream = null;
    }

    // 语音识别
    recog = new SR();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = "en-US";

    recog.onresult = (ev) => {
      // 组合“这次事件里”的全部 final
      let nextAll = "";
      for (let i=0; i<ev.results.length; i++){
        const r = ev.results[i];
        if (r.isFinal) nextAll += r[0].transcript;
      }
      nextAll = normalize(nextAll);

      // 计算真正新增并派发
      if (nextAll && nextAll !== accumFinal) {
        handleNewFinal(nextAll);
      }

      // 最新一条 interim
      const last = ev.results[ev.results.length - 1];
      const it = last && !last.isFinal ? (last[0]?.transcript || "") : "";
      const nIt = normalize(it);
      if (nIt !== lastInterim) {
        lastInterim = nIt;
        if (nIt) onText({ interim: nIt });
      }
    };

    recog.onerror = (e) => console.warn("SR error:", e.error);
    recog.onend = () => {
      // 某些浏览器会间歇性结束，继续监听
      try { recog.start(); } catch {}
    };

    recog.start();
  }

  async function stopSegmentLocal(){
    isRecording = false;

    try { recog?.stop?.(); } catch {}
    recog = null;

    // 等待 TTS 队列全部播完
    await new Promise((resolve) => {
      const check = () => {
        if (ttsPending === 0 && !window.speechSynthesis.speaking) return resolve();
        setTimeout(check, 120);
      };
      check();
    });

    // 结束页面录音 -> 输出 Blob
    let outBlob = null;
    if (pageRecorder) {
      await new Promise((res)=>{ pageRecorder.onstop = res; pageRecorder.stop(); });
      if (pageChunks.length) outBlob = new Blob(pageChunks, { type: "audio/webm" });
    }
    if (pageCaptureStream) pageCaptureStream.getTracks().forEach(t=>t.stop());
    pageRecorder = null;
    pageCaptureStream = null;

    onTtsBlob(outBlob || null);
    onTtsEnded();

    pageChunks = [];
    ttsPending = 0;
  }

  /* =======================
   *        WS 模式
   * ======================= */
  async function openWs(){
    if (TEXT_WS) {
      wsText = new WebSocket(`${TEXT_WS}?conversationId=${encodeURIComponent(conversationId)}`);
      wsText.onmessage = (evt)=>{
        try {
          if (typeof evt.data === "string" && evt.data.startsWith("{")){
            const obj = JSON.parse(evt.data);
            if (obj.interim) onText({ interim: obj.interim });
            if (obj.final)   onText({ final: obj.final });
          } else if (typeof evt.data === "string") {
            onText({ final: evt.data });
          }
        } catch {}
      };
    }
    if (AUDIO_WS) {
      wsAudio = new WebSocket(`${AUDIO_WS}?conversationId=${encodeURIComponent(conversationId)}&model=${encodeURIComponent(model)}&accent=${encodeURIComponent(accent)}`);
      wsAudio.binaryType = "arraybuffer";
      wsAudio.onmessage = (evt)=>{
        if (evt.data instanceof ArrayBuffer){
          const blob = new Blob([evt.data], { type: "audio/wav" });
          onTtsBlob(blob);
          onTtsEnded();
        }
      };
    }
  }
  async function closeWs(){
    try { wsText?.close?.(); } catch {}
    try { wsAudio?.close?.(); } catch {}
    wsText = null; wsAudio = null;
  }
  async function startSegmentWs(){
    // 真实后端：这里通常会通知开始 + 你在上层用 MediaRecorder 发送 mic 分片
    isRecording = true;
    wsAudio?.readyState === WebSocket.OPEN && wsAudio.send(JSON.stringify({ type: "start_segment", model, accent }));
  }
  async function stopSegmentWs(){
    isRecording = false;
    wsAudio?.readyState === WebSocket.OPEN && wsAudio.send(JSON.stringify({ type: "end_segment" }));
  }
  function sendAudioChunkWs(data){
    if (!data) return;
    if (data instanceof Blob) {
      data.arrayBuffer().then((buf)=> wsAudio?.readyState === WebSocket.OPEN && wsAudio.send(buf));
    } else if (data instanceof ArrayBuffer) {
      wsAudio?.readyState === WebSocket.OPEN && wsAudio.send(data);
    }
  }

  // 统一导出
  async function open()  { return USE_LOCAL ? openLocal()  : openWs(); }
  async function close() { return USE_LOCAL ? closeLocal() : closeWs(); }
  async function startSegment(){ return USE_LOCAL ? startSegmentLocal() : startSegmentWs(); }
  async function stopSegment() { return USE_LOCAL ? stopSegmentLocal()  : stopSegmentWs(); }

  async function startMic() {}
  async function stopMic() {}
  function sendAudioChunk(data){ if (!USE_LOCAL) sendAudioChunkWs(data); }

  return { open, close, startSegment, stopSegment, startMic, stopMic, sendAudioChunk, setOutputVolume };
}
