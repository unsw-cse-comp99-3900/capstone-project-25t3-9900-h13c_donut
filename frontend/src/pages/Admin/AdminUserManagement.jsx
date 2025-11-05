// frontend/src/pages/Admin/AdminUserManagement.jsx
// User Management Page

import React, { useState, useEffect } from 'react';
import { listUsers, updateUser, deleteUser, resetUserPassword } from '../../api/admin.js';
import styles from './AdminUserManagement.module.css';

export default function AdminUserManagement() {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const pageSize = 20;

  // Edit modal state
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
  });

  // Delete confirmation modal
  const [deletingUser, setDeletingUser] = useState(null);

  // Reset password modal
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  // Load user list
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
      setError(result.message || 'Failed to load user list');
    }

    setLoading(false);
  };

  // Initial load - Load all users on component mount
  useEffect(() => {
    loadUsers(1, '');
  }, []);

  // Search handler
  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    loadUsers(1, query);
  };

  // Open edit modal
  const openEditModal = (user) => {
    setEditingUser(user);
    setEditForm({
      username: user.username,
      email: user.email || '',
    });
  };

  // Close edit modal
  const closeEditModal = () => {
    setEditingUser(null);
    setEditForm({ username: '', email: '' });
  };

  // Submit edit
  const handleEditSubmit = async () => {
    if (!editForm.username.trim()) {
      alert('Username cannot be empty');
      return;
    }

    const result = await updateUser(editingUser.id, {
      username: editForm.username,
      email: editForm.email || null,
    });

    if (result.ok) {
      alert('User information updated successfully');
      closeEditModal();
      loadUsers(currentPage, searchQuery);
    } else {
      alert(`Update failed: ${result.message}`);
    }
  };

  // Open delete confirmation
  const openDeleteConfirm = (user) => {
    setDeletingUser(user);
  };

  // Close delete confirmation
  const closeDeleteConfirm = () => {
    setDeletingUser(null);
  };

  // Confirm delete
  const handleDeleteConfirm = async () => {
    const result = await deleteUser(deletingUser.id);

    if (result.ok) {
      alert('User deleted successfully');
      closeDeleteConfirm();
      loadUsers(currentPage, searchQuery);
    } else {
      alert(`Delete failed: ${result.message}`);
    }
  };

  // Open reset password modal
  const openResetPasswordModal = (user) => {
    setResetPasswordUser(user);
    setNewPassword('');
  };

  // Close reset password modal
  const closeResetPasswordModal = () => {
    setResetPasswordUser(null);
    setNewPassword('');
  };

  // Submit reset password
  const handleResetPasswordSubmit = async () => {
    if (!newPassword || newPassword.length < 6) {
      alert('Password must be at least 6 characters');
      return;
    }

    const result = await resetUserPassword(resetPasswordUser.id, newPassword);

    if (result.ok) {
      alert('Password reset successfully');
      closeResetPasswordModal();
    } else {
      alert(`Reset failed: ${result.message}`);
    }
  };

  // Pagination handling
  const totalPages = Math.ceil(totalUsers / pageSize);
  const canPrevPage = currentPage > 1;
  const canNextPage = currentPage < totalPages;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>User Management</h2>
        <div className={styles.searchBox}>
          <input
            type="text"
            placeholder="Search users (Username/Email)"
            value={searchQuery}
            onChange={handleSearch}
            className={styles.searchInput}
          />
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>Loading...</div>
      ) : (
        <>
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Created At</th>
                  <th>Actions</th>
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
                        {user.role === 'admin' ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleString('en-US')}</td>
                    <td className={styles.actions}>
                      <button
                        className={styles.btnEdit}
                        onClick={() => openEditModal(user)}
                      >
                        Edit
                      </button>
                      <button
                        className={styles.btnReset}
                        onClick={() => openResetPasswordModal(user)}
                      >
                        Reset Password
                      </button>
                      <button
                        className={styles.btnDelete}
                        onClick={() => openDeleteConfirm(user)}
                      >
                        Delete
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
              Previous
            </button>
            <span className={styles.paginationInfo}>
              Page {currentPage} / {totalPages} (Total {totalUsers})
            </span>
            <button
              disabled={!canNextPage}
              onClick={() => loadUsers(currentPage + 1, searchQuery)}
              className={styles.paginationBtn}
            >
              Next
            </button>
          </div>
        </>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>Edit User</h3>
            <div className={styles.formGroup}>
              <label>Username</label>
              <input
                type="text"
                value={editForm.username}
                onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Email</label>
              <input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                className={styles.input}
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSubmit} onClick={handleEditSubmit}>
                Submit
              </button>
              <button className={styles.btnCancel} onClick={closeEditModal}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>Confirm Delete</h3>
            <p>Are you sure you want to delete user <strong>{deletingUser.username}</strong>?</p>
            <p className={styles.warning}>This action cannot be undone!</p>
            <div className={styles.modalActions}>
              <button className={styles.btnDelete} onClick={handleDeleteConfirm}>
                Confirm Delete
              </button>
              <button className={styles.btnCancel} onClick={closeDeleteConfirm}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {resetPasswordUser && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>Reset Password</h3>
            <p>Set new password for user <strong>{resetPasswordUser.username}</strong></p>
            <div className={styles.formGroup}>
              <label>New Password (at least 6 characters)</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={styles.input}
                placeholder="Enter new password"
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSubmit} onClick={handleResetPasswordSubmit}>
                Confirm Reset
              </button>
              <button className={styles.btnCancel} onClick={closeResetPasswordModal}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
