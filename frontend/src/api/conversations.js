// src/api/conversations.js
const BASE_URL = "http://localhost:8000/api/v1"; // 用 localhost，保证 Cookie 同站

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
    throw new Error(msg);
  }
  return data?.data ?? data;
}

/** 
 * listConversations
 * 返回：Array<{ id, title, createdAt }>
 */
export async function listConversations() {
  const d = await api(`/conversations?offset=0&limit=100`);
  const items = (d.items || []).map(c => ({
    id: c.id,
    title: c.title || "",
    createdAt: c.startedAt ? Date.parse(c.startedAt) : Date.now(),
  }));
  return items; // ← 兼容 mockDB：直接是数组
}

/** 
 * createConversation({ title? })
 * 返回：{ id, title, createdAt, segments: [] }
 */
export async function createConversation({ title } = {}) {
  const d = await api(`/conversations`, { method: "POST", body: { title } });
  return {
    id: d.id,
    title: d.title || "",
    createdAt: d.createdAtMs ?? Date.now(),
    segments: [],
  }; // ← 兼容 mockDB：直接对象
}

/** 
 * getConversation(id) / loadConversation(id)
 * 返回：{ id, title, createdAt, segments: [...] }
 */
export async function getConversation(id) {
  const d = await api(`/conversations/${id}`);
  const conv = d.conversation || {};
  const segments = (d.transcripts || []).map(t => ({
    id: `s_${t.seq}`,
    start: t.startMs ?? Date.now(),
    end: t.endMs ?? Date.now(),
    transcript: t.text || "",
    audioUrl: t.audioUrl || null,
  }));
  return {
    id: conv.id,
    title: conv.title || "",
    createdAt: conv.startedAt ? Date.parse(conv.startedAt) : Date.now(),
    segments,
  };
}

// 兼容旧命名
export const loadConversation = getConversation;

/** 
 * renameConversation(id, title)
 * 返回：true
 */
export async function renameConversation(id, title) {
  await api(`/conversations/${id}`, { method: "PATCH", body: { title } });
  return true; // ← 兼容 mockDB
}

/** 
 * deleteConversation(id)
 * 返回：true
 */
export async function deleteConversation(id) {
  await api(`/conversations/${id}`, { method: "DELETE" });
  return true; // ← 兼容 mockDB
}

/** 
 * appendSegment(id, seg)
 * seg: { start, end, transcript, audioUrl }
 * 返回：{ id, start, end, transcript, audioUrl }
 */
export async function appendSegment(id, seg) {
  const d = await api(`/conversations/${id}/segments`, {
    method: "POST",
    body: {
      startMs: seg.start ?? null,
      endMs: seg.end ?? null,
      text: seg.transcript ?? "",
      audioUrl: seg.audioUrl ?? null,
    },
  });
  return {
    id: d.id,
    start: d.startMs ?? Date.now(),
    end: d.endMs ?? Date.now(),
    transcript: d.text || "",
    audioUrl: d.audioUrl || null,
  }; // ← 兼容 mockDB
}
