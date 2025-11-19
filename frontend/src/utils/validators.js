// src/util/validators.js

/**
 * 密码复杂度校验：
 * - 至少 8 位
 * - 至少包含以下四类中的两类：大写字母 / 小写字母 / 数字 / 特殊字符
 */
export function validatePasswordComplexity(pwd) {
  if (!pwd || pwd.length < 8) {
    return "Password must be at least 8 characters long and contain at least two of: uppercase, lowercase, number, special character.";
  }

  const hasLower = /[a-z]/.test(pwd);
  const hasUpper = /[A-Z]/.test(pwd);
  const hasDigit = /[0-9]/.test(pwd);
  const hasSpecial = /[^a-zA-Z0-9]/.test(pwd);

  const typeCount = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;

  if (typeCount < 2) {
    return "Password must contain at least two of: uppercase, lowercase, number, special character.";
  }

  return null; // 通过校验
}

/**
 * 邮箱格式校验
 */
export function validateEmailFormat(email) {
  if (!email) return "Email is required.";

  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email)) return "Please enter a valid email address.";

  return null;
}