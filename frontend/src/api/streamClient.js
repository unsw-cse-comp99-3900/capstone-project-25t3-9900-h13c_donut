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

  let ttsMime = "audio/mpeg";
  let ttsChunks = [];
  
  // 🔥 音频播放相关
  let audioContext = null;
  let audioQueue = [];
  let isPlaying = false;
  let currentVolume = outputVolume;

  function sendJSON(ws, obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  }

  // 🔥 播放音频片段
  async function playNextChunk() {
    if (audioQueue.length === 0) {
      isPlaying = false;
      return;
    }

    isPlaying = true;
    const chunk = audioQueue.shift();

    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }

      console.log("[streamClient] Decoding audio chunk:", chunk.byteLength, "bytes");
      const audioBuffer = await audioContext.decodeAudioData(chunk.slice(0));
      
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      
      const gainNode = audioContext.createGain();
      gainNode.gain.value = currentVolume;
      
      source.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      source.onended = () => {
        console.log("[streamClient] Chunk ended, playing next");
        playNextChunk();
      };
      
      source.start(0);
      console.log("[streamClient] ✅ Playing audio chunk");
      
    } catch (e) {
      console.error("[streamClient] ❌ Play error:", e);
      playNextChunk();
    }
  }

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
        console.log("[client] textWS message raw:", ev.data);
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
        } catch (e) {
          if (typeof ev.data === "string") onText?.(ev.data);
        }
      };
    });

    // 2) TTS 通道
    if (WS_TTS_URL) {
      try {
        await new Promise((resolve, reject) => {
          ttsWS = new WebSocket(WS_TTS_URL);
          ttsWS.binaryType = "arraybuffer"; // 🔥 关键！
          
          ttsWS.onopen = () => {
            console.log("[client] ttsWS open, subscribe", conversationId);
            sendJSON(ttsWS, { type: "start", conversationId });
            resolve();
          };
          
          ttsWS.onerror = (e) => { 
            console.warn("[client] ttsWS error", e); 
            reject(e); 
          };
          
          ttsWS.onmessage = (ev) => {
            // 🔥 关键修复：正确处理二进制数据
            if (typeof ev.data === "string") {
              try {
                const msg = JSON.parse(ev.data);
                console.log("[client] ttsWS control message:", msg);
                
                if (msg.type === "start") {
                  console.log("[client] 🎵 TTS stream starting");
                  ttsMime = msg.mime || "audio/mpeg";
                  ttsChunks = [];
                  audioQueue = [];
                  onTtsStart?.();
                  
                } else if (msg.type === "stop") {
                  console.log("[client] 🎵 TTS stream stopped, waiting for playback");
                  
                  // 等待播放完成
                  const waitForPlayback = async () => {
                    let waitCount = 0;
                    while ((audioQueue.length > 0 || isPlaying) && waitCount < 100) {
                      await new Promise(resolve => setTimeout(resolve, 100));
                      waitCount++;
                    }
                    console.log("[client] 🎵 Playback finished");
                    
                    // 创建完整 blob
                    const blob = new Blob(ttsChunks, { type: ttsMime });
                    console.log("[client] 🎵 Created audio blob:", blob.size, "bytes");
                    onTtsBlob?.(blob);
                    onTtsEnded?.();
                  };
                  waitForPlayback();
                  
                } else if (msg.type === "ready" || msg.type === "pong") {
                  // ignore
                }
              } catch {
                // ignore
              }
            } 
            // 🔥 处理二进制音频数据
            else if (ev.data instanceof ArrayBuffer) {
              console.log("[client] 🎵 TTS binary chunk received:", ev.data.byteLength, "bytes");
              
              // 保存到数组（用于最后创建完整 blob）
              ttsChunks.push(new Uint8Array(ev.data));
              
              // 🔥 立即加入播放队列
              audioQueue.push(ev.data.slice(0)); // 复制 ArrayBuffer
              
              // 如果还没开始播放，立即开始
              if (!isPlaying) {
                console.log("[client] 🎵 Starting audio playback");
                playNextChunk();
              }
            } else {
              console.warn("[client] ttsWS unknown data type:", typeof ev.data);
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
        console.log("[client] send audio chunk", e.data.size);
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
    if (audioContext) {
      try { await audioContext.close(); } catch {}
    }
  }

  function setOutputVolume(v) {
    currentVolume = Math.max(0, Math.min(1, v));
    console.log("[streamClient] Volume set to:", currentVolume);
  }

  return { open, startSegment, stopSegment, startMic, stopMic, close, setOutputVolume };
}