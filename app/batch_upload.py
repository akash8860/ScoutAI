from fastapi import UploadFile, File, APIRouter
import pandas as pd
from modules.Universal_web_scraper import run as universal_scraper_run
import asyncio

router = APIRouter()

@router.post("/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    df = pd.read_excel(file.file)
    for row in df.to_dict(orient="records"):
        url = row.get("url")
        city = row.get("city", "none")
        mode = row.get("mode", "none")
        await universal_scraper_run(url, city, mode)
    return {"status": "batch_scraping_done"}
