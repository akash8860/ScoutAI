from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
from playwright.async_api import async_playwright

async def scroll_and_extract(url, city, mode):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        for i in range(10):
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        blocks = soup.find_all("div")
        data = [{"Text": b.get_text(strip=True)} for b in blocks if b.get_text(strip=True)]

        df = pd.DataFrame(data)
        fname = os.path.join("output", f"{city}_{mode}_scroll_scraped.xlsx")
        os.makedirs("output", exist_ok=True)
        df.to_excel(fname, index=False)
        logging.info(f"Saved {len(df)} rows → {fname}")
        await browser.close()
