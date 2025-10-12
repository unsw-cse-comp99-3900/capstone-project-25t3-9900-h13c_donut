/**
 * In-Memory Mock DB (singleton, per-user isolation)
 * - Pure in-memory (lost on refresh)
 * - Data is scoped by userId so each user only sees their own conversations
 * - Shapes mimic a future backend
 */

function uid(prefix = "") {
  return prefix + Math.random().toString(36).slice(2, 8) + Date.now().toString(36);
}

// ===== In-memory stores =====
const __users = []; // { id, username, email, password }
const __convIndexByUser = new Map(); // userId -> { list: [{id,title,createdAt}], map: Map(id -> {id,title,createdAt,segments:[]}) }

// helpers
function ensureUserConvStore(userId) {
  if (!__convIndexByUser.has(userId)) {
    __convIndexByUser.set(userId, { list: [], map: new Map() });
  }
  return __convIndexByUser.get(userId);
}

// Seed demo data
(function seed() {
  const demo = {
    id: uid("u_"),
    username: "demo",
    email: "demo@example.com",
    password: "demo123",
  };
  __users.push(demo);

  const store = ensureUserConvStore(demo.id);
  const conv = {
    id: uid("c_"),
    title: "New Chat " + new Date().toLocaleString(),
    createdAt: Date.now(),
    segments: [],
  };
  store.list.unshift({ id: conv.id, title: conv.title, createdAt: conv.createdAt });
  store.map.set(conv.id, conv);
})();

// ===== Users =====
function findUserByEmail(email) {
  const e = String(email || "").toLowerCase();
  return __users.find((u) => (u.email || "").toLowerCase() === e) || null;
}

function findUserByUsername(username) {
  const n = String(username || "").toLowerCase();
  return __users.find((u) => (u.username || "").toLowerCase() === n) || null;
}

function verifyLoginByUsername(username, password) {
  const u = findUserByUsername(username);
  if (!u) return null;
  if (u.password !== password) return null;
  return u;
}

function createUser({ username, email, password }) {
  const user = { id: uid("u_"), username, email, password };
  __users.push(user);
  return user;
}

function verifyUserForReset(username, email) {
  const u = findUserByUsername(username);
  if (!u) return null;
  if ((u.email || "").toLowerCase() !== String(email || "").toLowerCase()) return null;
  return u; // both match
}

function updateUserPassword(userId, newPassword) {
  const u = __users.find((x) => x.id === userId);
  if (!u) return false;
  u.password = String(newPassword || "");
  return true;
}

// ===== Conversations (per user) =====
function listConversations(userId) {
  const store = ensureUserConvStore(userId);
  return store.list.map((c) => ({ ...c }));
}

function createConversation(userId, { title } = {}) {
  const store = ensureUserConvStore(userId);
  const ts = Date.now();
  const conv = {
    id: uid("c_"),
    title: title || `New Chat ${new Date(ts).toLocaleString()}`,
    createdAt: ts,
    segments: [],
  };
  store.list.unshift({ id: conv.id, title: conv.title, createdAt: conv.createdAt });
  store.map.set(conv.id, conv);
  return { id: conv.id, title: conv.title, createdAt: conv.createdAt, segments: [] };
}

function getConversation(userId, id) {
  const store = ensureUserConvStore(userId);
  const c = store.map.get(id);
  if (!c) return null;
  return {
    id: c.id,
    title: c.title,
    createdAt: c.createdAt,
    segments: c.segments.map((s) => ({ ...s })),
  };
}

function renameConversation(userId, id, title) {
  const store = ensureUserConvStore(userId);
  const c = store.map.get(id);
  if (!c) return false;
  c.title = title || c.title;
  const idx = store.list.findIndex((x) => x.id === id);
  if (idx >= 0) store.list[idx] = { ...store.list[idx], title: c.title };
  return true;
}

function appendSegment(userId, conversationId, seg) {
  const store = ensureUserConvStore(userId);
  const c = store.map.get(conversationId);
  if (!c) return null;
  const copy = {
    id: seg.id || uid("s_"),
    start: seg.start ?? Date.now(),
    end: seg.end ?? Date.now(),
    transcript: seg.transcript || "",
    audioUrl: seg.audioUrl || null,
  };
  c.segments.push(copy);
  return { ...copy };
}

// ===== Utils =====
function resetAll() {
  __users.splice(0, __users.length);
  __convIndexByUser.clear();
}

export const mockDB = {
  // users
  findUserByEmail,
  findUserByUsername,
  verifyLoginByUsername,
  createUser,
  verifyUserForReset,
  updateUserPassword,
  // conversations (per-user)
  listConversations,
  createConversation,
  getConversation,
  renameConversation,
  appendSegment,
  // utils
  resetAll,
};
