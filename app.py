# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, re

app = Flask(__name__)
# Allow both localhost and 127.0.0.1 origins on :8000 (static server)
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}
})

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ADM_FILE = os.path.join(DATA_DIR, "admins.json")
RES_FILE = os.path.join(DATA_DIR, "resources.json")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ---------- Utilities ----------
def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ADM_FILE):
        with open(ADM_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not os.path.exists(RES_FILE):
        with open(RES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

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

def _admins():
    _ensure_files()
    raw = _read_json(ADM_FILE, [])
    seen = set(); out = []
    for e in raw if isinstance(raw, list) else []:
        if isinstance(e, str):
            em = e.strip().lower()
            if em and em not in seen:
                seen.add(em); out.append(em)
    return out

def _resources():
    _ensure_files()
    raw = _read_json(RES_FILE, [])
    # expect list of dicts with string id
    return raw if isinstance(raw, list) else []

def _save_resources(items):
    _ensure_files()
    _write_json(RES_FILE, items)

def _is_admin_from_request():
    # Expect "X-User-Email" header (set by admin.html using session email)
    email = (request.headers.get("X-User-Email") or "").strip().lower()
    return email in _admins()

def _normalize_hours(hours):
    """Validate/normalize hours to { 'Sun': {open:'HH:MM', close:'HH:MM', closed:bool}, ... }"""
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
    """Return a new string id greater than any existing numeric-like id."""
    max_id = 0
    for r in existing:
        try:
            max_id = max(max_id, int(str(r.get("id", "0")).strip() or "0"))
        except Exception:
            continue
    return str(max_id + 1)

# ---------- Health ----------
@app.get("/api/health")
def health():
    return jsonify({"ok": True})

# ---------- Admins (existing) ----------
@app.get("/api/admins")
def get_admins():
    return jsonify(_admins())

@app.post("/api/admins")
def add_admin():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    admins = _admins()
    if email not in admins:
        admins.append(email)
        _write_json(ADM_FILE, sorted(admins))
    return jsonify(sorted(admins))

@app.delete("/api/admins")
def remove_admin():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    admins = [e for e in _admins() if e != email]
    _write_json(ADM_FILE, sorted(admins))
    return jsonify(sorted(admins))

# ---------- Resources (NEW CRUD) ----------
@app.get("/api/resources")
def list_resources():
    return jsonify(_resources())

@app.post("/api/resources")
def create_resource():
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    items = _resources()
    # minimal fields
    name = (payload.get("name") or "").strip()
    rtype = (payload.get("type") or "").strip().lower()
    building = (payload.get("building") or "").strip()
    room = (payload.get("room") or "").strip()
    notes = payload.get("notes") or ""
    hours = _normalize_hours(payload.get("hours", {}))

    if not name or not rtype or not building:
        return jsonify({"error": "name, type, building are required"}), 400

    new_id = _next_id(items)
    rec = {
        "id": new_id,
        "name": name,
        "type": rtype,
        "building": building,
        "room": room,
        "notes": notes,
        "hours": hours
    }
    items.append(rec)
    _save_resources(items)
    return jsonify(rec), 201

@app.put("/api/resources/<rid>")
def update_resource(rid):
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    items = _resources()

    # find existing
    idx = next((i for i, r in enumerate(items) if str(r.get("id")) == str(rid)), -1)
    if idx == -1:
        return jsonify({"error": "Not found"}), 404

    curr = items[idx]
    # patchable fields
    for key in ["name", "type", "building", "room", "notes"]:
        if key in payload:
            val = payload.get(key)
            curr[key] = (val or "").strip() if isinstance(val, str) else val
    if "hours" in payload:
        curr["hours"] = _normalize_hours(payload.get("hours", {}))

    items[idx] = curr
    _save_resources(items)
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
    # Runs on http://127.0.0.1:5050
    app.run(host="127.0.0.1", port=5050, debug=True)
