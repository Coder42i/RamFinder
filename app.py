# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, re

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}
})

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")     # <— NEW
ADM_FILE   = os.path.join(DATA_DIR, "admins.json")
RES_FILE   = os.path.join(DATA_DIR, "resources.json")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ---------- Utilities ----------
def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path, default in [
        (USERS_FILE, []),
        (ADM_FILE,   []),
        (RES_FILE,   []),
    ]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)

def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if data is not None else default
    except Exception:
        return default

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _norm_email(e): return (e or "").strip().lower()

def _list_emails(path):
    _ensure_files()
    raw = _read_json(path, [])
    out, seen = [], set()
    if isinstance(raw, list):
        for e in raw:
            if isinstance(e, str):
                n = _norm_email(e)
                if n and n not in seen:
                    seen.add(n); out.append(n)
    return out

def _users():  return _list_emails(USERS_FILE)
def _admins(): return _list_emails(ADM_FILE)

def _resources():
    _ensure_files()
    raw = _read_json(RES_FILE, [])
    return raw if isinstance(raw, list) else []

def _save_resources(items): _write_json(RES_FILE, items)

def _is_admin_from_request():
    email = _norm_email(request.headers.get("X-User-Email"))
    return email in _admins()

def _normalize_hours(hours):
    days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
    out = {}
    if not isinstance(hours, dict):
        return {d: {"closed": True} for d in days}
    for d in days:
        v = hours.get(d, {})
        if not isinstance(v, dict):
            out[d] = {"closed": True}
            continue
        closed = bool(v.get("closed", False))
        open_t = (v.get("open") or "00:00")
        close_t = (v.get("close") or "00:00")
        out[d] = {"open": open_t, "close": close_t, "closed": closed}
    return out

def _next_id(existing):
    max_id = 0
    for r in existing:
        try:
            max_id = max(max_id, int(str(r.get("id", "0")).strip() or "0"))
        except Exception:
            pass
    return str(max_id + 1)

# ---------- Health ----------
@app.get("/api/health")
def health():
    return jsonify({"ok": True})

# ---------- Users (NEW) ----------
@app.get("/api/users")
def get_users():
    return jsonify(_users())

@app.post("/api/users")
def add_user():
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not EMAIL_RE.match(email or ""):
        return jsonify({"error": "Invalid email"}), 400
    users = _users()
    if email not in users:
        users.append(email)
        users = sorted(set(users))
        _write_json(USERS_FILE, users)
    return jsonify(users)

@app.delete("/api/users")
def remove_user():
    # Optional endpoint; not used by UI now.
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    users = [u for u in _users() if u != email]
    _write_json(USERS_FILE, users)
    return jsonify(users)

# ---------- Admins (existing) ----------
@app.get("/api/admins")
def get_admins():
    return jsonify(_admins())

@app.post("/api/admins")
def add_admin():
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not EMAIL_RE.match(email or ""):
        return jsonify({"error": "Invalid email"}), 400
    admins = _admins()
    if email not in admins:
        admins.append(email)
        admins = sorted(set(admins))
        _write_json(ADM_FILE, admins)
    # Ensure admins are also present in users.json (nice invariant)
    users = _users()
    if email not in users:
        users.append(email)
        users = sorted(set(users))
        _write_json(USERS_FILE, users)
    return jsonify(admins)

@app.delete("/api/admins")
def remove_admin():
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    admins = [e for e in _admins() if e != email]
    _write_json(ADM_FILE, admins)
    return jsonify(admins)

# ---------- Resources (CRUD) ----------
@app.get("/api/resources")
def list_resources():
    return jsonify(_resources())

@app.post("/api/resources")
def create_resource():
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    items = _resources()
    name = (payload.get("name") or "").strip()
    rtype = (payload.get("type") or "").strip().lower()
    building = (payload.get("building") or "").strip()
    room = (payload.get("room") or "").strip()
    notes = payload.get("notes") or ""
    hours = _normalize_hours(payload.get("hours", {}))
    if not name or not rtype or not building:
        return jsonify({"error": "name, type, building are required"}), 400
    new_id = _next_id(items)
    rec = {"id": new_id, "name": name, "type": rtype, "building": building, "room": room, "notes": notes, "hours": hours}
    items.append(rec); _save_resources(items)
    return jsonify(rec), 201

@app.put("/api/resources/<rid>")
def update_resource(rid):
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    items = _resources()
    idx = next((i for i, r in enumerate(items) if str(r.get("id")) == str(rid)), -1)
    if idx == -1:
        return jsonify({"error": "Not found"}), 404
    curr = items[idx]
    for key in ["name", "type", "building", "room", "notes"]:
        if key in payload:
            val = payload.get(key)
            curr[key] = (val or "").strip() if isinstance(val, str) else val
    if "hours" in payload:
        curr["hours"] = _normalize_hours(payload.get("hours", {}))
    items[idx] = curr; _save_resources(items)
    return jsonify(curr)

@app.delete("/api/resources/<rid>")
def delete_resource(rid):
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    items = _resources()
    new_items = [r for r in items if str(r.get("id")) != str(rid)]
    if len(new_items) == len(items):
        return jsonify({"error": "Not found"}), 404
    _save_resources(new_items)
    return jsonify({"ok": True, "deleted": rid})

if __name__ == "__main__":
    _ensure_files()
    app.run(host="127.0.0.1", port=5050, debug=True)
