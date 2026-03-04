import asyncio
import re
from datetime import datetime
from typing import List
from urllib.parse import quote
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from loguru import logger

from src.scrapers.base_scraper import BaseScraper
from src.schemas.product import ProductDetail

class NoonScraper(BaseScraper):
    """
    Scraper for Noon Egypt.
    Updated for their Next.js dynamic classes using stable data-qa attributes.
    """

    def _is_relevant(self, query: str, title: str) -> bool:
        query_lower = query.lower()
        title_lower = title.lower()
        
        keywords = query_lower.split()
        matches = [word for word in keywords if word in title_lower]
        
        arabic_map = {"lenovo": "لينوفو", "samsung": "سامسونج", "iphone": "ايفون", "apple": "ابل"}
        for eng, ara in arabic_map.items():
            if eng in query_lower and ara in title_lower:
                matches.append(eng)

        negative_keywords = ["case", "cover", "protector", "screen", "glass", "جراب", "سكرينة", "كفر", "وصلة", "mouse", "ماوس", "bag", "شنطة", "monitor", "شاشة"]
        if any(neg in title_lower for neg in negative_keywords):
            return False

        return len(matches) >= 1

    async def scrape(self, product_query: str) -> List[ProductDetail]:
        results: List[ProductDetail] = []
        encoded_query = quote(product_query)
        search_url = f"https://www.noon.com/egypt-en/search/?q={encoded_query}"
        
        logger.info(f"[NoonScraper] Searching for '{product_query}' on Noon...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                # We changed this to domcontentloaded to prevent Timeout errors
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5) # Wait for React components to hydrate
                
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(3)

                html_content = await page.content()
                tree = HTMLParser(html_content)
                
                # Target all anchor links that represent products (containing '/p/')
                items = tree.css('a[href*="/p/"]')
                
                for item in items:
                    raw_url = item.attributes.get('href', '')
                    if not raw_url:
                        continue
                        
                    url = f"https://www.noon.com{raw_url}" if raw_url.startswith('/') else raw_url
                    
                    # 1. Title Extraction based on data-qa attribute (from your Inspect)
                    title_node = item.css_first('[data-qa="plp-product-box-name"]')
                    
                    title = ""
                    if title_node:
                        # Grab from title attribute (cleaner) or text
                        title = title_node.attributes.get('title', '') or title_node.text(strip=True)
                    else:
                        # Fallback
                        img_node = item.css_first('img')
                        if img_node:
                            title = img_node.attributes.get('alt', '')
                            
                    if not title or not self._is_relevant(product_query, title):
                        continue

                    # 2. Price Extraction based on data-qa attribute (from your Inspect)
                    price_node = item.css_first('[data-qa="plp-product-box-price"]')
                    price_value = 0.0
                    
                    if price_node:
                        price_text = price_node.text(strip=True)
                        # Extract the number (e.g., from "EGP 29,600")
                        price_match = re.search(r'([\d,]+(?:\.\d+)?)', price_text)
                        if price_match:
                            raw_price = price_match.group(1).replace(',', '')
                            price_value = float(raw_price)

                    # 3. Validation and Mapping (Avoid duplicate DOM entries)
                    if price_value > 0 and not any(p.url == url for p in results):
                        product = ProductDetail(
                            source_website="Noon",
                            product_name=title,
                            price=price_value,
                            currency="EGP",
                            url=url,
                            specifications={},
                            is_available=True,
                            scraped_at=datetime.now().isoformat()
                        )
                        results.append(product)
                    
                    if len(results) >= 5: 
                        break

            except Exception as e:
                logger.error(f"[NoonScraper] Error: {e}")
            finally:
                await browser.close()
                
        logger.success(f"[NoonScraper] Successfully scraped {len(results)} products!")
        return results