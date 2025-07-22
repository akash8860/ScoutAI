from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
from playwright.async_api import async_playwright

async def detect_and_paginate(url, city, mode):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        all_data = []
        page_num = 1

        while True:
            await page.wait_for_timeout(2000)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            cards = soup.find_all("div")
            data = [{"Text": card.get_text(strip=True)} for card in cards if card.get_text(strip=True)]
            all_data.extend(data)

            next_button = await page.query_selector("a[rel='next'], .pagination-next, button.next")
            if next_button:
                await next_button.click()
                page_num += 1
                logging.info(f"Paginated to page {page_num}")
            else:
                break

        df = pd.DataFrame(all_data)
        os.makedirs("output", exist_ok=True)
        fname = f"output/{city}_{mode}_paginated.xlsx"
        df.to_excel(fname, index=False)
        logging.info(f"Saved {len(df)} rows → {fname}")

        await browser.close()