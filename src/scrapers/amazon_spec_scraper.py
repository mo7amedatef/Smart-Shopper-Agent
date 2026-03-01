import asyncio
from typing import Dict
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from loguru import logger

class AmazonSpecScraper:
    """
    A specialized tool for the AI Agent to extract detailed specifications
    from a specific Amazon product URL.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def get_specs(self, url: str) -> Dict[str, str]:
        logger.info(f"[AmazonSpecScraper] Fetching specs for: {url}")
        specs: Dict[str, str] = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US"
            )
            page = await context.new_page()
            
            try:
                # Go to the specific product page
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Scroll down to ensure tables are loaded
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(2)
                
                html_content = await page.content()
                tree = HTMLParser(html_content)
                
                # --- Strategy 1: Extract Technical Details Table ---
                # This table usually contains RAM, OS, Processor, etc.
                tech_rows = tree.css('#productDetails_techSpec_section_1 tr')
                for row in tech_rows:
                    th = row.css_first('th')
                    td = row.css_first('td')
                    if th and td:
                        # Clean up text (Amazon adds hidden directional characters sometimes)
                        key = th.text(strip=True).replace('\u200f', '').replace('\u200e', '')
                        val = td.text(strip=True).replace('\u200f', '').replace('\u200e', '')
                        specs[key] = val

                # --- Strategy 2: Extract Product Overview Table (Fallback) ---
                if not specs:
                    overview_rows = tree.css('.a-normal.a-spacing-micro tr')
                    for row in overview_rows:
                        tds = row.css('td')
                        if len(tds) == 2:
                            key = tds[0].text(strip=True)
                            val = tds[1].text(strip=True)
                            specs[key] = val

                # --- Strategy 3: Extract "About this item" Bullets ---
                feature_bullets = tree.css('#feature-bullets li span.a-list-item')
                if feature_bullets:
                    features = [bullet.text(strip=True) for bullet in feature_bullets if bullet.text(strip=True)]
                    if features:
                        # Join bullets into a single descriptive string
                        specs['About'] = " | ".join(features)

            except Exception as e:
                logger.error(f"[AmazonSpecScraper] Error scraping details: {e}")
            finally:
                await browser.close()
                
        logger.success(f"[AmazonSpecScraper] Extracted {len(specs)} spec points.")
        return specs