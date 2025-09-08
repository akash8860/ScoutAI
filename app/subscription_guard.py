# app/subscription_guard.py
import json
import time
from pathlib import Path
from threading import Lock
from typing import Optional

# USERS_FILE placed at repo root
USERS_FILE = Path("users.json")
LOCK = Lock()

# Default monthly quotas per tier
DEFAULTS = {"free": 50, "pro": 1000, "enterprise": 10000}

def _load_users() -> dict:
    """
    Load users.json from repo root. Creates an empty file if missing.
    """
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({}))
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _save_users(data: dict) -> None:
    with LOCK:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def _reset_if_needed(entry: dict) -> None:
    now = int(time.time())
    # reset monthly if >30 days since last_reset (simple heuristic)
    if now - entry.get("last_reset", 0) > 60 * 60 * 24 * 30:
        entry["used"] = 0
        entry["last_reset"] = now

def ensure_user(username: str, tier: str = "free") -> None:
    users = _load_users()
    if username not in users:
        users[username] = {
            "tier": tier,
            "monthly_quota": DEFAULTS.get(tier, DEFAULTS["free"]),
            "used": 0,
            "last_reset": int(time.time())
        }
        _save_users(users)

def get_user_record(username: str) -> Optional[dict]:
    users = _load_users()
    entry = users.get(username)
    if entry:
        _reset_if_needed(entry)
    return entry

def can_consume(username: str) -> bool:
    rec = get_user_record(username)
    if not rec:
        return False
    return rec.get("used", 0) < rec.get("monthly_quota", 0)

def consume_quota(username: str, n: int = 1) -> None:
    users = _load_users()
    if username not in users:
        raise KeyError("user missing")
    users[username]["used"] = users[username].get("used", 0) + n
    _save_users(users)

# Optional helper to set a user's tier and quota
def set_user_tier(username: str, tier: str) -> None:
    users = _load_users()
    used = users.get(username, {}).get("used", 0)
    users[username] = {
        "tier": tier,
        "monthly_quota": DEFAULTS.get(tier, DEFAULTS["free"]),
        "used": used,
        "last_reset": int(time.time())
    }
    _save_users(users)
