// src/api/auth.js
const BASE_URL = "http://localhost:8000/api/v1";


async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include", // 关键：带上 HttpOnly Cookie
  });
  let data = null;
  try { data = await res.json(); } catch (_) {}
  if (!res.ok || (data && data.success === false)) {
    const msg = data?.error?.message || data?.detail || `HTTP ${res.status}`;
    return { ok: false, message: msg, code: data?.error?.code };
  }
  return { ok: true, data: data?.data ?? data };
}

/**
 * Login with username + password
 */
export async function login({ username, password }) {
  const r = await api("/auth/login", { method: "POST", body: { username, password } });
  if (!r.ok) return r;
  const { user, accessToken } = r.data;
  return { ok: true, token: accessToken, user: { id: user.id, username: user.username, email: user.email ?? "" } };
}

/**
 * Register (backend)
 * - unique username
 * - unique email
 */
export async function register({ username, email, password }) {
  const r = await api("/auth/register", { method: "POST", body: { username, email, password } });
  if (!r.ok) return r;
  const { id, username: un, email: em } = r.data;
  return { ok: true, message: "Registration successful", user: { id, username: un, email: em || "" } };
}

/**
 * Check if username+email exists for password reset
 */
export async function checkUserForReset({ username, email }) {
  const r = await api("/auth/check-reset", { method: "POST", body: { username, email } });
  if (!r.ok) return r;
  return { ok: true, userId: r.data.userId };
}

/**
 * Reset password (after verification)
 */
export async function resetPassword({ userId, newPassword }) {
  const r = await api("/auth/reset-password", { method: "POST", body: { userId, newPassword } });
  return r.ok ? { ok: true, message: "Password updated successfully" } : r;
}

/**
 * Change password for logged-in user
 */
export async function changePassword({ userId, newPassword }) {
  // 后端根据 Cookie/JWT 验证当前用户，无需传 userId，但保持前端签名不变
  const r = await api("/auth/change-password", { method: "POST", body: { newPassword } });
  return r.ok ? { ok: true } : r;
}
