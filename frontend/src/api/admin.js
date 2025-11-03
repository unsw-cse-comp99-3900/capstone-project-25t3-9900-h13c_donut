// frontend/src/api/admin.js
// 管理员相关 API 接口

import { apiRequest } from '../config/api.js';

// ============================================================================
// 一、用户管理接口
// ============================================================================

/**
 * 获取用户列表（支持搜索和分页）
 * @param {object} params - 查询参数
 * @param {string} [params.q] - 搜索关键词（username/email）
 * @param {number} [params.offset=0] - 分页偏移量
 * @param {number} [params.limit=20] - 每页数量
 * @returns {Promise<{ok: boolean, data?: {items: Array, offset: number, limit: number, total: number}}>}
 */
export async function listUsers({ q = '', offset = 0, limit = 20 } = {}) {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  params.append('offset', offset);
  params.append('limit', limit);

  return apiRequest(`/admin/users?${params.toString()}`);
}

/**
 * 获取用户详情
 * @param {string} userId - 用户 ID
 * @returns {Promise<{ok: boolean, data?: {user: object}}>}
 */
export async function getUserDetail(userId) {
  return apiRequest(`/admin/users/${userId}`);
}

/**
 * 更新用户信息（管理员）
 * @param {string} userId - 用户 ID
 * @param {object} data - 更新数据
 * @param {string} [data.username] - 新用户名
 * @param {string} [data.email] - 新邮箱
 * @param {string} [data.role] - 新角色（user/admin）
 * @returns {Promise<{ok: boolean, data?: {user: object}}>}
 */
export async function updateUser(userId, data) {
  return apiRequest(`/admin/users/${userId}`, {
    method: 'PATCH',
    body: data,
  });
}

/**
 * 删除用户（管理员）
 * @param {string} userId - 用户 ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteUser(userId) {
  return apiRequest(`/admin/users/${userId}`, {
    method: 'DELETE',
  });
}

/**
 * 重置用户密码（管理员）
 * @param {string} userId - 用户 ID
 * @param {string} newPassword - 新密码
 * @returns {Promise<{ok: boolean}>}
 */
export async function resetUserPassword(userId, newPassword) {
  return apiRequest(`/admin/users/${userId}/reset-password`, {
    method: 'POST',
    body: { newPassword },
  });
}

// ============================================================================
// 二、密钥管理接口
// ============================================================================

/**
 * 批量生成密钥
 * @param {object} params - 生成参数
 * @param {number} params.count - 生成数量（1-200）
 * @param {string} [params.keyType='paid'] - 密钥类型
 * @param {number} [params.expireDays] - 过期天数（不传表示永久）
 * @param {string} [params.prefix='FAT'] - 密钥前缀
 * @returns {Promise<{ok: boolean, data?: {keys: Array<{id: string, key: string, keyType: string, expiresAt: string}>}}>}
 */
export async function batchGenerateKeys({ count, keyType = 'paid', expireDays, prefix = 'FAT' }) {
  return apiRequest('/admin/license-keys/batch', {
    method: 'POST',
    body: { count, keyType, expireDays, prefix },
  });
}

/**
 * 获取密钥列表
 * @param {object} params - 查询参数
 * @param {boolean} [params.is_used] - 过滤已使用/未使用
 * @param {string} [params.key_type] - 过滤密钥类型
 * @param {number} [params.offset=0] - 分页偏移量
 * @param {number} [params.limit=20] - 每页数量
 * @returns {Promise<{ok: boolean, data?: {items: Array, offset: number, limit: number, total: number}}>}
 */
export async function listLicenseKeys({ is_used, key_type, offset = 0, limit = 20 } = {}) {
  const params = new URLSearchParams();
  if (is_used !== undefined) params.append('is_used', is_used);
  if (key_type) params.append('key_type', key_type);
  params.append('offset', offset);
  params.append('limit', limit);

  return apiRequest(`/admin/license-keys?${params.toString()}`);
}

/**
 * 获取密钥详情
 * @param {string} keyId - 密钥 ID
 * @returns {Promise<{ok: boolean, data?: object}>}
 */
export async function getLicenseKeyDetail(keyId) {
  return apiRequest(`/admin/license-keys/${keyId}`);
}

/**
 * 删除密钥
 * @param {string} keyId - 密钥 ID
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteLicenseKey(keyId) {
  return apiRequest(`/admin/license-keys/${keyId}`, {
    method: 'DELETE',
  });
}

/**
 * 验证密钥（普通用户使用）
 * @param {string} key - 密钥明文
 * @param {boolean} consume - 是否消费该密钥（true表示激活）
 * @returns {Promise<{ok: boolean, data?: {ok: boolean}}>}
 */
export async function verifyKey(key, consume = false) {
  return apiRequest('/admin/verify-key', {
    method: 'POST',
    body: { key, consume },
  });
}
