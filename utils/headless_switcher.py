from playwright.async_api import async_playwright

async def try_headless_with_fallback(url, scraper_func):
    """
    Tries to run the scraper function in headless mode first.
    If it fails, retries in headful (visible) mode.

    Args:
        url (str): The URL to scrape.
        scraper_func (coroutine): The scraping function to call, should accept (page, url).
    """
    try:
        return await run_scraper(url, scraper_func, headless=True)
    except Exception as e:
        print(f"Headless mode failed: {e}. Retrying in headful mode...")
        return await run_scraper(url, scraper_func, headless=False)

async def run_scraper(url, scraper_func, headless=True):
    """
    Launches Playwright, navigates to URL, and executes the provided scraper function.

    Args:
        url (str): The page to scrape.
        scraper_func (coroutine): Function that receives (page, url).
        headless (bool): Whether to run in headless mode.

    Returns:
        Any: Whatever the scraper_func returns.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        result = await scraper_func(page, url)
        await browser.close()
        return result
