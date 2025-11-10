/* assets/favs.js — simple per-user favorites using localStorage */
window.FAVS = window.FAVS || (() => {
  const key = (email) => `rf:favs:${(email||'').toLowerCase().trim()}`;

  function _read(email){
    try { return JSON.parse(localStorage.getItem(key(email))) || []; }
    catch { return []; }
  }
  function _write(email, list){
    const uniq = [...new Set((list||[]).map(String))];
    localStorage.setItem(key(email), JSON.stringify(uniq));
    return uniq;
  }

  function list(email){ return _read(email); }
  function has(email, id){ return _read(email).includes(String(id)); }
  function add(email, id){ const s=_read(email); if(!s.includes(String(id))) s.push(String(id)); return _write(email,s); }
  function remove(email, id){ const s=_read(email).filter(x=>x!==String(id)); return _write(email,s); }
  function toggle(email, id){ return has(email,id) ? remove(email,id) : add(email,id); }

  /** Utility: return full resource objects in the same order as saved favorites */
  async function detailed(email){
    const ids = list(email);
    const res = await fetch('data/resources.json', {cache:'no-store'});
    const all = await res.json();
    const byId = new Map(all.map(r => [String(r.id), r]));
    return ids.map(i => byId.get(String(i))).filter(Boolean);
  }

  return { list, has, add, remove, toggle, detailed };
})();
