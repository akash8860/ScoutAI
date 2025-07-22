from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modules.Universal_web_scraper import run as universal_scraper_run
from app import users, batch_upload, history, status_tracker

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

@app.post("/scrape")
async def trigger_scrape(req: ScrapeRequest):
    await universal_scraper_run(req.url, req.city, req.mode)
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
