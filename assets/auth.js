const AUTH = (() => {
  const SESSION_KEY = 'rf:session';
  const USERS_KEY   = 'rf:users'; // [{email, name?, createdAt}]

  async function isAdmin(email) {
    try {
      const res = await fetch('data/admins.json', { cache: 'no-store' });
      const list = await res.json();
      return Array.isArray(list)
        && list.map(e => (e||'').toLowerCase()).includes((email||'').toLowerCase());
    } catch { return false; }
  }

  function current()   { return store.get(SESSION_KEY, null); }
  function logout()    { store.remove(SESSION_KEY); }
  function ensureUsers(){
    if (!Array.isArray(store.get(USERS_KEY, []))) store.set(USERS_KEY, []);
  }
  function upsertUser(email, name) {
    ensureUsers();
    const users = store.get(USERS_KEY, []);
    const i = users.findIndex(u => (u.email||'').toLowerCase() === email.toLowerCase());
    if (i >= 0) { if (name) users[i].name = name; }
    else { users.push({ email, name: name||email.split('@')[0], createdAt: new Date().toISOString() }); }
    store.set(USERS_KEY, users);
  }

  async function login(email, name) {
    const normalized = (email||'').trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized))
      throw new Error('Please enter a valid email address.');
    upsertUser(normalized, name);
    const admin = await isAdmin(normalized);
    const sess  = { email: normalized, name: name||normalized.split('@')[0], admin, ts: Date.now() };
    store.set(SESSION_KEY, sess);
    return sess;
  }

  return { current, login, logout, isAdmin };
})();
