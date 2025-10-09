// src/api/auth.js

export async function login({ email, password }) {
  await new Promise((res) => setTimeout(res, 700));
  if (email.includes("fail")) {
    return { ok: false, message: "Invalid credentials (mock)" };
  }
  return { ok: true, token: "mock-token-123" };
}
