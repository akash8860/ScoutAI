import os  # File and directory operations
import importlib.util  # Check if a module is installed
import pandas as pd  # Data manipulation and Excel export
import re  # Regex for sanitizing filenames
import requests  # Fetching HTML pages
import time  # Sleep between requests
import json  # Read/write resume state
from bs4 import BeautifulSoup  # HTML parser
from bs4.element import Tag  # Type check for HTML tags

# Fallback mapping using if-elif logic
# This module scrapes property listings from MagicBricks and handles city name fallbacks
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
    elif city == 'hyd':
        return 'hyderabad'
    else:
        return city

# Check if openpyxl is installed
def is_openpyxl_available():  
    return importlib.util.find_spec("openpyxl") is not None

# Replace unsafe characters in filenames
def sanitize_filename(name):  
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

# Mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'  
}

# Get HTML content from a URL
def fetch_webpage(url):  
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# Generate filename for storing progress
def get_state_filename(city):  
    return f"magicbricks_{sanitize_filename(city).lower()}_state.json"

# Ask user if resume is needed and return saved page
def get_resume_page(city):  
    state_file = get_state_filename(city)
    if os.path.exists(state_file):
        choice = input(f"Resume scraping {city} from last saved page? (yes/no): ").strip().lower()
        if choice == 'yes':
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    return state.get("last_page", 1)
            except:
                return 1
        else:
            os.remove(state_file)
    return 1

# Save the current page number
def save_resume_page(city, page_number):  
    state_file = get_state_filename(city)
    try:
        with open(state_file, "w") as f:
            json.dump({"last_page": page_number}, f)
    except Exception as e:
        print(f"Could not save resume file: {e}")

# Parse listings from one page
def scrape_page(url):  
    page = fetch_webpage(url)
    if not page:
        return []

    soup = BeautifulSoup(page, "html.parser")
    main_cards = soup.find_all('div', class_='mb-srp__card')
    all_card_data = []

    for card in main_cards:
        card_data = {}
        if isinstance(card, Tag):
            title_tag = card.find('h2', class_='mb-srp__card--title')
            card_data['Property Name'] = title_tag.get_text(strip=True) if title_tag else None

            summary_list = card.find_all('div', class_='mb-srp__card__summary__list--item')
            for item in summary_list:
                if isinstance(item, Tag):
                    label = item.find('div', class_='mb-srp__card__summary--label')
                    value = item.find('div', class_='mb-srp__card__summary--value')
                    if label and value:
                        key = item.get('data-summary') or label.get_text(strip=True)
                        card_data[key] = value.get_text(strip=True)

            price_block = card.find('div', class_='mb-srp__card__estimate')
            if price_block:
                price_amount = price_block.find('div', class_='mb-srp__card__price--amount')
                price_psqft = price_block.find('div', class_='mb-srp__card__price--size')
                card_data['Total Price'] = price_amount.get_text(strip=True) if price_amount else None
                card_data['Price per Sqft'] = price_psqft.get_text(strip=True) if price_psqft else None

        all_card_data.append(card_data)

    return all_card_data

# Loop over all paginated pages
def scrape_multiple_pages(base_url, city):  
    all_results = []
    page = get_resume_page(city)

    while True:
        full_url = f"{base_url}&page={page}"
        print(f"Scraping page {page}...")
        page_data = scrape_page(full_url)

        if not page_data:
            print(f"Finished scraping. Total pages scraped: {page - 1}")
            break

        all_results.extend(page_data)
        save_resume_page(city, page)
        page += 1
        time.sleep(2)

    return all_results

# Check if URL is for MagicBricks
def can_handle(url: str) -> bool:  
    return "magicbricks.com" in url

# CLI mode for running independently
if __name__ == "__main__":  
    if not is_openpyxl_available():
        print("openpyxl is not installed. Please install it using: pip install openpyxl")
    else:
        excel_path = input("Enter Excel file path with city mappings: ").strip()
        df_cities = pd.read_excel(excel_path)
        cities = df_cities.to_dict("records")

        base_url_template = (
            "https://www.magicbricks.com/property-for-rent/commercial-real-estate"
            "?proptype=Commercial-Office-Space,Office-ITPark-SEZ,Commercial-Shop,"
            "Commercial-Showroom,Commercial-Land,Industrial-Land,Warehouse/-Godown,"
            "Industrial-Building,Industrial-Shed&cityName={}"
        )

        save_dir = os.path.join(os.getcwd(), "scraped_data")
        os.makedirs(save_dir, exist_ok=True)

        for city_row in cities:
            original_city = city_row.get("original_city", "").strip()
            platform_city = city_row.get("magicbricks_city", original_city).strip()
            fallback_city = get_fallback_city(platform_city)

            if fallback_city != platform_city:
                print(f"Using fallback: {platform_city} → {fallback_city}")
            platform_city = fallback_city

            print(f"\nNow scraping city: {original_city} as {platform_city}")
            formatted_city = platform_city.replace(" ", "%20")
            city_url = base_url_template.format(formatted_city)

            city_data = scrape_multiple_pages(city_url, platform_city)

            if city_data:
                df = pd.DataFrame(city_data)
                filename = f"{sanitize_filename(original_city)}_Properties.xlsx"
                full_path = os.path.join(save_dir, filename)
                df.to_excel(full_path, index=False)
                print(f"Saved {len(df)} records for {original_city} to {filename}")
            else:
                print(f"No data collected for {original_city}")
