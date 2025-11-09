const store = {
  get(key, fallback = null) {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
    catch { return fallback; }
  },
  set(key, value) { localStorage.setItem(key, JSON.stringify(value)); },
  remove(key) { localStorage.removeItem(key); },
  push(key, item, max = 50) {
    const arr = this.get(key, []);
    arr.unshift(item);
    if (arr.length > max) arr.length = max;
    this.set(key, arr);
    return arr;
  }
};
