// src/api/dashboard.js
// 使用统一的 API 配置
import { apiRequest } from '../config/api.js';

/**
 * Verify and consume upgrade key (普通用户激活付费模型)
 * @param {string} key - 密钥明文
 * @returns {Promise<{ok: boolean, message?: string}>}
 */
export async function verifyUpgradeKey(key) {
  // 调用 consume=true 以真正激活密钥
  const result = await apiRequest('/admin/verify-key', {
    method: 'POST',
    body: { key, consume: true },
  });

  if (result.ok && result.data?.ok) {
    return { ok: true };
  } else {
    return { ok: false, message: result.message || '密钥无效或已使用' };
  }
}
