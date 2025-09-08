from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os
import time
import json
import uuid
from pathlib import Path
from typing import Optional

# your scraper entry point (keep as-is)
from modules.Universal_web_scraper import run as universal_scraper_run

# subscription guard (file-based)
from app.subscription_guard import (
    ensure_user,
    get_user_record,
    can_consume,
    consume_quota,
    _load_users,
    _save_users,
    DEFAULTS
)

# Files at repo root
USERS_FILE = Path("users.json")
HISTORY_FILE = Path("history.json")

app = FastAPI()

# CORS middleware (for extension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; restrict in production to your extension origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    city: str = "none"
    mode: str = "none"


def extract_username_from_request(request: Request) -> Optional[str]:
    """
    Accept 'Authorization: Bearer <username>' or 'X-User' header.
    Temporary simple auth until OAuth is added.
    """
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1].strip()
    return request.headers.get("x-user")


def record_history_entry(username: str, url: str, city: str, mode: str,
                         status: str, rows: int = 0, output_file: Optional[str] = None,
                         notes: str = "") -> dict:
    """
    Append a history entry to history.json (latest first).
    """
    entry = {
        "id": str(uuid.uuid4()),
        "user": username,
        "url": url,
        "city": city,
        "mode": mode,
        "timestamp": int(time.time()),
        "status": status,
        "rows": rows,
        "output_file": output_file,
        "notes": notes
    }
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]")
    arr = json.loads(HISTORY_FILE.read_text())
    arr.insert(0, entry)
    HISTORY_FILE.write_text(json.dumps(arr, indent=2))
    return entry


@app.post("/scrape")
async def trigger_scrape(req: ScrapeRequest, request: Request):
    """
    Main scrape endpoint with quota enforcement and history logging.
    Client must provide Authorization: Bearer <github-username> (or X-User).
    """
    username = extract_username_from_request(request)
    if not username:
        raise HTTPException(status_code=401, detail="Missing user token/header. Provide Authorization: Bearer <github-username>")

    # ensure user exists (auto-create as free)
    rec = get_user_record(username)
    if not rec:
        ensure_user(username, tier="free")
        rec = get_user_record(username)

    # quota check
    if not can_consume(username):
        raise HTTPException(status_code=403, detail="Monthly scrape quota exceeded. Sponsor: https://github.com/sponsors/akash8860")

    # run the scraper
    try:
        # If your universal_scraper_run is synchronous, you can run it in a thread:
        # loop = asyncio.get_event_loop()
        # result = await loop.run_in_executor(None, universal_scraper_run, req.url, req.city, req.mode)
        await universal_scraper_run(req.url, req.city, req.mode)
        status = "success"
        # optionally compute rows/output_file if your scraper returns them or writes a file
        output_file = None
        rows = 0
    except Exception as e:
        # record failed history
        record_history_entry(username, req.url, req.city, req.mode, "failure", rows=0, output_file=None, notes=str(e))
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")

    # on success consume quota and record history
    try:
        consume_quota(username, 1)
    except Exception:
        # don't block success if saving quota fails; consider logging
        pass

    # If your scraper produced a named output file, set output_file accordingly.
    # Here we keep the existing behaviour: static path example (adjust as needed)
    # e.g., output_file = f"output/{username}_{int(time.time())}.xlsx"
    # rows = <number of rows extracted>  # if available from your scraper
    record_history_entry(username, req.url, req.city, req.mode, "success", rows=rows, output_file=output_file)

    return {
        "status": "scraping_finished",
        "details": f"Scraping done: {req.url}, City: {req.city}, Mode: {req.mode}"
    }


@app.get("/quota")
async def get_quota(request: Request):
    """
    Return the current tier/usage for the requester.
    Expects Authorization: Bearer <username> or X-User header.
    Response: { "tier": "free", "used": 2, "limit": 50 }
    """
    username = extract_username_from_request(request)
    if not username:
        raise HTTPException(status_code=401, detail="Missing user token/header")

    rec = get_user_record(username)
    if not rec:
        ensure_user(username, tier="free")
        rec = get_user_record(username)

    return {
        "tier": rec.get("tier", "free"),
        "used": rec.get("used", 0),
        "limit": rec.get("monthly_quota", 0),
    }


@app.get("/history")
async def get_history(request: Request, limit: int = 50):
    """
    Return recent history entries for the authenticated user.
    """
    username = extract_username_from_request(request)
    if not username:
        raise HTTPException(status_code=401, detail="Missing user token/header")

    if not HISTORY_FILE.exists():
        return []

    all_entries = json.loads(HISTORY_FILE.read_text())
    user_entries = [e for e in all_entries if e.get("user") == username]
    return user_entries[:limit]


# Admin endpoint to set a user's tier manually (protected by ADMIN_TOKEN)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")  # set a secure token in production

@app.post("/admin/set_tier")
async def admin_set_tier(admin_token: str = Body(...), username: str = Body(...), tier: str = Body(...)):
    """
    Usage: POST /admin/set_tier with JSON body { "admin_token":"..", "username":"..", "tier":"pro" }
    This sets/creates the user and assigns the default quota for the tier.
    """
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    # basic validation of tier
    if tier not in DEFAULTS:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {tier}. Valid: {list(DEFAULTS.keys())}")

    # create or update user
    users = _load_users()
    users[username] = {
        "tier": tier,
        "monthly_quota": DEFAULTS.get(tier, DEFAULTS["free"]),
        "used": users.get(username, {}).get("used", 0),
        "last_reset": int(time.time())
    }
    _save_users(users)
    return {"ok": True, "username": username, "tier": tier}


# Excel download route (keep your existing behavior)
@app.get("/download")
def download_file():
    file_path = "output/Delhi_buy_paginated.xlsx"
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        filename="Delhi_buy_paginated.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    import uvicorn
    # Run as app.api_server if this file is in app/ folder
    uvicorn.run("app.api_server:app", host="0.0.0.0", port=8000, reload=True)
