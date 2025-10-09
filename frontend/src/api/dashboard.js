// src/api/dashboard.js
export async function verifyUpgradeKey(key) {
  // mock: 如果 key === "SECRET123" 返回成功，否则失败
  await new Promise((r) => setTimeout(r, 500)); // 模拟网络延迟
  if (key === "SECRET123") {
    return { ok: true };
  } else {
    return { ok: false };
  }
}
