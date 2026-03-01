import asyncio
from typing import List
from urllib.parse import quote
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser

from src.scrapers.base_scraper import BaseScraper
from src.schemas.product import ProductDetail

class AmazonScraper(BaseScraper):
    """
    Scraper implementation for Amazon Egypt using Playwright and Selectolax.
    Inherits from BaseScraper.
    """

    async def scrape(self, product_query: str) -> List[ProductDetail]:
        results: List[ProductDetail] = []
        encoded_query = quote(product_query)
        search_url = f"https://www.amazon.eg/-/en/s?k={encoded_query}"

        async with async_playwright() as p:
            # Launch browser (headless by default based on __init__)
            browser = await p.chromium.launch(headless=self.headless)
            
            # Set a realistic User-Agent to avoid immediate bot detection
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Go to Amazon search page and wait for the network to be mostly idle
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                
                # Wait for the main search results container to appear
                await page.wait_for_selector('div.s-main-slot', timeout=10000)
                
                # Extract the HTML content
                html_content = await page.content()
                
                # Parse with Selectolax for high performance
                tree = HTMLParser(html_content)
                
                # Find all product containers
                # Amazon frequently changes classes, but 's-result-item' is relatively stable
                items = tree.css('div[data-component-type="s-search-result"]')
                
                for item in items:
                    # Title
                    title_node = item.css_first('h2 a span')
                    if not title_node:
                        continue
                    title = title_node.text(strip=True)
                    
                    # Price (Amazon splits whole and fraction)
                    price_node = item.css_first('span.a-price-whole')
                    price_text = price_node.text(strip=True) if price_node else "0"
                    price_value = self.clean_price(price_text)
                    
                    # URL
                    link_node = item.css_first('h2 a')
                    url_suffix = link_node.attributes.get('href', '') if link_node else ""
                    full_url = f"https://www.amazon.eg{url_suffix}" if url_suffix.startswith('/') else url_suffix
                    
                    # Skip items without a valid price (like sponsored ads missing price tags)
                    if price_value <= 0:
                        continue
                        
                    product = ProductDetail(
                        source_website="Amazon Egypt",
                        product_name=title,
                        price=price_value,
                        url=full_url,
                        is_available=True
                    )
                    results.append(product)
                    
                    # Limit to top 5 results to save processing time later
                    if len(results) >= 5:
                        break

            except Exception as e:
                print(f"[AmazonScraper] Error occurred: {e}")
            finally:
                await browser.close()
                
        return results