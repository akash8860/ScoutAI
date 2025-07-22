from playwright.async_api import async_playwright

async def analyze_dom_structure(url):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        html = await page.content()

        if "Load More" in html or "Show More" in html:
            return "scroll"
        elif any(p in html for p in ["pagination", "page="]):
            return "pagination"
        elif "property-card" in html or "listing" in html:
            return "scroll"
        else:
            return "unknown"
