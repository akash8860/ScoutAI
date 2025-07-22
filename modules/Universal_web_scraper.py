# modules/Universal_web_scraper.py
import logging
from utils.logger import init_logger
from strategies.pagination_handler import detect_and_paginate
from strategies.instant_like_scraper import run_ids_mode

init_logger("universal_scraper.log")

async def run(url, city, mode):
    print("Universal scraper activated.")
    logging.info(f"Started universal scrape → URL: {url}, City: {city}, Mode: {mode}")

    if city.lower() == "none" or mode.lower() == "none":
        logging.info("City or mode is 'none'. Running Instant Data Scraper fallback.")
        await run_ids_mode(url)
        return

    try:
        await detect_and_paginate(url, city, mode)
    except Exception as e:
        logging.error(f"Pagination scraping failed: {e}")
        logging.info("Automatically falling back to Instant Data Scraper mode.")
        await run_ids_mode(url)
