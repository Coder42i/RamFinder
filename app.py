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
USERS_FILE   = os.path.join(DATA_DIR, "users.json")
ADM_FILE     = os.path.join(DATA_DIR, "admins.json")
RES_FILE     = os.path.join(DATA_DIR, "resources.json")
UPDATES_FILE = os.path.join(DATA_DIR, "updates.json")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- File helpers ----------

def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)


def _ensure_files():
    _ensure_dir(DATA_DIR)
    _ensure_file(USERS_FILE, [])
    _ensure_file(ADM_FILE, [])
    _ensure_file(RES_FILE, [])
    _ensure_file(UPDATES_FILE, [])


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return default if data is None else data
    except Exception:
        return default


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _norm_email(e):
    return (e or "").strip().lower()


def _list_emails(path):
    """Read a JSON list of emails (or dicts with 'email') and normalize."""
    _ensure_files()
    raw = _read_json(path, [])
    out, seen = [], set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                email = _norm_email(item)
            elif isinstance(item, dict) and "email" in item:
                email = _norm_email(item.get("email"))
            else:
                continue
            if email and email not in seen:
                seen.add(email)
                out.append(email)
    return out


# ---------- Core collections ----------

def _users():
    return _list_emails(USERS_FILE)


def _save_users(emails):
    clean = sorted({ _norm_email(e) for e in (emails or []) if _norm_email(e) })
    _write_json(USERS_FILE, clean)


def _admins():
    return _list_emails(ADM_FILE)


def _save_admins(emails):
    clean = sorted({ _norm_email(e) for e in (emails or []) if _norm_email(e) })
    _write_json(ADM_FILE, clean)


def _resources():
    _ensure_files()
    raw = _read_json(RES_FILE, [])
    return raw if isinstance(raw, list) else []


def _save_resources(items):
    _write_json(RES_FILE, items)


def _subscribers():
    """Return normalized list of subscriber emails."""
    _ensure_files()
    raw = _read_json(UPDATES_FILE, [])
    subs = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                subs.append(_norm_email(item))
            elif isinstance(item, dict) and "email" in item:
                subs.append(_norm_email(item["email"]))
    clean = sorted({ e for e in subs if e })
    return clean


def _save_subscribers(emails):
    clean = sorted({ _norm_email(e) for e in (emails or []) if _norm_email(e) })
    _write_json(UPDATES_FILE, clean)


# ---------- Misc helpers ----------

def _is_admin_from_request():
    email = _norm_email(request.headers.get("X-User-Email"))
    return email in _admins()


def _normalize_hours(hours):
    """Ensure hours is a dict with all 7 days. Values are passed through."""
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    out = {}
    if not isinstance(hours, dict):
        # Everything closed by default if malformed
        return {d: {"closed": True} for d in days}
    for d in days:
        val = hours.get(d)
        if not isinstance(val, dict):
            out[d] = {"closed": True}
        else:
            # Keep open/close if present, default closed flag if missing
            closed = bool(val.get("closed", False))
            entry = {
                "open":  val.get("open", "00:00"),
                "close": val.get("close", "00:00"),
                "closed": closed,
            }
            out[d] = entry
    return out


def _next_resource_id(items):
    max_id = 0
    for r in items:
        try:
            max_id = max(max_id, int(str(r.get("id"))))
        except Exception:
            continue
    return str(max_id + 1)


# ---------- Health ----------

@app.get("/api/health")
def api_health():
    _ensure_files()
    users = _users()
    admins = _admins()
    resources = _resources()
    return jsonify({
        "ok": True,
        "users": len(users),
        "admins": len(admins),
        "resources": len(resources),
    })


# ---------- Users ----------

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
        _save_users(users)
    return jsonify(users)


@app.delete("/api/users")
def delete_user():
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not email:
        return jsonify({"error": "Missing email"}), 400
    users = [u for u in _users() if u != email]
    _save_users(users)
    return jsonify(users)


# ---------- Admins ----------

@app.get("/api/admins")
def get_admins():
    return jsonify(_admins())


@app.post("/api/admins")
def add_admin():
    # For this class/demo app we don't enforce admin auth here,
    # because the frontend uses this to bootstrap admins.
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not EMAIL_RE.match(email or ""):
        return jsonify({"error": "Invalid email"}), 400

    admins = _admins()
    if email not in admins:
        admins.append(email)
        _save_admins(admins)

    # Also ensure admin is listed as a user
    users = _users()
    if email not in users:
        users.append(email)
        _save_users(users)

    return jsonify(admins)


@app.delete("/api/admins")
def delete_admin():
    # Optional: enforce that the caller is an admin
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not email:
        return jsonify({"error": "Missing email"}), 400

    admins = [a for a in _admins() if a != email]
    _save_admins(admins)
    return jsonify(admins)


# ---------- Resources ----------

@app.get("/api/resources")
def get_resources():
    return jsonify(_resources())


@app.post("/api/resources")
def create_resource():
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    name      = (payload.get("name") or "").strip()
    rtype     = (payload.get("type") or "").strip()
    building  = (payload.get("building") or "").strip()
    room      = (payload.get("room") or "").strip()
    notes     = (payload.get("notes") or "").strip()
    hours_raw = payload.get("hours") or {}

    if not name or not rtype or not building:
        return jsonify({"error": "Missing required fields"}), 400

    items = _resources()
    rid = _next_resource_id(items)
    resource = {
        "id": rid,
        "name": name,
        "type": rtype,
        "building": building,
        "room": room,
        "notes": notes,
        "hours": _normalize_hours(hours_raw),
    }
    # Optional: if accessibility was passed through from admin UI
    if "accessibility" in payload:
        resource["accessibility"] = payload["accessibility"]

    items.append(resource)
    _save_resources(items)
    return jsonify(resource), 201


@app.put("/api/resources/<rid>")
def update_resource(rid):
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    items = _resources()
    found = None
    for r in items:
        if str(r.get("id")) == str(rid):
            found = r
            break

    if not found:
        return jsonify({"error": "Not found"}), 404

    # Update editable fields if present
    if "name" in payload:
        found["name"] = (payload.get("name") or "").strip()
    if "type" in payload:
        found["type"] = (payload.get("type") or "").strip()
    if "building" in payload:
        found["building"] = (payload.get("building") or "").strip()
    if "room" in payload:
        found["room"] = (payload.get("room") or "").strip()
    if "notes" in payload:
        found["notes"] = (payload.get("notes") or "").strip()
    if "hours" in payload:
        found["hours"] = _normalize_hours(payload.get("hours") or {})
    if "accessibility" in payload:
        # allow clearing if empty string
        acc = payload.get("accessibility")
        if acc:
          found["accessibility"] = acc
        elif "accessibility" in found:
          del found["accessibility"]

    _save_resources(items)
    return jsonify(found)


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


# ---------- Updates / Notifications ----------

@app.post("/api/updates/subscribe")
def subscribe_updates():
    """Public endpoint: anyone can subscribe with an email address."""
    payload = request.get_json(silent=True) or {}
    email = _norm_email(payload.get("email"))
    if not EMAIL_RE.match(email or ""):
        return jsonify({"error": "Invalid email"}), 400

    subs = _subscribers()
    if email not in subs:
        subs.append(email)
        _save_subscribers(subs)

    return jsonify({"ok": True})


@app.get("/api/updates")
def get_updates():
    """Admin-only endpoint: list all subscriber emails."""
    if not _is_admin_from_request():
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(_subscribers())


if __name__ == "__main__":
    _ensure_files()
    app.run(host="127.0.0.1", port=5050, debug=True)
