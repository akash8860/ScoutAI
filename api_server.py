from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
from modules.Universal_web_scraper import run as universal_scraper_run

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    city: str = "none"
    mode: str = "none"

@app.post("/scrape")
async def trigger_scrape(req: ScrapeRequest):
    await universal_scraper_run(req.url, req.city, req.mode)  # Wait for it to finish
    return {
        "status": "scraping_finished",
        "details": f"Scraping done: {req.url}, City: {req.city}, Mode: {req.mode}"
    }

# Add this route for Excel download
@app.get("/download")
def download_file():
    file_path = "output/Delhi_buy_paginated.xlsx"
    return FileResponse(
        path=file_path,
        filename="Delhi_buy_paginated.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
