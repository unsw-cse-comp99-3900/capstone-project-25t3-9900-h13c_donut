import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./LoginPage.module.css";
import { login } from "../../api/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      alert("Please fill in both fields.");
      return;
    }
    setLoading(true);
    try {
      const resp = await login({ email, password });
      if (resp.ok) {
        navigate("/dashboard");
      } else {
        alert(resp.message || "Login failed.");
      }
    } catch (err) {
      alert(err.message || "Unexpected error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pageWrap}>
      <h1 className={styles.title}>
        Welcome to <span className={styles.colorful}>SystemX!</span>
      </h1>

      <div className={styles.card}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Signing In..." : "Sign In"}
          </button>

          <div className={styles.footer}>
            <span
              className={styles.link}
              onClick={() => navigate("/register")}
            >
              Register
            </span>
            <span
              className={styles.link}
              onClick={() => navigate("/forgot-password")}
            >
              Forget password?
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}
