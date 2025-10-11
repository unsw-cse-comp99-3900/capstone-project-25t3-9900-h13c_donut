// src/api/dashboard.js
export async function verifyUpgradeKey(key) {
  // mock: key === "SECRET123" -> success, else fail
  await new Promise((r) => setTimeout(r, 500));
  if (key === "SECRET123") {
    return { ok: true };
  } else {
    return { ok: false };
  }
}
