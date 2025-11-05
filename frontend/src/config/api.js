// frontend/src/config/api.js
// Unified API configuration with environment variable support

/**
 * API Base URL
 * Uses environment variable VITE_API_BASE_URL, or defaults to localhost
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API v1 path prefix
 */
export const API_V1_PREFIX = '/api/v1';

/**
 * Complete API Base URL (with version prefix)
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
 * Universal API request method
 * @param {string} path - API path (without base URL)
 * @param {object} options - Fetch options
 * @returns {Promise<{ok: boolean, data?: any, message?: string, code?: string}>}
 */
export async function apiRequest(path, { method = 'GET', body, headers = {} } = {}) {
  const url = `${API_BASE}${path}`;

  const fetchOptions = {
    method,
    credentials: 'include', // Important: Include HttpOnly cookies
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
    } catch {
      // Response might not be JSON (e.g., 204 No Content, plain text)
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
