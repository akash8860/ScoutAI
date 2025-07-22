import os
import pandas as pd
from bs4 import BeautifulSoup
import pandas as pd
from playwright.async_api import async_playwright

async def run_ids_mode(url):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        tables = soup.find_all("table")
        lists = soup.select("ul, ol")
        divs = soup.select("div[class*=list], div[class*=card]")

        elements = tables + lists + divs
        results = [{"Block": el.get_text(strip=True)} for el in elements]

        df = pd.DataFrame(results)
        fname = "output/instant_data_output.xlsx"
        os.makedirs("output", exist_ok=True)
        df.to_excel(fname, index=False)
        print(f"Saved {len(df)} entries → {fname}")

        await browser.close()
