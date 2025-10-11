/**
 * Conversations API (user-scoped, in-memory/localStorage first)
 *
 * USE_LOCAL_STORAGE = true → store as { [userId]: Conversation[] } in key "convos_v2".
 */

const USE_LOCAL_STORAGE = true;
const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getUserId() {
  return (
    localStorage.getItem("authUserId") ||
    sessionStorage.getItem("authUserId") ||
    "anon"
  );
}

/* ------------ Local helpers (user-scoped) ------------ */
const LKEY = "convos_v2";
function readAll() {
  try { return JSON.parse(localStorage.getItem(LKEY)) || {}; }
  catch { return {}; }
}
function writeAll(bag) { localStorage.setItem(LKEY, JSON.stringify(bag)); }
function loadForUser(uid) {
  const bag = readAll();
  return Array.isArray(bag[uid]) ? bag[uid] : [];
}
function saveForUser(uid, convs) {
  const bag = readAll();
  bag[uid] = convs;
  writeAll(bag);
}

export async function listConversations() {
  if (USE_LOCAL_STORAGE) return loadForUser(getUserId());
  const r = await fetch(`${API}/conversations`, { credentials: "include" });
  if (!r.ok) throw new Error("Failed to list conversations");
  return r.json();
}

export async function createConversation(payload = {}) {
  if (USE_LOCAL_STORAGE) {
    const uid = getUserId();
    const ts = Date.now();
    const id = "c_" + ts + "_" + Math.random().toString(36).slice(2, 7); // 更稳的唯一值
    const title = payload.title || `New Chat ${new Date(ts).toLocaleString()}`;
    const conv = { id, title, createdAt: ts, segments: [] };
    const all = loadForUser(uid);
    // 防重复：若同 id 已存在则不写入
    if (!all.some((x) => x.id === id)) {
      saveForUser(uid, [conv, ...all]);
    }
    return conv;
  }
  const r = await fetch(`${API}/conversations`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("Failed to create conversation");
  return r.json();
}

export async function loadConversation(id) {
  if (USE_LOCAL_STORAGE) {
    const uid = getUserId();
    const all = loadForUser(uid);
    return all.find((c) => c.id === id) || null;
  }
  const r = await fetch(`${API}/conversations/${id}`, { credentials: "include" });
  if (!r.ok) throw new Error("Failed to load conversation");
  return r.json();
}

export async function renameConversation(id, title) {
  if (USE_LOCAL_STORAGE) {
    const uid = getUserId();
    const all = loadForUser(uid);
    const idx = all.findIndex((c) => c.id === id);
    if (idx >= 0) {
      all[idx] = { ...all[idx], title: title || all[idx].title };
      saveForUser(uid, all);
    }
    return { ok: true };
  }
  const r = await fetch(`${API}/conversations/${id}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return { ok: r.ok };
}

export async function appendSegment(conversationId, seg) {
  if (USE_LOCAL_STORAGE) {
    const uid = getUserId();
    const all = loadForUser(uid);
    const idx = all.findIndex((c) => c.id === conversationId);
    if (idx >= 0) {
      const conv = all[idx];
      conv.segments = [...(conv.segments || []), seg];
      all[idx] = conv;
      saveForUser(uid, all);
    }
    return seg;
  }
  const r = await fetch(`${API}/conversations/${conversationId}/segments`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(seg),
  });
  if (!r.ok) throw new Error("Failed to append segment");
  return r.json();
}

export async function deleteConversation(id) {
  if (USE_LOCAL_STORAGE) {
    const uid = getUserId();
    const all = loadForUser(uid);
    saveForUser(uid, all.filter((c) => c.id !== id));
    return { ok: true };
  }
  const r = await fetch(`${API}/conversations/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  return { ok: r.ok };
}
