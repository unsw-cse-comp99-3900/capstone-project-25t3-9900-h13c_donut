// frontend/src/config/api.js
// 统一的 API 配置文件，支持环境变量

/**
 * API Base URL
 * 优先使用环境变量 VITE_API_BASE_URL，否则使用默认值
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API v1 路径前缀
 */
export const API_V1_PREFIX = '/api/v1';

/**
 * 完整的 API Base URL (包含版本前缀)
 */
export const API_BASE = `${API_BASE_URL}${API_V1_PREFIX}`;

/**
 * WebSocket URLs
 */
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
export const WS_UPLOAD_URL = `${WS_BASE_URL}/ws/upload-audio`;
export const WS_TEXT_URL = `${WS_BASE_URL}/ws/asr-text`;
export const WS_TTS_URL = `${WS_BASE_URL}/ws/tts-audio`;

/**
 * API 请求通用方法
 * @param {string} path - API 路径（不包含 base URL）
 * @param {object} options - fetch 选项
 * @returns {Promise<{ok: boolean, data?: any, message?: string, code?: string}>}
 */
export async function apiRequest(path, { method = 'GET', body, headers = {} } = {}) {
  const url = `${API_BASE}${path}`;

  const fetchOptions = {
    method,
    credentials: 'include', // 重要：带上 HttpOnly Cookie
    headers: {
      ...headers,
    },
  };

  if (body) {
    fetchOptions.headers['Content-Type'] = 'application/json';
    fetchOptions.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(url, fetchOptions);
    let data = null;

    try {
      data = await res.json();
    } catch (_) {
      // 响应可能不是 JSON
    }

    if (!res.ok || (data && data.success === false)) {
      const msg = data?.error?.message || data?.detail || `HTTP ${res.status}`;
      return { ok: false, message: msg, code: data?.error?.code || data?.code };
    }

    return { ok: true, data: data?.data ?? data };
  } catch (error) {
    return { ok: false, message: error.message || 'Network error', code: 'NETWORK_ERROR' };
  }
}
