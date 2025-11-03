// frontend/src/pages/Admin/AdminDashboard.jsx
// 管理员仪表盘 - 入口页面，包含两个按钮切换到不同管理页面

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminUserManagement from './AdminUserManagement.jsx';
import AdminKeyManagement from './AdminKeyManagement.jsx';
import styles from './AdminDashboard.module.css';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('users'); // 'users' or 'keys'

  // 退出登录
  const handleLogout = () => {
    // 清除本地存储
    localStorage.removeItem('authUserId');
    localStorage.removeItem('authUsername');
    localStorage.removeItem('authUserRole');

    // 跳转到登录页
    navigate('/login');
  };

  return (
    <div className={styles.container}>
      {/* 顶部导航栏 */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>管理员仪表盘</h1>
          <span className={styles.badge}>Admin Dashboard</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.username}>
            {localStorage.getItem('authUsername') || '管理员'}
          </span>
          <button className={styles.btnLogout} onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </header>

      {/* 标签页切换按钮 */}
      <nav className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'users' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <svg className={styles.tabIcon} viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
          </svg>
          用户管理
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'keys' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('keys')}
        >
          <svg className={styles.tabIcon} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
          </svg>
          批量生成付费密钥
        </button>
      </nav>

      {/* 主内容区域 */}
      <main className={styles.main}>
        {activeTab === 'users' ? <AdminUserManagement /> : <AdminKeyManagement />}
      </main>

      {/* 底部标识 */}
      <footer className={styles.footer}>
        <span>Accent 0</span>
      </footer>
    </div>
  );
}
