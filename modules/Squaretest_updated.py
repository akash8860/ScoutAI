import asyncio
import pandas as pd
import os
import json
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Setup logging to file and console
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("square_scraper.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

setup_logger()

MAX_RETRIES = 1  # Maximum number of retries per city
BATCH_SIZE = 100  # Number of records per Excel batch

# Detect if the URL is for SquareYards
def can_handle(url: str) -> bool:
    return "squareyards.com" in url

# Determine URL prefix based on mode (rent/buy/commercial)
def get_mode_url_prefix(mode):
    mode = mode.strip().lower()
    if mode == "rent":
        return "https://www.squareyards.com/rent/property-for-rent-in-"
    elif mode == "buy":
        return "https://www.squareyards.com/sale/property-for-sale-in-"
    elif mode == "commercial":
        return "https://www.squareyards.com/sale/commercial-properties-in-"
    else:
        raise ValueError("Invalid mode. Choose 'rent', 'buy', or 'commercial'.")

# Extract property listings from HTML content
def extract_selected_fields(html):
    soup = BeautifulSoup(html, 'html.parser')
    listings = soup.select("article.listing-card.horizontal.two-line-description")
    results = []

    for card in listings:
        data = {}
        title_tag = card.select_one("h2.heading > a")
        data['Title'] = title_tag.get_text(strip=True) if title_tag else ""
        data['URL'] = title_tag['href'] if title_tag and title_tag.has_attr('href') else ""

        body_div = card.select_one("div.listing-body")
        data['Listing Page URL'] = body_div['data-url'] if body_div and body_div.has_attr("data-url") else ""

        loc = card.select_one("p.location > span")
        data['Location'] = loc.get_text(strip=True) if loc else ""

        price = card.select_one("p.listing-price")
        data['Price'] = price.get_text(strip=True) if price else ""

        info = card.select_one("ul.listing-information")
        data['Information'] = info.get_text(strip=True) if info else ""

        desc = card.select_one("div.description.redirectReadMore")
        data['Description'] = desc.get_text(strip=True) if desc else ""

        results.append(data)
    return results

# Return fallback city name using if-elif logic
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
        return city  # Default: no change

# Resume state filename generator
def get_state_filename(city, mode):
    return f"{mode}_{city.replace(' ', '_').lower()}_state.json"

# Delete old resume file
def delete_resume_file(city, mode):
    state_file = get_state_filename(city, mode)
    if os.path.exists(state_file):
        os.remove(state_file)
        logging.info(f"Deleted resume state file: {state_file}")

# Ask user whether to resume scraping from last page
def get_resume_page(city, mode):
    state_file = get_state_filename(city, mode)
    if os.path.exists(state_file):
        choice = input(f"Resume scraping {city} ({mode}) from last saved page? (yes/no): ").strip().lower()
        if choice == 'yes':
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    return state.get("last_page", 1)
            except:
                return 1
        else:
            delete_resume_file(city, mode)
            return 1
    return 1

# Save scraping progress
def save_resume_page(city, mode, page_number):
    state_file = get_state_filename(city, mode)
    try:
        with open(state_file, "w") as f:
            json.dump({"last_page": page_number}, f)
    except:
        pass

# Save a batch of listings to Excel
def save_batch(city, mode, data, batch_num):
    filename = f"{mode}_{city.replace(' ', '_').lower()}_batch_{batch_num}.xlsx"
    try:
        pd.DataFrame(data).to_excel(filename, index=False)
        logging.info(f"Saved batch {batch_num} -> {filename} ({len(data)} rows)")
    except Exception as e:
        logging.error(f"Failed to save batch {batch_num}: {e}")

# Combine all batch Excel files into one
def combine_batches(city, mode):
    city_prefix = f"{mode}_{city.replace(' ', '_').lower()}"
    all_batches = [f for f in os.listdir() if f.startswith(city_prefix + "_batch_") and f.endswith(".xlsx")]
    try:
        combined_data = pd.concat([pd.read_excel(f) for f in sorted(all_batches)], ignore_index=True)
        final_filename = f"{city_prefix}.xlsx"
        combined_data.to_excel(final_filename, index=False)
        logging.info(f"Combined all batches into {final_filename} ({len(combined_data)} rows)")
        for f in all_batches:
            try:
                os.remove(f)
                logging.info(f"Deleted batch file: {f}")
            except Exception as e:
                logging.warning(f"Failed to delete batch file {f}: {e}")
    except Exception as e:
        logging.error(f"Failed to combine batches for {city}: {e}")

# Main async function to scrape city listings
async def scrape_city(city, mode, url_prefix, playwright):
    retries = 0
    original_city = city
    page_number = get_resume_page(city, mode)
    batch = []
    batch_num = (page_number - 1) // BATCH_SIZE + 1
    city_slug = city.strip().lower().replace(" ", "-")
    full_url = url_prefix + city_slug

    while retries < MAX_RETRIES:
        try:
            browser = await playwright.chromium.launch(headless=False, timeout=0)
            context = await browser.new_context()
            page = await context.new_page()

            logging.info(f"Navigating to {full_url}")
            response = await page.goto(full_url, timeout=0)

            try:
                await page.wait_for_selector("article.listing-card", timeout=10000)
            except:
                # Try fallback city if original fails
                alt_city = get_fallback_city(city)
                if alt_city and alt_city != city:
                    logging.info(f"No listings found. Trying fallback city: {alt_city}")
                    city = alt_city
                    city_slug = city.strip().lower().replace(" ", "-")
                    full_url = url_prefix + city_slug
                    response = await page.goto(full_url, timeout=0)
                    await page.wait_for_selector("article.listing-card", timeout=10000)
                else:
                    logging.warning(f"No listings found and no fallback for {city}. Skipping.")
                    await browser.close()
                    return

            # Loop over paginated listing pages
            while True:
                logging.info(f"Scraping Page {page_number} of {city} ({mode})")
                html = await page.content()
                new_data = extract_selected_fields(html)

                if not new_data:
                    logging.warning("No listings found on this page. Ending scrape.")
                    break

                batch.extend(new_data)
                if len(batch) >= BATCH_SIZE:
                    save_batch(city, mode, batch, batch_num)
                    batch = []
                    batch_num += 1

                save_resume_page(city, mode, page_number)
                logging.info(f"Progress saved at page {page_number}")

                next_btn = await page.query_selector(f"a[rel='nofollow']:has-text('{page_number+1}')")
                if next_btn:
                    await next_btn.click()
                    await page.wait_for_timeout(4000)
                    page_number += 1
                else:
                    logging.info("No more pages.")
                    break

            if batch:
                save_batch(city, mode, batch, batch_num)

            await browser.close()
            combine_batches(city, mode)
            return

        except Exception as e:
            logging.error(f"Error scraping {city} (Retry {retries+1}/{MAX_RETRIES}): {e}")
        retries += 1

    logging.error(f"Failed to scrape {city} after {MAX_RETRIES} retries.")
