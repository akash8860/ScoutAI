# main.py
import asyncio
from detect_platform_and_structure import detect_platform
from modules import Universal_web_scraper

async def handle_scrape():
    url = input("Enter any real estate site URL: ").strip()
    city = input("Enter city/locality (or 'none'): ").strip()
    mode = input("Enter mode (buy/rent/commercial/none): ").strip().lower()

    platform = detect_platform(url)
    print(f"Platform detected: {platform}")

    if platform == "universal":
        await Universal_web_scraper.run(url, city, mode)
    else:
        use_ids = input("Unknown or unsupported platform. Use fallback Instant Data mode? (y/n): ").strip().lower()
        if use_ids == 'y':
            from strategies.instant_like_scraper import run_ids_mode
            await run_ids_mode(url)

if __name__ == "__main__":
    asyncio.run(handle_scrape())
