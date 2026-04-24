"""
Authentication helpers.
Uses PyJWT when available, falls back to a stdlib HMAC token.
"""
from __future__ import annotations
import hashlib, hmac, json, time, os, base64, functools
from typing import Optional, Tuple, Dict
from backend.config import SECRET_KEY, TOKEN_EXPIRY_HOURS
from backend import database as db

try:
    import jwt as pyjwt
    _HAS_JWT = True
except ImportError:
    _HAS_JWT = False

# --------------- password hashing (stdlib, no bcrypt needed) ---------------

def _hash_pw(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return base64.b64encode(salt).decode() + ":" + base64.b64encode(dk).decode()


def _verify_pw(password: str, stored: str) -> bool:
    salt_b64, dk_b64 = stored.split(":")
    salt = base64.b64decode(salt_b64)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return hmac.compare_digest(base64.b64encode(dk).decode(), dk_b64)

# --------------- token creation / verification ---------------

def _make_token_stdlib(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw).decode() + "." + sig


def _verify_token_stdlib(token: str) -> Optional[dict]:
    try:
        raw_b64, sig = token.rsplit(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64)
        expected = hmac.new(SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(raw)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "usr": username,
        "exp": int(time.time()) + TOKEN_EXPIRY_HOURS * 3600,
    }
    if _HAS_JWT:
        return pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return _make_token_stdlib(payload)


def verify_token(token: str) -> Optional[dict]:
    if _HAS_JWT:
        try:
            data = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            data["sub"] = int(data["sub"])
            return data
        except (pyjwt.PyJWTError, Exception):
            return None
    return _verify_token_stdlib(token)

# --------------- user operations ---------------

def signup(username: str, email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    if db.query("SELECT 1 FROM users WHERE username=?", (username,), one=True):
        return None, "Username already taken"
    if db.query("SELECT 1 FROM users WHERE email=?", (email,), one=True):
        return None, "Email already registered"
    uid = db.execute(
        "INSERT INTO users (username, email, pw_hash) VALUES (?,?,?)",
        (username, email, _hash_pw(password)),
    )
    return {"id": uid, "username": username, "email": email}, None


def login(username: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    row = db.query("SELECT * FROM users WHERE username=?", (username,), one=True)
    if not row or not _verify_pw(password, row["pw_hash"]):
        return None, "Invalid credentials"
    return create_token(row["id"], row["username"]), None

# --------------- Flask decorator for protected routes ---------------

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request, jsonify
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return wrapper
