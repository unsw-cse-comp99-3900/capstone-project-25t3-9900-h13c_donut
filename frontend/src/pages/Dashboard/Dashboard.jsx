import React, { useState } from "react";
import styles from "./Dashboard.module.css";
import { verifyUpgradeKey } from "../../api/dashboard";

function Dashboard() {
  const [modelUnlocked, setModelUnlocked] = useState(false);
  const [selectedModel, setSelectedModel] = useState("modelI");
  const [selectedAccent, setSelectedAccent] = useState("Accent I");

  const handleUpgradeModel = async () => {
    const key = prompt("Please enter the upgrade key:");
    if (!key) return;

    const res = await verifyUpgradeKey(key); // 后端接口占位
    if (res.ok) {
      alert("Upgrade successful! Model II unlocked.");
      setModelUnlocked(true);
    } else {
      alert("Invalid key!");
    }
  };

  const handleChangePassword = () => {
    const newPassword = prompt("Enter new password:");
    if (newPassword) {
      alert("Password changed (mock)");
    }
  };

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      alert("Logged out (mock)");
    }
  };

  const handleStartRecording = () => {
    alert("Recording started (mock)");
  };

  return (
    <div className={styles.container}>
      {/* Left Sidebar */}
      <div className={styles.sidebar}>
        <div className={styles.top}>
          <button className={styles.settingsButton}>⚙️</button>
          <div className={styles.dropdown}>
            <div onClick={handleUpgradeModel}>Upgrade Model</div>
            <div onClick={handleChangePassword}>Change Password</div>
            <div onClick={handleLogout}>Log Out</div>
          </div>
        </div>
        <div className={styles.bottom}>
          <select
            value={selectedAccent}
            onChange={(e) => setSelectedAccent(e.target.value)}
          >
            <option>Accent I</option>
            <option>Accent II</option>
            <option>Accent III</option>
            <option>Accent IV</option>
            <option>Accent V</option>
          </select>
        </div>
      </div>

      {/* Right Main */}
      <div className={styles.main}>
        <div className={styles.modelSelect}>
          <label>Model: </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={!modelUnlocked && selectedModel === "modelII"}
          >
            <option value="modelI">Model I</option>
            <option value="modelII">Model II</option>
          </select>
        </div>
        <div className={styles.controls}>
          <button onClick={() => alert("Volume control (mock) 🔊")}>🔊</button>
          <button onClick={handleStartRecording}>▶️ Start</button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
