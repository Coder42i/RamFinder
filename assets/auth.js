/* assets/auth.js — resilient, API-aware auth with session refresh */
window.AUTH = window.AUTH || (() => {
  const SESSION_KEY = 'rf:session';
  const USERS_KEY   = 'rf:users';
  const ADM_OVR_KEY = 'rf:admins:override'; // local override list (demo mode)
  const API_BASE    = 'http://127.0.0.1:5050';

  // ----- utils -----
  const normEmail = (e) => (e || '').trim().toLowerCase();
  const uniq = (arr) => [...new Set((arr || []).map(normEmail))].filter(Boolean);

  function getJSON(key, fallback = null) {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
    catch { return fallback; }
  }
  function setJSON(key, value) { localStorage.setItem(key, JSON.stringify(value)); }

  function current() {
    const sess = getJSON(SESSION_KEY, null);
    if (!sess || !sess.email) return null;
    // normalize the shape (in case of older sessions)
    return { email: normEmail(sess.email), name: sess.name || '', admin: !!sess.admin, ts: sess.ts || Date.now() };
  }
  function logout()  { localStorage.removeItem(SESSION_KEY); }
  function ensureUsers(){
    if (!Array.isArray(getJSON(USERS_KEY, []))) setJSON(USERS_KEY, []);
  }
  function upsertUser(email, name) {
    ensureUsers();
    const users = getJSON(USERS_KEY, []);
    const e = normEmail(email);
    const i = users.findIndex(u => normEmail(u.email) === e);
    if (i >= 0) { if (name) users[i].name = name; }
    else users.push({ email: e, name: name || e.split('@')[0], createdAt: new Date().toISOString() });
    setJSON(USERS_KEY, users);
  }

  // ----- API helpers with fallback -----
  async function apiHealth() {
    try {
      const r = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
      if (!r.ok) throw 0;
      const j = await r.json();
      return !!j.ok;
    } catch { return false; }
  }

  async function loadBaseAdminsFile() {
    try {
      const res = await fetch('data/admins.json', { cache: 'no-store' });
      const list = await res.json();
      return Array.isArray(list) ? uniq(list) : [];
    } catch { return []; }
  }

  function getAdminsOverride() {
    const v = getJSON(ADM_OVR_KEY, []);
    return Array.isArray(v) ? uniq(v) : [];
  }
  function setAdminsOverride(list) {
    setJSON(ADM_OVR_KEY, uniq(list || []));
  }

  async function apiGetAdmins() {
    try {
      const r = await fetch(`${API_BASE}/api/admins`, { cache: 'no-store' });
      if (!r.ok) throw 0;
      return uniq(await r.json());
    } catch {
      // fallback: base file + local override
      const base = await loadBaseAdminsFile();
      const ovr  = getAdminsOverride();
      return uniq([...base, ...ovr]);
    }
  }

  async function apiAddAdmin(email) {
    email = normEmail(email);
    // try API first
    try {
      const r = await fetch(`${API_BASE}/api/admins`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email })
      });
      if (!r.ok) throw 0;
      return uniq(await r.json());
    } catch {
      // fallback to local override
      const ovr = getAdminsOverride();
      if (!ovr.includes(email)) { ovr.push(email); setAdminsOverride(ovr); }
      return apiGetAdmins();
    }
  }

  async function apiRemoveAdmin(email) {
    email = normEmail(email);
    try {
      const r = await fetch(`${API_BASE}/api/admins`, {
        method: 'DELETE',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email })
      });
      if (!r.ok) throw 0;
      return uniq(await r.json());
    } catch {
      // fallback: local override
      const ovr = getAdminsOverride().filter(x => normEmail(x) !== email);
      setAdminsOverride(ovr);
      return apiGetAdmins();
    }
  }

  // ----- public helpers -----
  async function isAdmin(email) {
    const list = await apiGetAdmins();
    return list.includes(normEmail(email));
  }

  async function login(email, name) {
    const e = normEmail(email);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) throw new Error('Please enter a valid email address.');
    upsertUser(e, name);
    const admin = await isAdmin(e);
    const sess  = { email: e, name: name || e.split('@')[0], admin, ts: Date.now() };
    setJSON(SESSION_KEY, sess);
    return sess;
  }

  /**
   * Recompute admin flag from latest admins and update stored session.
   * Call this on each page load before using sess.admin.
   */
  async function refreshSessionAdmin() {
    const sess = current();
    if (!sess) return null;
    const admin = await isAdmin(sess.email);
    const updated = { ...sess, admin };
    setJSON(SESSION_KEY, updated);
    return updated;
  }

  async function getAdminsMerged() { return apiGetAdmins(); }
  async function addAdmin(email)   { return apiAddAdmin(email); }
  async function removeAdmin(email){ return apiRemoveAdmin(email); }

  // Keep export around (useful for static/manual updates)
  async function exportMergedAdmins() {
    const merged = await apiGetAdmins();
    const blob = new Blob([JSON.stringify(merged, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'admins.json';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  return {
    current, logout, login,
    refreshSessionAdmin,
    isAdmin, getAdminsMerged,
    addAdmin, removeAdmin, exportMergedAdmins,
    apiHealth
  };
})();
