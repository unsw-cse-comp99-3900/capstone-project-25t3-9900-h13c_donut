// src/api/auth.js
import { mockDB } from "./mockDB";

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Login with username + password
 */
export async function login({ username, password }) {
  await delay(400);
  if ((username || "").includes("fail")) {
    return { ok: false, message: "Invalid credentials (mock)" };
  }
  const user = mockDB.verifyLoginByUsername(username, password);
  if (!user) return { ok: false, message: "Invalid username or password" };
  const token = "mock-token-" + user.id;
  return {
    ok: true,
    token,
    user: { id: user.id, username: user.username, email: user.email },
  };
}

/**
 * Register (mock)
 * - unique username
 * - unique email
 */
export async function register({ username, email, password }) {
  await delay(600);
  if (!username || !email || !password) return { ok: false, message: "Missing required fields" };
  if (mockDB.findUserByUsername(username)) {
    return { ok: false, code: "USERNAME_EXISTS", message: "Username already exists" };
  }
  if (mockDB.findUserByEmail(email)) {
    return { ok: false, code: "EMAIL_EXISTS", message: "Email already registered" };
  }
  const user = mockDB.createUser({ username, email, password });
  return {
    ok: true,
    message: "Registration successful",
    user: { id: user.id, username: user.username, email: user.email },
  };
}

/**
 * Check if username+email exists for password reset
 */
export async function checkUserForReset({ username, email }) {
  await delay(400);
  const u = mockDB.verifyUserForReset(username, email);
  if (!u) return { ok: false, message: "User not found" };
  return { ok: true, userId: u.id };
}

/**
 * Reset password (after verification)
 */
export async function resetPassword({ userId, newPassword }) {
  await delay(400);
  if (!userId || !newPassword) return { ok: false, message: "Missing parameters" };
  const ok = mockDB.updateUserPassword(userId, newPassword);
  return ok ? { ok: true, message: "Password updated successfully" } : { ok: false, message: "User not found" };
}

/**
 * Change password for logged-in user (simple version:
 * only provide newPassword; verify identity by current session userId)
 */
export async function changePassword({ userId, newPassword }) {
  await delay(400);
  if (!userId || !newPassword) return { ok: false, message: "Missing parameters" };
  const ok = mockDB.updateUserPassword(userId, newPassword);
  return ok ? { ok: true } : { ok: false, message: "User not found" };
}
