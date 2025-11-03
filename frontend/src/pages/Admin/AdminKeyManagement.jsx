// frontend/src/pages/Admin/AdminKeyManagement.jsx
// 密钥管理页面 - 批量生成密钥

import React, { useState } from 'react';
import { batchGenerateKeys } from '../../api/admin.js';
import styles from './AdminKeyManagement.module.css';

export default function AdminKeyManagement() {
  const [generating, setGenerating] = useState(false);
  const [generatedKeys, setGeneratedKeys] = useState([]);
  const [error, setError] = useState('');

  // 表单状态
  const [formData, setFormData] = useState({
    count: 1,
    keyType: 'paid',
    expireDays: '',
    prefix: 'FAT',
  });

  // 处理表单输入
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  // 生成密钥
  const handleGenerate = async () => {
    setError('');

    // 验证输入
    const count = parseInt(formData.count, 10);
    if (isNaN(count) || count < 1 || count > 200) {
      setError('生成数量必须在 1-200 之间');
      return;
    }

    const expireDays = formData.expireDays ? parseInt(formData.expireDays, 10) : null;
    if (expireDays !== null && (isNaN(expireDays) || expireDays < 1 || expireDays > 3650)) {
      setError('过期天数必须在 1-3650 之间');
      return;
    }

    if (!formData.prefix || formData.prefix.trim().length === 0) {
      setError('密钥前缀不能为空');
      return;
    }

    setGenerating(true);

    const result = await batchGenerateKeys({
      count,
      keyType: formData.keyType,
      expireDays,
      prefix: formData.prefix.trim().toUpperCase(),
    });

    setGenerating(false);

    if (result.ok) {
      setGeneratedKeys(result.data.keys);
      setError('');
    } else {
      setError(result.message || '生成密钥失败');
    }
  };

  // 复制单个密钥
  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key).then(() => {
      alert('密钥已复制到剪贴板');
    }).catch(() => {
      alert('复制失败，请手动复制');
    });
  };

  // 复制所有密钥
  const handleCopyAll = () => {
    const allKeys = generatedKeys.map(item => item.key).join('\n');
    navigator.clipboard.writeText(allKeys).then(() => {
      alert(`已复制所有 ${generatedKeys.length} 个密钥到剪贴板`);
    }).catch(() => {
      alert('复制失败，请手动复制');
    });
  };

  // 导出为文本文件
  const handleExport = () => {
    const content = generatedKeys.map(item => {
      const expiry = item.expiresAt ? ` (过期时间: ${new Date(item.expiresAt).toLocaleString('zh-CN')})` : ' (永久有效)';
      return `${item.key}${expiry}`;
    }).join('\n');

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `license-keys-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 清除结果
  const handleClear = () => {
    setGeneratedKeys([]);
    setError('');
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>批量生成付费密钥</h2>
        <p className={styles.subtitle}>生成的密钥仅显示一次，请及时保存</p>
      </div>

      <div className={styles.form}>
        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label>生成数量 *</label>
            <input
              type="number"
              name="count"
              value={formData.count}
              onChange={handleInputChange}
              min="1"
              max="200"
              className={styles.input}
              placeholder="1-200"
            />
            <span className={styles.hint}>最多生成 200 个密钥</span>
          </div>

          <div className={styles.formGroup}>
            <label>密钥类型</label>
            <select
              name="keyType"
              value={formData.keyType}
              onChange={handleInputChange}
              className={styles.select}
            >
              <option value="paid">付费模型 (paid)</option>
              <option value="trial">试用 (trial)</option>
              <option value="promotion">促销 (promotion)</option>
            </select>
          </div>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label>过期天数</label>
            <input
              type="number"
              name="expireDays"
              value={formData.expireDays}
              onChange={handleInputChange}
              min="1"
              max="3650"
              className={styles.input}
              placeholder="留空表示永久有效"
            />
            <span className={styles.hint}>留空表示永久有效，最长 3650 天（10年）</span>
          </div>

          <div className={styles.formGroup}>
            <label>密钥前缀 *</label>
            <input
              type="text"
              name="prefix"
              value={formData.prefix}
              onChange={handleInputChange}
              maxLength="8"
              className={styles.input}
              placeholder="FAT"
            />
            <span className={styles.hint}>用于标识渠道，最多 8 个字符</span>
          </div>
        </div>

        <div className={styles.formActions}>
          <button
            className={styles.btnGenerate}
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? '生成中...' : '生成密钥'}
          </button>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {generatedKeys.length > 0 && (
        <div className={styles.results}>
          <div className={styles.resultsHeader}>
            <h3>生成成功！共 {generatedKeys.length} 个密钥</h3>
            <div className={styles.resultsActions}>
              <button className={styles.btnCopyAll} onClick={handleCopyAll}>
                复制全部
              </button>
              <button className={styles.btnExport} onClick={handleExport}>
                导出为文本
              </button>
              <button className={styles.btnClear} onClick={handleClear}>
                清除
              </button>
            </div>
          </div>

          <div className={styles.warning}>
            ⚠️ 密钥仅显示一次，离开页面后无法再次查看明文！请务必保存。
          </div>

          <div className={styles.keysContainer}>
            {generatedKeys.map((item, index) => (
              <div key={item.id} className={styles.keyItem}>
                <div className={styles.keyIndex}>{index + 1}</div>
                <div className={styles.keyContent}>
                  <div className={styles.keyText}>{item.key}</div>
                  <div className={styles.keyMeta}>
                    <span className={styles.keyType}>{item.keyType}</span>
                    {item.expiresAt ? (
                      <span className={styles.keyExpiry}>
                        过期时间: {new Date(item.expiresAt).toLocaleString('zh-CN')}
                      </span>
                    ) : (
                      <span className={styles.keyPermanent}>永久有效</span>
                    )}
                  </div>
                </div>
                <button
                  className={styles.btnCopy}
                  onClick={() => handleCopyKey(item.key)}
                >
                  复制
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={styles.info}>
        <h4>使用说明</h4>
        <ul>
          <li>每个密钥仅支持激活一次，激活后自动失效</li>
          <li>密钥格式：<code>{formData.prefix}-XXXX-XXXX-XXXX-XXXX</code></li>
          <li>生成后立即保存，系统不会存储明文密钥</li>
          <li>建议定期检查密钥使用情况，及时清理过期密钥</li>
        </ul>
      </div>
    </div>
  );
}
