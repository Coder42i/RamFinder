# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, re

app = Flask(__name__)
# Allow your static site on http://localhost:8000 to call this API:
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}})

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ADM_FILE = os.path.join(DATA_DIR, "admins.json")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ADM_FILE):
        with open(ADM_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def _read_admins():
    _ensure_files()
    try:
        with open(ADM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            # normalize to lowercase unique
            seen = set()
            out = []
            for e in data:
                if isinstance(e, str):
                    n = e.strip().lower()
                    if n and n not in seen:
                        seen.add(n)
                        out.append(n)
            return out
    except Exception:
        return []

def _write_admins(admins):
    _ensure_files()
    with open(ADM_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(admins), f, indent=2)

@app.get("/api/health")
def health():
    return jsonify({"ok": True})

@app.get("/api/admins")
def get_admins():
    return jsonify(_read_admins())

@app.post("/api/admins")
def add_admin():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    admins = _read_admins()
    if email not in admins:
        admins.append(email)
        _write_admins(admins)
    return jsonify(admins)

@app.delete("/api/admins")
def remove_admin():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    admins = [e for e in _read_admins() if e != email]
    _write_admins(admins)
    return jsonify(admins)

if __name__ == "__main__":
    # Runs on http://localhost:5050
    app.run(host="127.0.0.1", port=5050, debug=True)
