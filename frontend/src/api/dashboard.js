// src/api/dashboard.js
const BASE_URL = "http://localhost:8000/api/v1";


async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
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
 * verify upgrade key (backend)
 * 兼容原逻辑：key === "SECRET123" -> ok:true，否则 ok:false
 */
export async function verifyUpgradeKey(key) {
  const r = await api("/admin/verify-key", { method: "POST", body: { key } });
  return r.ok ? { ok: !!r.data?.ok } : { ok: false, message: r.message };
}
