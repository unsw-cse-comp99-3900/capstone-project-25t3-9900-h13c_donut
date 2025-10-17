const WS_UPLOAD_URL = import.meta.env.VITE_WS_UPLOAD_URL;
const WS_TEXT_URL   = import.meta.env.VITE_WS_TEXT_URL;
const WS_TTS_URL    = import.meta.env.VITE_WS_TTS_URL;

export function createStreamClient({
  conversationId,
  model = "free",
  accent = "American English",
  onText,
  onTtsStart,
  onTtsBlob,
  onTtsEnded,
  outputVolume = 1,
}) {
  let uploadWS = null;
  let textWS = null;
  let ttsWS = null;

  let mediaStream = null;
  let mediaRecorder = null;

  // ===== TTS 播放相关 =====
  let ttsMime = "audio/mpeg";
  let ttsChunks = []; // 收集所有二进制分片，最后拼成 Blob

  // -- MSE 播放器 --
  let audioEl = null;
  let mediaSource = null;
  let sourceBuffer = null;
  let mseQueue = [];         // Uint8Array 队列，等待 append
  let mseReady = false;
  let mseEnded = false;

  // -- WebAudio 退化播放器（仅在 MSE 不可用时启用） --
  let audioContext = null;
  let decodeQueue = [];      // ArrayBuffer 队列
  let decodePlaying = false;

  let currentVolume = Math.max(0, Math.min(1, outputVolume));

  // ========== 工具 ==========
  function sendJSON(ws, obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  }

  function ensureAudioElement() {
    if (audioEl) return audioEl;
    audioEl = document.createElement("audio");
    audioEl.autoplay = true;
    audioEl.controls = false;
    audioEl.style.display = "none"; // 不占位
    audioEl.volume = currentVolume;
    document.body.appendChild(audioEl);
    return audioEl;
  }

  // ========== MSE 实现 ==========
  function mseInit() {
    const el = ensureAudioElement();
    if (!("MediaSource" in window)) return false;

    mediaSource = new MediaSource();
    el.src = URL.createObjectURL(mediaSource);
    mseQueue = [];
    mseReady = false;
    mseEnded = false;

    mediaSource.addEventListener("sourceopen", () => {
      try {
        // 绝大多数浏览器支持 'audio/mpeg'
        if (!MediaSource.isTypeSupported(ttsMime)) {
          // 退化为 audio/mpeg
          ttsMime = "audio/mpeg";
        }
        sourceBuffer = mediaSource.addSourceBuffer(ttsMime);
        sourceBuffer.mode = "sequence";
        sourceBuffer.addEventListener("updateend", mseFeed);
        mseReady = true;
        mseFeed();
      } catch (e) {
        console.warn("[MSE] sourceopen error, fallback to WebAudio:", e);
        mseTearDown();
      }
    });

    mediaSource.addEventListener("error", (e) => {
      console.warn("[MSE] mediaSource error:", e);
    });

    return true;
  }

  function mseAppend(u8) {
    if (!mseReady || !sourceBuffer) {
      mseQueue.push(u8);
      return;
    }
    mseQueue.push(u8);
    mseFeed();
  }

  function mseFeed() {
    if (!sourceBuffer || sourceBuffer.updating) return;
    if (mseQueue.length === 0) {
      if (mseEnded && mediaSource && mediaSource.readyState === "open") {
        try { mediaSource.endOfStream(); } catch {}
      }
      return;
    }
    const chunk = mseQueue.shift();
    try {
      sourceBuffer.appendBuffer(chunk);
    } catch (e) {
      console.warn("[MSE] append error, dropping chunk:", e);
    }
  }

  function mseEnd() {
    mseEnded = true;
    mseFeed();
  }

  function mseTearDown() {
    try {
      if (sourceBuffer) {
        sourceBuffer.abort();
      }
    } catch {}
    try {
      if (mediaSource && mediaSource.readyState === "open") {
        mediaSource.endOfStream();
      }
    } catch {}
    sourceBuffer = null;
    mediaSource = null;
    mseQueue = [];
    mseReady = false;
    mseEnded = false;
  }

  // ========== WebAudio 退化实现（攒包后解码） ==========
  const MIN_CHUNK_BYTES = 24 * 1024; // 累计到 24KB 再解码
  const MAX_BUFFER_BYTES = 1024 * 1024; // 上限 1MB

  async function waPlayNext() {
    if (decodePlaying) return;
    decodePlaying = true;

    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      const el = ensureAudioElement(); // 用 <audio> 控制音量的视觉行为，这里不用其解码
      el.volume = currentVolume;

      while (decodeQueue.length > 0) {
        // 拼接尽可能多的分片，提高解码成功率
        let total = 0;
        for (const ab of decodeQueue) total += ab.byteLength;
        if (total < MIN_CHUNK_BYTES) break;

        // 取尽量多的数据去解码
        const big = new Uint8Array(total);
        let offset = 0;
        while (decodeQueue.length) {
          const ab = decodeQueue.shift();
          const u8 = new Uint8Array(ab);
          big.set(u8, offset);
          offset += u8.byteLength;
        }

        try {
          const buf = big.buffer;
          const decoded = await audioContext.decodeAudioData(buf.slice(0));
          const src = audioContext.createBufferSource();
          const gain = audioContext.createGain();
          gain.gain.value = currentVolume;
          src.buffer = decoded;
          src.connect(gain);
          gain.connect(audioContext.destination);

          await new Promise((resolve) => {
            src.onended = resolve;
            src.start(0);
          });
        } catch (e) {
          console.warn("[WebAudio] decode failed once, keep buffering:", e);
          // 放回去，等待更多数据
          decodeQueue.unshift(big.buffer);
          if (big.byteLength > MAX_BUFFER_BYTES) {
            console.warn("[WebAudio] buffer too large, dropping");
            decodeQueue = [];
          }
          break;
        }
      }
    } finally {
      decodePlaying = false;
    }
  }

  // ========== 外部 API ==========
  async function open() {
    console.log("[client] createStreamClient.open() called");

    // 1) 文本通道
    await new Promise((resolve, reject) => {
      textWS = new WebSocket(WS_TEXT_URL);
      textWS.onopen = () => {
        console.log("[client] textWS open, subscribe", conversationId);
        sendJSON(textWS, { type: "subscribe", conversationId });
        resolve();
      };
      textWS.onerror = (e) => { console.error("[client] textWS error", e); reject(e); };
      textWS.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg?.type === "ready" || msg?.type === "pong") return;
          if (msg.type === "interim") {
            onText?.({ interim: msg.text, ts: msg.ts, confidence: msg.confidence });
          } else if (msg.type === "final") {
            onText?.({ final: msg.text, ts: msg.ts, confidence: msg.confidence });
          } else {
            console.warn("[client] textWS unknown msg:", msg);
          }
        } catch {
          if (typeof ev.data === "string") onText?.(ev.data);
        }
      };
    });

    // 2) TTS 通道
    if (WS_TTS_URL) {
      try {
        await new Promise((resolve, reject) => {
          ttsWS = new WebSocket(WS_TTS_URL);
          ttsWS.binaryType = "arraybuffer";

          ttsWS.onopen = () => {
            console.log("[client] ttsWS open, subscribe", conversationId);
            sendJSON(ttsWS, { type: "start", conversationId });
            resolve();
          };

          ttsWS.onerror = (e) => { console.warn("[client] ttsWS error", e); reject(e); };

          ttsWS.onmessage = (ev) => {
            if (typeof ev.data === "string") {
              // 控制消息
              try {
                const msg = JSON.parse(ev.data);
                if (msg.type === "start") {
                  console.log("[client] 🎵 TTS stream starting");
                  ttsMime = msg.mime || "audio/mpeg";
                  ttsChunks = [];

                  // 优先使用 MSE，失败则退化到 WebAudio
                  const ok = mseInit();
                  if (!ok) {
                    console.warn("[client] MSE not available, fallback to WebAudio buffering");
                    // 清理 WebAudio 队列
                    decodeQueue = [];
                    decodePlaying = false;
                  }
                  onTtsStart?.();
                } else if (msg.type === "stop") {
                  console.log("[client] 🎵 TTS stream stopped");
                  // 完成 MSE
                  if (mediaSource) mseEnd();

                  // 等待播放几百毫秒再出 blob（保险）
                  setTimeout(() => {
                    const blob = new Blob(ttsChunks, { type: ttsMime });
                    onTtsBlob?.(blob);
                    onTtsEnded?.();
                  }, 300);
                }
              } catch {
                // ignore 非 JSON 文本
              }
            } else if (ev.data instanceof ArrayBuffer) {
              // 二进制分片
              const ab = ev.data.slice(0);
              const u8 = new Uint8Array(ab);
              ttsChunks.push(u8);

              // MSE 路径
              if (mediaSource && sourceBuffer) {
                mseAppend(u8);
              } else {
                // 退化路径：缓冲到一定大小再解码
                decodeQueue.push(ab);
                if (!decodePlaying) waPlayNext();
              }
            }
          };
        });
      } catch (e) {
        console.error("[client] ttsWS connection failed:", e);
        ttsWS = null;
      }
    }

    // 3) 上传通道
    await new Promise((resolve, reject) => {
      uploadWS = new WebSocket(WS_UPLOAD_URL);
      uploadWS.onopen = () => {
        console.log("[client] uploadWS open");
        sendJSON(uploadWS, {
          type: "start",
          conversationId,
          model,
          accent,
          sampleRate: 48000,
          format: "audio/webm;codecs=opus",
          asrProvider: "whisper",
        });
        resolve();
      };
      uploadWS.onerror = (e) => { console.error("[client] uploadWS error", e); reject(e); };
    });
  }

  async function startSegment() {
    // noop
  }

  async function stopSegment() {
    if (uploadWS?.readyState === WebSocket.OPEN) {
      console.log("[client] send stop");
      sendJSON(uploadWS, { type: "stop" });
    }
  }

  async function startMic() {
    console.log("[client] requesting mic");
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log("[client] mic granted");
    } catch (e) {
      console.error("[client] getUserMedia failed:", e.name, e.message);
      throw e;
    }

    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    mediaRecorder = new MediaRecorder(mediaStream, {
      mimeType: mime,
      audioBitsPerSecond: 128000,
    });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0 && uploadWS?.readyState === WebSocket.OPEN) {
        e.data.arrayBuffer().then((buf) => uploadWS.send(buf));
      }
    };

    mediaRecorder.start(40);
  }

  async function stopMic() {
    try { mediaRecorder?.stop(); } catch {}
    mediaStream?.getTracks().forEach((t) => t.stop());
    mediaRecorder = null;
    mediaStream = null;
  }

  async function close() {
    try { textWS?.close(); } catch {}
    try { ttsWS?.close(); } catch {}
    try { uploadWS?.close(); } catch {}

    // 释放 MSE
    try { mseTearDown(); } catch {}

    // 释放 WebAudio
    if (audioContext) {
      try { await audioContext.close(); } catch {}
      audioContext = null;
    }
  }

  function setOutputVolume(v) {
    currentVolume = Math.max(0, Math.min(1, v));
    if (audioEl) audioEl.volume = currentVolume;
    // WebAudio 退化路径下也会在播放时读取 currentVolume
    console.log("[streamClient] Volume set to:", currentVolume);
  }

  return { open, startSegment, stopSegment, startMic, stopMic, close, setOutputVolume };
}
