/* assets/auth.js — signup/login with users.json and admins.json.
   Change: Admins are implicitly registered; on first admin login we also add them to users.json. */
window.AUTH = window.AUTH || (() => {
  const SESSION_KEY = 'rf:session';
  const USERS_OVR   = 'rf:users:override';   // local fallback list (demo)
  const ADM_OVR     = 'rf:admins:override';  // local fallback list (demo)
  const API_BASE    = 'http://127.0.0.1:5050';

  const norm = (e) => (e||'').trim().toLowerCase();
  const uniq = (arr) => [...new Set((arr||[]).map(norm))].filter(Boolean);

  function getJSON(k, d=null){ try{ return JSON.parse(localStorage.getItem(k)) ?? d; } catch{ return d; } }
  function setJSON(k, v){ localStorage.setItem(k, JSON.stringify(v)); }

  function current(){
    const s = getJSON(SESSION_KEY, null);
    if (!s || !s.email) return null;
    return { email: norm(s.email), name: s.name || '', admin: !!s.admin, ts: s.ts || Date.now() };
  }
  function logout(){ localStorage.removeItem(SESSION_KEY); }

  // --- API helpers with graceful fallback ---
  async function apiHealth(){
    try{ const r = await fetch(`${API_BASE}/api/health`, {cache:'no-store'}); const j = await r.json(); return !!j.ok; }
    catch{ return false; }
  }

  async function baseUsersFile(){
    try{ const r = await fetch('data/users.json', {cache:'no-store'}); const j = await r.json(); return Array.isArray(j)?uniq(j):[]; }
    catch{ return []; }
  }
  async function baseAdminsFile(){
    try{ const r = await fetch('data/admins.json', {cache:'no-store'}); const j = await r.json(); return Array.isArray(j)?uniq(j):[]; }
    catch{ return []; }
  }
  function ovrUsers(){ const v = getJSON(USERS_OVR, []); return Array.isArray(v)?uniq(v):[]; }
  function ovrAdmins(){ const v = getJSON(ADM_OVR, []); return Array.isArray(v)?uniq(v):[]; }
  function setOvrUsers(list){ setJSON(USERS_OVR, uniq(list||[])); }
  function setOvrAdmins(list){ setJSON(ADM_OVR, uniq(list||[])); }

  async function getUsers(){
    // Users known to the system (file/override/API)
    try{ const r = await fetch(`${API_BASE}/api/users`, {cache:'no-store'}); if(!r.ok) throw 0; return uniq(await r.json()); }
    catch{ const base = await baseUsersFile(); return uniq([...base, ...ovrUsers()]); }
  }
  async function getAdmins(){
    // Admins (file/override/API)
    try{ const r = await fetch(`${API_BASE}/api/admins`, {cache:'no-store'}); if(!r.ok) throw 0; return uniq(await r.json()); }
    catch{ const base = await baseAdminsFile(); return uniq([...base, ...ovrAdmins()]); }
  }

  // Persist user (signup) via API, else local override
  async function apiAddUser(email){
    email = norm(email);
    try{
      const r = await fetch(`${API_BASE}/api/users`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email})
      });
      if(!r.ok) throw 0;
      return uniq(await r.json());
    }catch{
      const list = ovrUsers();
      if(!list.includes(email)){ list.push(email); setOvrUsers(list); }
      return getUsers();
    }
  }

  // Persist admin via API, else local override
  async function apiAddAdmin(email){
    email = norm(email);
    try{
      const r = await fetch(`${API_BASE}/api/admins`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email})
      });
      if(!r.ok) throw 0;
      return uniq(await r.json());
    }catch{
      const list = ovrAdmins();
      if(!list.includes(email)){ list.push(email); setOvrAdmins(list); }
      // Ensure user exists in local override as well
      const u = ovrUsers(); if(!u.includes(email)){ u.push(email); setOvrUsers(u); }
      return getAdmins();
    }
  }

  // --- Role checks ---
  async function isRegistered(email){
    const e = norm(email);
    const users  = await getUsers();
    const admins = await getAdmins();
    // Treat admins as implicitly registered
    return users.includes(e) || admins.includes(e);
  }
  async function isAdmin(email){
    const admins = await getAdmins();
    return admins.includes(norm(email));
  }

  // --- Signup / Login ---
  async function signup(email, name){
    const e = norm(email);
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) throw new Error('Please enter a valid email address.');
    await apiAddUser(e); // writes to users.json when backend is up; otherwise local override
    // Optional: auto-login after signup
    return login(e, name);
  }

  async function login(email, name){
    const e = norm(email);
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) throw new Error('Please enter a valid email address.');
    const admin = await isAdmin(e);

    // If not registered AND is admin, auto-register to users.json for consistency.
    const registered = await isRegistered(e);
    if(!registered && admin){
      await apiAddUser(e); // best-effort (works offline via override too)
    }
    // Recompute after possible auto-add
    const isNowRegistered = admin ? true : (await isRegistered(e));
    if(!isNowRegistered) throw new Error('No account found. Please sign up first.');

    const sess = { email: e, name: name || e.split('@')[0], admin, ts: Date.now() };
    setJSON(SESSION_KEY, sess);
    return sess;
  }

  async function refreshSessionAdmin(){
    const s = current();
    if(!s) return null;
    const admin = await isAdmin(s.email);
    const updated = { ...s, admin };
    setJSON(SESSION_KEY, updated);
    return updated;
  }

  // --- Admin helpers used by Admin Cockpit ---
  async function getAdminsMerged(){ return getAdmins(); }
  async function addAdmin(email){ return apiAddAdmin(email); }
  async function removeAdmin(email){
    email = norm(email);
    try{
      const r = await fetch(`${API_BASE}/api/admins`, {method:'DELETE', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email})});
      if(!r.ok) throw 0;
      return uniq(await r.json());
    }catch{
      const list = ovrAdmins().filter(x => x !== email); setOvrAdmins(list);
      return getAdmins();
    }
  }

  async function exportMergedAdmins(){
    const merged = await getAdmins();
    const blob = new Blob([JSON.stringify(merged, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'admins.json';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  return {
    current, logout, refreshSessionAdmin,
    signup, login, isRegistered, isAdmin,
    getAdminsMerged, addAdmin, removeAdmin, exportMergedAdmins,
    apiHealth
  };
})();
