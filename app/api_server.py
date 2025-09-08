from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modules.Universal_web_scraper import run as universal_scraper_run
from app import users, batch_upload, history, status_tracker

# subscription guard (new)
from app.subscription_guard import (
    ensure_user,
    get_user_record,
    can_consume,
    consume_quota,
)

app = FastAPI()

# CORS for extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session support for login
app.add_middleware(SessionMiddleware, secret_key="your-secret")

# Include platform routers
app.include_router(users.router)
app.include_router(batch_upload.router)
app.include_router(history.router)
app.include_router(status_tracker.router)

# Scrape trigger
class ScrapeRequest(BaseModel):
    url: str
    city: str = "none"
    mode: str = "none"


def extract_username_from_request(request: Request) -> str:
    """
    Minimal extraction method:
    1) Authorization: Bearer <username>
    2) X-User: <username>
    Temporarily we treat the provided value as the GitHub username / identifier.
    Replace with OAuth later.
    """
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        # 'Bearer username' or 'Bearer token' (we use username for now)
        return auth.split(None, 1)[1].strip()
    return request.headers.get("x-user")


@app.post("/scrape")
async def trigger_scrape(req: ScrapeRequest, request: Request = None):
    """
    Enforces monthly quota per user. Client must provide:
      Authorization: Bearer <github-username>
    or
      X-User: <github-username>

    Behavior:
    - If user not present in users.json, create with 'free' tier automatically.
    - If quota exceeded -> 403 with sponsor link message.
    - On successful scrape, decrement quota by 1.
    """
    # extract username
    # Note: FastAPI will pass Request if included as param; if None, try to access global (should not happen)
    if request is None:
        raise HTTPException(status_code=500, detail="Internal server error: request not available")

    username = extract_username_from_request(request)
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Missing user token/header. Provide Authorization: Bearer <github-username> or X-User header."
        )

    # ensure user exists (auto-create as free). Change behavior if you want to deny unknowns.
    rec = get_user_record(username)
    if not rec:
        ensure_user(username, tier="free")
        rec = get_user_record(username)

    # quota enforcement
    if not can_consume(username):
        raise HTTPException(
            status_code=403,
            detail="Monthly scrape quota exceeded. Consider sponsoring ScoutAI: https://github.com/sponsors/akash8860"
        )

    # run scraper; only consume quota if scrape succeeds
    try:
        # keep using the same call you already had
        await universal_scraper_run(req.url, req.city, req.mode)
    except Exception as e:
        # don't consume quota on failure; return error for client
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")

    # on success, decrement quota
    try:
        consume_quota(username, 1)
    except Exception:
        # don't block response if saving quota fails; you may want to log this
        pass

    return {
        "status": "scraping_finished",
        "details": f"Scraping done: {req.url}, City: {req.city}, Mode: {req.mode}"
    }


# Excel download endpoint
@app.get("/download")
def download_file():
    file_path = "output/Delhi_buy_paginated.xlsx"
    return FileResponse(
        path=file_path,
        filename="Delhi_buy_paginated.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api_server:app", host="0.0.0.0", port=8000, reload=True)
