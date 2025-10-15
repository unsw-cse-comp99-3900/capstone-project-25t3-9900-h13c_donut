/**
 * Real-time WebSocket Client - 匹配后端协议
 * 统一WebSocket端点，支持音频流和文本转录
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/realtime';

// 口音映射：前端 -> 后端
const ACCENT_MAP = {
  'American English': 'us',
  'British English': 'uk',
  'Australia English': 'au',
  'Chinese English': 'us', // 暂用美式
  'India English': 'in',
};

// 模型映射：前端 -> 后端
const MODEL_MAP = {
  'modelI': 'free',
  'modelII': 'paid',
  'free': 'free',
  'paid': 'paid',
};

export class RealTimeClient {
  constructor(options = {}) {
    const {
      onPartialText = () => {},
      onFinalText = () => {},
      onTTSChunk = () => {},
      onDone = () => {},
      onError = () => {},
      onConnected = () => {},
      onDisconnected = () => {},
    } = options;

    this.callbacks = {
      onPartialText,
      onFinalText,
      onTTSChunk,
      onDone,
      onError,
      onConnected,
      onDisconnected,
    };

    this.ws = null;
    this.sessionId = null;
    this.audioSequence = 0;
    this.isConnected = false;
    this.isInitialized = false;
  }

  /**
   * 连接WebSocket
   * @param {string} token - JWT认证token
   * @param {string} sessionId - 可选的会话ID（用于恢复会话）
   */
  async connect(token, sessionId = null) {
    if (this.ws) {
      console.warn('WebSocket already connected');
      return;
    }

    return new Promise((resolve, reject) => {
      // 构建WebSocket URL
      const params = new URLSearchParams();
      if (token) params.append('token', token);
      if (sessionId) params.append('session_id', sessionId);
      
      const wsUrl = `${WS_URL}?${params.toString()}`;
      
      console.log('[RealTimeClient] Connecting to:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[RealTimeClient] WebSocket connected');
        this.isConnected = true;
        this.callbacks.onConnected();
        resolve();
      };

      this.ws.onmessage = (event) => {
        this._handleMessage(event);
      };

      this.ws.onerror = (error) => {
        console.error('[RealTimeClient] WebSocket error:', error);
        this.callbacks.onError(error);
        reject(error);
      };

      this.ws.onclose = (event) => {
        console.log('[RealTimeClient] WebSocket closed:', event.code, event.reason);
        this.isConnected = false;
        this.isInitialized = false;
        this.callbacks.onDisconnected();
      };
    });
  }

  /**
   * 初始化会话
   * @param {string} accent - 口音类型
   * @param {string} model - 模型类型
   */
  async initSession(accent = 'American English', model = 'free') {
    if (!this.isConnected) {
      throw new Error('WebSocket not connected');
    }

    const backendAccent = ACCENT_MAP[accent] || 'us';
    const backendModel = MODEL_MAP[model] || 'free';

    const initMessage = {
      type: 'init',
      sessionId: this.sessionId, // null for new session
      accent: backendAccent,
      model: backendModel,
    };

    console.log('[RealTimeClient] Sending init:', initMessage);
    this._send(initMessage);

    // 等待init_success响应
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Init timeout'));
      }, 5000);

      const originalHandler = this._handleMessage.bind(this);
      this._handleMessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'init_success') {
            clearTimeout(timeout);
            this.sessionId = data.sessionId;
            this.isInitialized = true;
            console.log('[RealTimeClient] Session initialized:', this.sessionId);
            this._handleMessage = originalHandler;
            resolve(this.sessionId);
          } else if (data.type === 'error') {
            clearTimeout(timeout);
            this._handleMessage = originalHandler;
            reject(new Error(data.error));
          }
        } catch (e) {
          console.error('[RealTimeClient] Init response parse error:', e);
        }
      };
    });
  }

  /**
   * 发送音频数据（base64编码）
   * @param {ArrayBuffer|Blob} audioData - 音频数据
   */
  async sendAudio(audioData) {
    if (!this.isInitialized) {
      console.warn('[RealTimeClient] Session not initialized');
      return;
    }

    try {
      // 转换为ArrayBuffer
      let buffer;
      if (audioData instanceof Blob) {
        buffer = await audioData.arrayBuffer();
      } else if (audioData instanceof ArrayBuffer) {
        buffer = audioData;
      } else {
        console.error('[RealTimeClient] Invalid audio data type');
        return;
      }

      // 转换为base64
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64 = btoa(binary);

      // 发送音频消息
      const audioMessage = {
        type: 'audio',
        data: base64,
        sequence: this.audioSequence++,
      };

      this._send(audioMessage);
    } catch (error) {
      console.error('[RealTimeClient] Send audio error:', error);
      this.callbacks.onError(error);
    }
  }

  /**
   * 发送停止消息
   */
  stop() {
    if (!this.isInitialized) {
      console.warn('[RealTimeClient] Session not initialized');
      return;
    }

    const stopMessage = { type: 'stop' };
    console.log('[RealTimeClient] Sending stop');
    this._send(stopMessage);
  }

  /**
   * 关闭连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.audioSequence = 0;
    this.isConnected = false;
    this.isInitialized = false;
  }

  /**
   * 处理收到的消息
   * @private
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('[RealTimeClient] Received:', data.type);

      switch (data.type) {
        case 'partial':
          // 部分转录
          this.callbacks.onPartialText(data.text, data.sequence);
          break;

        case 'final':
          // 最终转录
          this.callbacks.onFinalText(data.text, data.segments, data.confidence);
          break;

        case 'tts_chunk':
          // TTS音频分块
          try {
            console.log(`[RealTimeClient] Processing TTS chunk: seq=${data.seq}, isLast=${data.isLast}`);
            // 解码base64为音频数据
            const audioData = this._base64ToArrayBuffer(data.bytes_b64 || data.data);
            console.log(`[RealTimeClient] Decoded audio data: ${audioData.byteLength} bytes`);
            const audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
            console.log(`[RealTimeClient] Created audio blob: ${audioBlob.size} bytes`);
            this.callbacks.onTTSChunk(audioBlob, data.seq, data.isLast);
            console.log(`[RealTimeClient] ✅ onTTSChunk callback called`);
          } catch (e) {
            console.error('[RealTimeClient] TTS chunk decode error:', e);
          }
          break;

        case 'done':
          // 处理完成
          this.callbacks.onDone(data.sessionId, data.totalDuration, data.audioUrl);
          break;

        case 'error':
          // 错误消息
          console.error('[RealTimeClient] Server error:', data.error, data.code);
          this.callbacks.onError(new Error(data.error), data.code);
          break;

        case 'ping':
          // 心跳 - 回复pong
          this._send({ type: 'pong' });
          break;

        case 'audio_received':
          // 音频接收确认（可选处理）
          console.debug('[RealTimeClient] Audio chunk confirmed:', data.sequence);
          break;

        default:
          console.warn('[RealTimeClient] Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('[RealTimeClient] Message parse error:', error);
    }
  }

  /**
   * 发送JSON消息
   * @private
   */
  _send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('[RealTimeClient] WebSocket not ready');
    }
  }

  /**
   * Base64转ArrayBuffer
   * @private
   */
  _base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * 获取当前状态
   */
  getState() {
    return {
      isConnected: this.isConnected,
      isInitialized: this.isInitialized,
      sessionId: this.sessionId,
    };
  }
}

/**
 * 创建Real-time客户端实例（工厂函数）
 */
export function createRealTimeClient(options) {
  return new RealTimeClient(options);
}

