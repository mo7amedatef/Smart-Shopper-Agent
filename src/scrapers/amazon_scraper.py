import asyncio
import re
from typing import List
from urllib.parse import quote
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from loguru import logger

from src.scrapers.base_scraper import BaseScraper
from src.schemas.product import ProductDetail

class AmazonScraper(BaseScraper):
    """
    Final Hybrid Scraper for Amazon Egypt. 
    Handles Arabic/English titles and cleans duplicate prices.
    """

    def _is_relevant(self, query: str, title: str) -> bool:
        query_lower = query.lower()
        title_lower = title.lower()
        
        # Split query into words and check if MOST of them (or their Arabic equivalents) exist
        # For simplicity, we check if the main brand or model exists
        keywords = query_lower.split()
        matches = [word for word in keywords if word in title_lower]
        
        # Support for common Arabic brands if English fails
        arabic_map = {"lenovo": "لينوفو", "samsung": "سامسونج", "iphone": "ايفون", "apple": "ابل"}
        for eng, ara in arabic_map.items():
            if eng in query_lower and ara in title_lower:
                matches.append(eng)

        # Blacklist to avoid accessories
        negative_keywords = ["case", "cover", "protector", "screen", "glass", "جراب", "سكرينة", "كفر"]
        if any(neg in title_lower for neg in negative_keywords):
            return False

        return len(matches) >= 1 # At least one core keyword matched

    async def scrape(self, product_query: str) -> List[ProductDetail]:
        results: List[ProductDetail] = []
        encoded_query = quote(product_query)
        search_url = f"https://www.amazon.eg/-/en/s?k={encoded_query}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                html_content = await page.content()
                tree = HTMLParser(html_content)
                items = tree.css('div[data-asin]')
                
                for item in items:
                    asin = item.attributes.get('data-asin')
                    if not asin: continue

                    # Better Title Extraction
                    title_node = item.css_first('h2')
                    title = title_node.text(strip=True) if title_node else "No Title"
                    
                    if not self._is_relevant(product_query, title):
                        continue

                    # Clean Price Extraction (Regex to find the first numeric price)
                    price_node = item.css_first('.a-price-whole') or item.css_first('.a-price')
                    if price_node:
                        raw_price = price_node.text(strip=True)
                        # Extract only numbers and dots
                        clean_p = re.sub(r'[^\d.]', '', raw_price.split('.')[0])
                        price_value = float(clean_p) if clean_p else 0
                    else:
                        price_value = 0

                    if price_value > 0:
                        # Construct URL
                        full_url = f"https://www.amazon.eg/dp/{asin}"
                        
                        results.append(ProductDetail(
                            source_website="Amazon Egypt",
                            product_name=title,
                            price=price_value,
                            url=full_url,
                            is_available=True
                        ))
                    
                    if len(results) >= 5: break

            except Exception as e:
                logger.error(f"Scrape Error: {e}")
            finally:
                await browser.close()
                
        return results