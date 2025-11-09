// assets/auth.js
const AUTH = (() => {
  const SESSION_KEY = 'rf:session';
  const USERS_KEY   = 'rf:users';

  // Local fallback override (for offline demos)
  const ADM_OVR_KEY = 'rf:admins:override';

  const API_BASE = 'http://127.0.0.1:5050';

  // ---- small utils ----
  const normEmail = (e) => (e || '').trim().toLowerCase();
  const uniq = (arr) => [...new Set(arr.map(normEmail))].filter(Boolean);

  function getJSON(key, fallback=null) {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
  }
  function setJSON(key, value) { localStorage.setItem(key, JSON.stringify(value)); }

  // ---- API helpers with fallback ----
  async function apiGetAdmins() {
    try {
      const r = await fetch(`${API_BASE}/api/admins`, { cache: 'no-store' });
      if (!r.ok) throw new Error();
      return await r.json();
    } catch {
      // fallback to base file + override
      const base = await (async () => {
        try {
          const res = await fetch('data/admins.json', { cache: 'no-store' });
          const list = await res.json();
          return Array.isArray(list) ? uniq(list) : [];
        } catch { return []; }
      })();
      const ovr = Array.isArray(getJSON(ADM_OVR_KEY, [])) ? uniq(getJSON(ADM_OVR_KEY, [])) : [];
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
      if (!r.ok) throw new Error();
      return await r.json();
    } catch {
      // fallback: update local override
      const ovr = Array.isArray(getJSON(ADM_OVR_KEY, [])) ? getJSON(ADM_OVR_KEY, []) : [];
      if (!ovr.map(normEmail).includes(email)) ovr.push(email);
      setJSON(ADM_OVR_KEY, uniq(ovr));
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
      if (!r.ok) throw new Error();
      return await r.json();
    } catch {
      // fallback: update local override
      const ovr = Array.isArray(getJSON(ADM_OVR_KEY, [])) ? getJSON(ADM_OVR_KEY, []) : [];
      setJSON(ADM_OVR_KEY, ovr.filter(e => normEmail(e) !== email));
      return apiGetAdmins();
    }
  }

  // ---- session & users ----
  function current() { return getJSON(SESSION_KEY, null); }
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

  async function isAdmin(email) {
    const all = await apiGetAdmins();
    return all.includes(normEmail(email));
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

  // expose cockpit ops
  const addAdmin    = apiAddAdmin;
  const removeAdmin = apiRemoveAdmin;
  const getAdminsMerged = apiGetAdmins;

  // keep export in case you want it later
  async function exportMergedAdmins() {
    const merged = await apiGetAdmins();
    const blob = new Blob([JSON.stringify(merged, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'admins.json';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  return { current, login, logout, isAdmin, addAdmin, removeAdmin, getAdminsMerged, exportMergedAdmins };
})();
