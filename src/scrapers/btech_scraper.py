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

class BtechScraper(BaseScraper):
    """
    Scraper for B.TECH Egypt.
    Updated for their new Tailwind CSS / React Frontend.
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

        negative_keywords = ["case", "cover", "protector", "screen", "glass", "monitor", "شاشة", "جراب", "سكرينة", "كفر", "وصلة", "mouse", "ماوس", "bag", "شنطة"]
        if any(neg in title_lower for neg in negative_keywords):
            return False

        return len(matches) >= 1

    async def scrape(self, product_query: str) -> List[ProductDetail]:
        results: List[ProductDetail] = []
        encoded_query = quote(product_query)
        # The new B.TECH search URL
        search_url = f"https://btech.com/en/s?q={encoded_query}"
        
        logger.info(f"[BtechScraper] Searching for '{product_query}' on B.TECH...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4) # B.TECH's new frontend takes a moment to hydrate
                
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(2)

                html_content = await page.content()
                tree = HTMLParser(html_content)
                
                # Based on your Inspect, products are wrapped in <article> tags
                items = tree.css('article')
                
                for item in items:
                    # 1. Title & URL Extraction (from the 'a' tag)
                    link_node = item.css_first('a')
                    if not link_node:
                        continue
                        
                    # Extract title from h2 if exists, else fallback to 'title' attribute
                    h2_node = link_node.css_first('h2')
                    title = h2_node.text(strip=True) if h2_node else link_node.attributes.get('title', '')
                    
                    raw_url = link_node.attributes.get('href', '')
                    # Fix relative URLs
                    url = f"https://btech.com{raw_url}" if raw_url.startswith('/') else raw_url
                    
                    if not title or not url:
                        continue
                    
                    if not self._is_relevant(product_query, title):
                        continue

                    # 2. Price Extraction using Regex on the whole article text
                    article_text = item.text(strip=True)
                    # Look for "EGP" followed by optional space, then numbers and commas
                    price_match = re.search(r'EGP\s*([\d,]+)', article_text)
                    
                    if price_match:
                        raw_price = price_match.group(1).replace(',', '')
                        price_value = float(raw_price)
                    else:
                        price_value = 0.0

                    if price_value > 0:
                        # 4. Data Mapping
                        product = ProductDetail(
                            source_website="B.TECH",
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
                logger.error(f"[BtechScraper] Error: {e}")
            finally:
                await browser.close()
                
        logger.success(f"[BtechScraper] Successfully scraped {len(results)} products!")
        return results