import asyncio
import logging
import os
import json
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Configuration
BATCH_SIZE = 100
MAX_SCROLLS = 6
DEBUG_MODE = True  # Capture screenshots
HEADLESS = False   # Set to True to run headless

# ========== Utilities ==========

def save_resume_page(city, mode, page_number):
    fname = f"{mode}_{city.replace(' ', '_').lower()}_state.json"
    with open(fname, 'w') as f:
        json.dump({"last_page": page_number}, f)

def get_resume_page(city, mode):
    fname = f"{mode}_{city.replace(' ', '_').lower()}_state.json"
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            return json.load(f).get("last_page", 1)
    return 1

def save_batch(city, mode, data, batch_num):
    if not data or not isinstance(data, list) or not isinstance(data[0], dict):
        logging.warning("Invalid batch, skipping save.")
        return
    df = pd.DataFrame(data)
    fname = f"{mode}_{city.replace(' ', '_').lower()}_batch_{batch_num}.xlsx"
    df.to_excel(fname, index=False)
    logging.info(f"Saved batch {batch_num} ({len(df)} rows) → {fname}")

def combine_batches(city, mode):
    prefix = f"{mode}_{city.replace(' ', '_').lower()}"
    files = sorted(f for f in os.listdir() if f.startswith(f"{prefix}_batch_") and f.endswith('.xlsx'))
    try:
        combined = pd.concat([pd.read_excel(f) for f in files], ignore_index=True)
        combined.to_excel(f"{prefix}.xlsx", index=False)
        for f in files:
            os.remove(f)
        logging.info(f"Combined into → {prefix}.xlsx")
    except Exception as e:
        logging.error(f"Failed to combine batches: {e}")

def extract_selected_fields(html):
    soup = BeautifulSoup(html, 'html.parser')
    listings = soup.select("div[data-pos^='srp-']")
    results = []

    for item in listings:
        data = {}
        link_tag = item.find("a", href=True)
        data["URL"] = "https://housing.com" + link_tag['href'] if link_tag else ""

        title = item.select_one("h2") or item.select_one("div.T_cardV1Title")
        data["Title"] = title.get_text(strip=True) if title else ""

        seller = item.find("div", class_="T_contactBar")
        data["Seller"] = seller.get_text(strip=True) if seller else ""

        price = item.find("div", class_="T_price")
        data["Price"] = price.get_text(strip=True) if price else ""

        results.append(data)
    return results

async def scroll_and_load(page, screenshot_prefix):
    for i in range(MAX_SCROLLS):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(2500)
        if DEBUG_MODE:
            await page.screenshot(path=f"{screenshot_prefix}_scroll_{i + 1}.png")

# ========== Pagination Handler ==========

async def paginate(page, page_number):
    try:
        page_links = await page.query_selector_all("button.T_paginationButton")
        for link in page_links:
            label = await link.inner_text()
            if label.strip() == str(page_number + 1):
                await link.click()
                await page.wait_for_timeout(3000)
                return True

        next_button = await page.query_selector("button[aria-label='Next']")
        if next_button:
            await next_button.click()
            await page.wait_for_timeout(3000)
            return True

        fallback_button = await page.query_selector("button[data-testid='buttonId']")
        if fallback_button:
            await fallback_button.click()
            await page.wait_for_timeout(3000)
            return True

    except Exception as e:
        logging.warning(f"Pagination interaction failed: {e}")
    return False

# ========== Main Scraper ==========

async def scrape_city(city, mode, url_prefix, playwright):
    page_number = get_resume_page(city, mode)
    batch, batch_num = [], 1
    city_slug = city.strip().lower().replace(" ", "_")
    full_url = url_prefix + city_slug

    try:
        browser = await playwright.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        logging.info(f"Navigating to {full_url}")
        await page.goto(full_url)

        await page.wait_for_selector("input[placeholder*='locality']", timeout=10000)
        await page.get_by_role("button", name="Search").click()
        await page.wait_for_timeout(3000)

        while True:
            logging.info(f"Scraping Page {page_number} of {city} ({mode})")
            await scroll_and_load(page, f"screenshots/{city_slug}_{mode}_page_{page_number}")
            html = await page.content()
            new_data = extract_selected_fields(html)

            if not new_data:
                logging.warning("Empty listing. Ending scrape.")
                break

            batch.extend(new_data)
            if len(batch) >= BATCH_SIZE:
                save_batch(city, mode, batch, batch_num)
                batch = []
                batch_num += 1

            save_resume_page(city, mode, page_number)

            success = await paginate(page, page_number)
            if not success:
                logging.info("No more pages or failed to navigate.")
                break

            page_number += 1

        if batch:
            save_batch(city, mode, batch_num)

        await browser.close()
        combine_batches(city, mode)

    except Exception as e:
        logging.error(f"Fatal scraping error: {e}")

# ========== Fallbacks and Runner ==========

def get_fallback_city(city):
    city = city.strip().lower()

    if city == 'delhi':
        return 'new delhi'
    elif city == 'bangalore':
        return 'bengaluru'
    elif city == 'mumbai':
        return 'bombay'
    elif city == 'gurgaon':
        return 'gurugram'
    elif city == 'noida':
        return 'greater noida'
    elif city == 'hyderabad':
        return 'secunderabad'
    else:
        return city


def get_mode_url_prefix(mode):
    BASE_URLS = {
        "rent": "https://housing.com/rent/property-for-rent-in-",
        "buy": "https://housing.com/in/buy/real-estate-",
        "commercial": "https://housing.com/commercial/commercial-real-estate-in-"
    }
    return BASE_URLS.get(mode.strip().lower())

# ========== Entry Point ==========

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    os.makedirs("screenshots", exist_ok=True)

    # Interactive prompt
    city_input = input("Enter city name: ").strip()
    mode_input = input("Enter mode (rent / buy / commercial): ").strip().lower()

    city = get_fallback_city(city_input)
    url_prefix = get_mode_url_prefix(mode_input)

    if not url_prefix:
        print("Invalid mode. Use: rent, buy, commercial")
        exit(1)

    async def runner():
        async with async_playwright() as playwright:
            await scrape_city(city, mode_input, url_prefix, playwright)

    asyncio.run(runner())
