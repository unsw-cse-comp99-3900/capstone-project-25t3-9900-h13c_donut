import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Dashboard.module.css";

import { verifyUpgradeKey } from "../../api/dashboard";
import {
  listConversations,
  createConversation,
  loadConversation,
  renameConversation,
  appendSegment,
  deleteConversation,
} from "../../api/conversations";
import { createStreamClient } from "../../api/streamClient";
import { changePassword } from "../../api/auth";

/** ===== Constants ===== */
const ACCENTS = [
  "American English",
  "Australia English",
  "British English",
  "Chinese English",
  "India English",
];
const USE_LOCAL_SPEECH = (import.meta.env.VITE_USE_LOCAL_SPEECH || "1") === "1";

/** Simple eye icon */
function EyeIcon({ open = false }) {
  return open ? (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z" fill="none" stroke="currentColor" strokeWidth="1.8"/>
      <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8"/>
    </svg>
  ) : (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 3l18 18" fill="none" stroke="currentColor" strokeWidth="1.8"/>
      <path d="M10.58 10.58a3 3 0 104.24 4.24M9.88 5.09A10.7 10.7 0 0112 5c7 0 11 7 11 7a17.2 17.2 0 01-3.11 3.88M6.11 7.11A17.2 17.2 0 001 12s4 7 11 7a10.7 10.7 0 003.04-.43" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

/** Title helper */
function titleFrom(text) {
  if (!text) {
    const ts = new Date();
    return `New Chat ${ts.toLocaleDateString()}/${ts.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  }
  const first = (text.split(/(?<=[.!?])\s+/)[0] || text).slice(0, 60);
  const cleaned = first
    .replace(/\s+/g, " ")
    .replace(/[^\p{L}\p{N}\s'’,-]/gu, "")
    .trim();
  if (!cleaned) return "New Chat";
  const titleCased = cleaned.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1));
  return titleCased;
}

export default function Dashboard() {
  const navigate = useNavigate();

  /** ===== user session ===== */
  const userId =
    localStorage.getItem("authUserId") || sessionStorage.getItem("authUserId");
  const username =
    localStorage.getItem("authUsername") ||
    sessionStorage.getItem("authUsername") ||
    "User";

  useEffect(() => {
    if (!userId) navigate("/login", { replace: true });
  }, [userId, navigate]);

  const ACTIVE_KEY = `activeId:${userId || "anon"}`;
  const PAID_UNLOCK_KEY = `paidUnlocked:${userId || "anon"}`;

  /** ===== settings menu ===== */
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  useEffect(() => {
    const onDocClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  /** ===== model / accent ===== */
  // 下拉框改为 Free / Paid；Paid 默认被锁，解锁后可选
  const [modelUnlocked, setModelUnlocked] = useState(() => {
    return localStorage.getItem(PAID_UNLOCK_KEY) === "1";
  });
  const [selectedModel, setSelectedModel] = useState(() => {
    return localStorage.getItem(PAID_UNLOCK_KEY) === "1" ? "paid" : "free";
  });
  const [selectedAccent, setSelectedAccent] = useState(ACCENTS[0]);

  useEffect(() => {
    // 如果未解锁且当前选择了 paid，强制回退到 free
    if (!modelUnlocked && selectedModel === "paid") {
      setSelectedModel("free");
    }
  }, [modelUnlocked, selectedModel]);

  /** ===== conversations ===== */
  const [convos, setConvos] = useState([]);
  const [activeId, setActiveId] = useState(() => localStorage.getItem(ACTIVE_KEY));
  const activeConv = convos.find((c) => c.id === activeId) || null;

  useEffect(() => {
    if (!userId) return;
    (async () => {
      const list = await listConversations();
      if (list.length) {
        setConvos(list);
        const stored = localStorage.getItem(ACTIVE_KEY);
        const pick = stored && list.some((c) => c.id === stored) ? stored : list[0].id;
        setActiveId(pick);
        localStorage.setItem(ACTIVE_KEY, pick);
      } else {
        const c = await createConversation();
        setConvos([c]);
        setActiveId(c.id);
        localStorage.setItem(ACTIVE_KEY, c.id);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
  }, [activeId, ACTIVE_KEY]);

  // 防止 New 被连点导致重复
  const creatingRef = useRef(false);
  const handleNewConversation = async () => {
    if (creatingRef.current) return;
    creatingRef.current = true;
    try {
      const c = await createConversation();
      setConvos((prev) => (prev.some((x) => x.id === c.id) ? prev : [c, ...prev]));
      setActiveId(c.id);
      localStorage.setItem(ACTIVE_KEY, c.id);
    } finally {
      creatingRef.current = false;
    }
  };

  const activateConversation = async (id) => {
    if (id === activeId) return;
    setActiveId(id);
    const data = await loadConversation(id);
    if (data) setConvos((prev) => prev.map((c) => (c.id === id ? data : c)));
  };

  /** ===== dots + rename/delete ===== */
  const [hoverId, setHoverId] = useState(null);
  const [dotMenuFor, setDotMenuFor] = useState(null);
  const dotMenuRef = useRef(null);
  useEffect(() => {
    const onDocClick = (e) => {
      if (dotMenuRef.current && !dotMenuRef.current.contains(e.target)) setDotMenuFor(null);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [renameId, setRenameId] = useState(null);
  const openRename = (conv) => {
    setRenameId(conv.id);
    setRenameValue(conv.title || "");
    setRenameOpen(true);
    setDotMenuFor(null);
  };
  const commitRename = async () => {
    if (!renameId) return;
    await renameConversation(renameId, renameValue || "Untitled");
    setConvos((prev) =>
      prev.map((c) => (c.id === renameId ? { ...c, title: renameValue || "Untitled" } : c))
    );
    setRenameOpen(false);
    setRenameId(null);
  };
  const doDelete = async (id) => {
    await deleteConversation(id);
    setConvos((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) {
      const next = await listConversations();
      if (next.length) {
        setActiveId(next[0].id);
        localStorage.setItem(ACTIVE_KEY, next[0].id);
      } else {
        const c = await createConversation();
        setConvos([c]);
        setActiveId(c.id);
        localStorage.setItem(ACTIVE_KEY, c.id);
      }
    }
    setDotMenuFor(null);
  };

  /** ===== transcript / stream ===== */
  const [recording, setRecording] = useState(false);
  const [volumeOpen, setVolumeOpen] = useState(false);
  const [volume, setVolume] = useState(1);
  const transcriptBoxRef = useRef(null);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [interimText, setInterimText] = useState("");
  const currentSegIdRef = useRef(null);
  const segAudioUrlRef = useRef(null);
  const streamRef = useRef(null);

  const startSegment = async () => {
    if (!activeConv) return null;
    const segId = "s_" + Date.now();
    currentSegIdRef.current = segId;
    segAudioUrlRef.current = null;

    setConvos((prev) =>
      prev.map((c) =>
        c.id !== activeConv.id
          ? c
          : {
              ...c,
              segments: [
                ...(c.segments || []),
                { id: segId, start: Date.now(), end: null, transcript: "", audioUrl: null },
              ],
            }
      )
    );
    setLiveTranscript("");
    setInterimText("");
    setTimeout(() => {
      if (transcriptBoxRef.current)
        transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
    }, 0);
    return segId;
  };

  const finishSegment = async () => {
    const segId = currentSegIdRef.current;
    if (!segId) return;

    const updated = convos.map((c) => {
      if (c.id !== activeConv.id) return c;
      const segs = (c.segments || []).map((s) =>
        s.id === segId
          ? { ...s, end: Date.now(), transcript: liveTranscript, audioUrl: segAudioUrlRef.current }
          : s
      );
      const next = { ...c, segments: segs };
      if ((c.segments?.length || 0) >= 1 && c.title?.startsWith("New Chat") && liveTranscript) {
        next.title = titleFrom(liveTranscript) || c.title;
      }
      return next;
    });
    setConvos(updated);

    try {
      await appendSegment(activeConv.id, {
        id: segId,
        start: Date.now() - 1,
        end: Date.now(),
        transcript: liveTranscript,
        audioUrl: segAudioUrlRef.current,
      });
    } catch {}

    setLiveTranscript("");
    setInterimText("");
    currentSegIdRef.current = null;
    segAudioUrlRef.current = null;
  };

  const micStart = async () => {
    // 确保有会话，并拿到本次真正使用的 convId
    let convId = activeId;
    if (!activeConv) {
      const c = await createConversation();
      setConvos((prev) => (prev.some((x) => x.id === c.id) ? prev : [c, ...prev]));
      setActiveId(c.id);
      convId = c.id;
    }
    await startSegment();

    streamRef.current = createStreamClient({
      conversationId: convId,
      model: selectedModel, // "free" | "paid"
      accent: selectedAccent,
      mode: USE_LOCAL_SPEECH ? "local" : "ws",
      onText: (payload) => {
        if (typeof payload === "string") {
          setInterimText("");
          setLiveTranscript((prev) => (prev ? prev + payload : payload));
        } else {
          const { interim, final } = payload;
          if (interim != null) setInterimText(interim);
          if (final) {
            setInterimText("");
            setLiveTranscript((prev) => (prev ? prev + final : final));
          }
        }
        if (transcriptBoxRef.current) {
          transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
        }
      },
      onTtsStart: () => {},
      onTtsBlob: (blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        segAudioUrlRef.current = url;
      },
      onTtsEnded: () => {},
      outputVolume: volume,
    });

    await streamRef.current.open();
    await streamRef.current.startSegment();
    await streamRef.current.startMic?.();
    setRecording(true);
  };

  const micStop = async () => {
    setRecording(false);
    try { await streamRef.current?.stopMic?.(); } catch {}
    try { await streamRef.current?.stopSegment?.(); } catch {}
    try { await streamRef.current?.close?.(); } catch {}
    streamRef.current = null;
    await finishSegment();
  };

  const onMicToggle = () => (recording ? micStop() : micStart());

  /** ===== upgrade / logout / change password ===== */
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const upgradeKeyRef = useRef(null);

  const [pwdOpen, setPwdOpen] = useState(false);
  const [newPwd, setNewPwd] = useState("");
  const [showNewPwd, setShowNewPwd] = useState(false);

  const confirmUpgrade = async () => {
    const key = upgradeKeyRef.current?.value?.trim();
    if (!key) return;
    const r = await verifyUpgradeKey(key);
    if (r?.ok) {
      setModelUnlocked(true);
      localStorage.setItem(PAID_UNLOCK_KEY, "1");
      setUpgradeOpen(false);
      alert("Upgrade successful! Paid model unlocked.");
      // 如果当前正好在选择 paid 被禁用的状态，允许用户选择
    } else alert("Invalid key!");
  };

  const confirmChangePassword = async () => {
    if (!newPwd) { alert("Please enter a new password."); return; }
    try {
      const res = await changePassword({ userId, newPassword: newPwd });
      if (res?.ok) {
        setPwdOpen(false);
        setNewPwd("");
        setShowNewPwd(false);
        alert("Password updated. It will take effect next login.");
      } else {
        alert(res?.message || "Failed to update password.");
      }
    } catch (e) {
      alert(e?.message || "Unexpected error.");
    }
  };

  const confirmLogout = () => {
    if (recording) micStop();
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUserId");
    localStorage.removeItem("authUsername");
    sessionStorage.removeItem("authToken");
    sessionStorage.removeItem("authUserId");
    sessionStorage.removeItem("authUsername");
    navigate("/login", { replace: true });
  };

  return (
    <div className={styles.container}>
      {/* ===== Sidebar ===== */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTop} ref={menuRef}>
          <button
            className={styles.settingsButton}
            onClick={() => setMenuOpen((v) => !v)}
            title="Settings"
          >
            ⚙️
          </button>
          <span className={styles.hiText}>Hi, {username}!</span>
          {menuOpen && (
            <div className={styles.dropdown}>
              <button onClick={() => { setMenuOpen(false); setUpgradeOpen(true); }}>
                <span className={styles.icon}>🌐</span> Update Model
              </button>
              <button onClick={() => { setMenuOpen(false); setPwdOpen(true); }}>
                <span className={styles.icon}>🛠️</span> Change Password
              </button>
              <button onClick={() => { setMenuOpen(false); confirmLogout(); }}>
                <span className={styles.icon}>📤</span> Log Out
              </button>
            </div>
          )}
        </div>

        <div className={styles.convoHeader}>
          <span>Conversations</span>
          <button className={styles.newBtn} onClick={handleNewConversation}>New</button>
        </div>

        <ul className={styles.convoList}>
          {convos.map((c) => {
            const lastSeg = (c.segments || [])[ (c.segments || []).length - 1 ];
            const preview = lastSeg?.transcript?.slice(0, 38) || "";
            return (
              <li
                key={c.id}
                onMouseEnter={() => setHoverId(c.id)}
                onMouseLeave={() => setHoverId(null)}
                className={`${styles.convoItem} ${c.id === activeId ? styles.convoActive : ""}`}
                onClick={() => activateConversation(c.id)}
              >
                <div className={styles.convoRow}>
                  <div className={styles.convoTitle}>{c.title || "Untitled"}</div>
                  <button
                    className={`${styles.dotBtn} ${hoverId === c.id ? styles.dotBtnVisible : ""}`}
                    onClick={(e) => { e.stopPropagation(); setDotMenuFor(c.id === dotMenuFor ? null : c.id); }}
                    title="More"
                  >
                    ⋯
                  </button>
                </div>
                {preview ? <div className={styles.convoPreview}>{preview}</div> : null}

                {dotMenuFor === c.id && (
                  <div ref={dotMenuRef} className={styles.dotMenu} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.dotMenuItem} onClick={() => openRename(c)}>✏️ Rename</div>
                    <div className={styles.dotMenuItemDanger} onClick={() => doDelete(c.id)}>🗑️ Delete</div>
                  </div>
                )}
              </li>
            );
          })}
          {!convos.length && <li className={styles.convoEmpty}>No conversations yet</li>}
        </ul>
      </aside>

      {/* ===== Main ===== */}
      <main className={styles.main}>
        <div className={styles.modelBox}>
          <label className={styles.accentLabel}>Model </label>
          <select
            className={styles.select}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="free">Free</option>
            <option value="paid" disabled={!modelUnlocked}>Paid</option>
          </select>
        </div>

        <div className={styles.transcript} ref={transcriptBoxRef}>
          {activeConv?.segments?.map((s) => (
            <div key={s.id} className={styles.segment}>
              <div className={styles.segmentMeta}>
                <span>
                  {new Date(s.start).toLocaleTimeString()} — {s.end ? new Date(s.end).toLocaleTimeString() : "…"}
                </span>
                {s.audioUrl && <audio controls src={s.audioUrl} className={styles.segmentAudio} />}
              </div>
              {s.transcript ? <div className={styles.segmentText}>{s.transcript}</div> : null}
            </div>
          ))}
          {recording ? (
            <div className={`${styles.segment} ${styles.segmentLive}`}>
              <div className={styles.segmentMeta}><span>Recording…</span></div>
              <div className={styles.segmentText}>
                {liveTranscript}<span style={{ opacity: 0.5 }}>{interimText}</span>
              </div>
            </div>
          ) : !activeConv?.segments?.length ? (
            <span className={styles.placeholder}>Transcription will appear here…</span>
          ) : null}
        </div>

        <div className={styles.accentBox}>
          <label className={styles.accentLabel}>Accent</label>
          <select className={styles.select} value={selectedAccent} onChange={(e) => setSelectedAccent(e.target.value)}>
            {ACCENTS.map((a) => <option key={a}>{a}</option>)}
          </select>
        </div>

        <div className={styles.centerControls}>
          <button
            className={`${styles.iconBtn} ${styles.micBtn} ${recording ? styles.micActive : ""}`}
            onClick={onMicToggle}
            title={recording ? "Stop" : "Start"}
          >
            🎙️
          </button>
          <div className={styles.volumeWrap}>
            <button className={styles.iconBtn} title="Volume" onClick={() => setVolumeOpen((v) => !v)}>
              🔊
            </button>
            {volumeOpen && (
              <div className={styles.volumePopover} onMouseLeave={() => setVolumeOpen(false)}>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={volume}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value);
                    setVolume(v);
                    streamRef.current?.setOutputVolume?.(v);
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ===== rename modal ===== */}
      {renameOpen && (
        <div className={styles.backdrop} onClick={() => setRenameOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Rename Conversation</div>
            <div className={styles.modalBody}>
              <input
                className={styles.input}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && commitRename()}
                autoFocus
                placeholder="Enter a new title"
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setRenameOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={commitRename}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* ===== upgrade modal ===== */}
      {upgradeOpen && (
        <div className={styles.backdrop} onClick={() => setUpgradeOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Enter upgrade key</div>
            <div className={styles.modalBody}>
              <input
                className={styles.input}
                ref={upgradeKeyRef}
                placeholder="Enter key (e.g., SECRET123)"
                autoFocus
              />
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setUpgradeOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={confirmUpgrade}>Confirm</button>
            </div>
          </div>
        </div>
      )}

      {/* ===== change password modal ===== */}
      {pwdOpen && (
        <div className={styles.backdrop} onClick={() => setPwdOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>Change Password</div>
            <div className={styles.modalBody}>
              <label className={styles.modalLabel}>New Password</label>
              <div className={styles.field}>
                <input
                  className={`${styles.input} ${styles.inputWithEye}`}
                  type={showNewPwd ? "text" : "password"}
                  placeholder="Enter a new password"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                />
                <button
                  type="button"
                  className={styles.eyeBtn}
                  onClick={() => setShowNewPwd((v) => !v)}
                  aria-label={showNewPwd ? "Hide password" : "Show password"}
                  title={showNewPwd ? "Hide password" : "Show password"}
                >
                  <EyeIcon open={showNewPwd} />
                </button>
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnGhost} onClick={() => setPwdOpen(false)}>Cancel</button>
              <button className={styles.btnPrimary} onClick={confirmChangePassword}>Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
