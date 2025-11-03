// frontend/src/pages/Admin/AdminUserManagement.jsx
// 用户管理页面

import React, { useState, useEffect } from 'react';
import { listUsers, updateUser, deleteUser, resetUserPassword } from '../../api/admin.js';
import styles from './AdminUserManagement.module.css';

export default function AdminUserManagement() {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const pageSize = 20;

  // 编辑弹窗状态
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
    role: 'user',
  });

  // 删除确认弹窗
  const [deletingUser, setDeletingUser] = useState(null);

  // 重置密码弹窗
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  // 加载用户列表
  const loadUsers = async (page = 1, query = '') => {
    setLoading(true);
    setError('');

    const offset = (page - 1) * pageSize;
    const result = await listUsers({ q: query, offset, limit: pageSize });

    if (result.ok) {
      setUsers(result.data.items);
      setTotalUsers(result.data.total);
      setCurrentPage(page);
    } else {
      setError(result.message || '加载用户列表失败');
    }

    setLoading(false);
  };

  // 初始加载
  useEffect(() => {
    loadUsers(1, searchQuery);
  }, []);

  // 搜索处理
  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    loadUsers(1, query);
  };

  // 打开编辑弹窗
  const openEditModal = (user) => {
    setEditingUser(user);
    setEditForm({
      username: user.username,
      email: user.email || '',
      role: user.role,
    });
  };

  // 关闭编辑弹窗
  const closeEditModal = () => {
    setEditingUser(null);
    setEditForm({ username: '', email: '', role: 'user' });
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    if (!editForm.username.trim()) {
      alert('用户名不能为空');
      return;
    }

    const result = await updateUser(editingUser.id, {
      username: editForm.username,
      email: editForm.email || null,
      role: editForm.role,
    });

    if (result.ok) {
      alert('用户信息更新成功');
      closeEditModal();
      loadUsers(currentPage, searchQuery);
    } else {
      alert(`更新失败: ${result.message}`);
    }
  };

  // 打开删除确认
  const openDeleteConfirm = (user) => {
    setDeletingUser(user);
  };

  // 关闭删除确认
  const closeDeleteConfirm = () => {
    setDeletingUser(null);
  };

  // 确认删除
  const handleDeleteConfirm = async () => {
    const result = await deleteUser(deletingUser.id);

    if (result.ok) {
      alert('用户删除成功');
      closeDeleteConfirm();
      loadUsers(currentPage, searchQuery);
    } else {
      alert(`删除失败: ${result.message}`);
    }
  };

  // 打开重置密码弹窗
  const openResetPasswordModal = (user) => {
    setResetPasswordUser(user);
    setNewPassword('');
  };

  // 关闭重置密码弹窗
  const closeResetPasswordModal = () => {
    setResetPasswordUser(null);
    setNewPassword('');
  };

  // 提交重置密码
  const handleResetPasswordSubmit = async () => {
    if (!newPassword || newPassword.length < 6) {
      alert('密码长度至少6位');
      return;
    }

    const result = await resetUserPassword(resetPasswordUser.id, newPassword);

    if (result.ok) {
      alert('密码重置成功');
      closeResetPasswordModal();
    } else {
      alert(`重置失败: ${result.message}`);
    }
  };

  // 分页处理
  const totalPages = Math.ceil(totalUsers / pageSize);
  const canPrevPage = currentPage > 1;
  const canNextPage = currentPage < totalPages;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>用户管理</h2>
        <div className={styles.searchBox}>
          <input
            type="text"
            placeholder="搜索用户（用户名/Email）"
            value={searchQuery}
            onChange={handleSearch}
            className={styles.searchInput}
          />
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : (
        <>
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className={styles.idCell}>{user.id.slice(0, 8)}...</td>
                    <td>{user.username}</td>
                    <td>{user.email || '-'}</td>
                    <td>
                      <span className={user.role === 'admin' ? styles.badgeAdmin : styles.badgeUser}>
                        {user.role === 'admin' ? '管理员' : '用户'}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleString('zh-CN')}</td>
                    <td className={styles.actions}>
                      <button
                        className={styles.btnEdit}
                        onClick={() => openEditModal(user)}
                      >
                        编辑
                      </button>
                      <button
                        className={styles.btnReset}
                        onClick={() => openResetPasswordModal(user)}
                      >
                        重置密码
                      </button>
                      <button
                        className={styles.btnDelete}
                        onClick={() => openDeleteConfirm(user)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.pagination}>
            <button
              disabled={!canPrevPage}
              onClick={() => loadUsers(currentPage - 1, searchQuery)}
              className={styles.paginationBtn}
            >
              上一页
            </button>
            <span className={styles.paginationInfo}>
              第 {currentPage} / {totalPages} 页（共 {totalUsers} 条）
            </span>
            <button
              disabled={!canNextPage}
              onClick={() => loadUsers(currentPage + 1, searchQuery)}
              className={styles.paginationBtn}
            >
              下一页
            </button>
          </div>
        </>
      )}

      {/* 编辑用户弹窗 */}
      {editingUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>编辑用户</h3>
            <div className={styles.formGroup}>
              <label>用户名</label>
              <input
                type="text"
                value={editForm.username}
                onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>邮箱</label>
              <input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>角色</label>
              <select
                value={editForm.role}
                onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                className={styles.select}
              >
                <option value="user">用户</option>
                <option value="admin">管理员</option>
              </select>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSubmit} onClick={handleEditSubmit}>
                提交
              </button>
              <button className={styles.btnCancel} onClick={closeEditModal}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认弹窗 */}
      {deletingUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>确认删除</h3>
            <p>确定删除用户 <strong>{deletingUser.username}</strong> 吗？</p>
            <p className={styles.warning}>删除后不可恢复！</p>
            <div className={styles.modalActions}>
              <button className={styles.btnDelete} onClick={handleDeleteConfirm}>
                确认删除
              </button>
              <button className={styles.btnCancel} onClick={closeDeleteConfirm}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 重置密码弹窗 */}
      {resetPasswordUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>重置密码</h3>
            <p>为用户 <strong>{resetPasswordUser.username}</strong> 设置新密码</p>
            <div className={styles.formGroup}>
              <label>新密码（至少6位）</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={styles.input}
                placeholder="请输入新密码"
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSubmit} onClick={handleResetPasswordSubmit}>
                确认重置
              </button>
              <button className={styles.btnCancel} onClick={closeResetPasswordModal}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
