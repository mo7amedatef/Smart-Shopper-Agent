import asyncio
from typing import Dict
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from loguru import logger

class NoonSpecScraper:
    """
    Extracts detailed specifications from a specific Noon product URL.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def get_specs(self, url: str) -> Dict[str, str]:
        logger.info(f"[NoonSpecScraper] Fetching specs for: {url}")
        specs: Dict[str, str] = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Scroll down in steps to trigger lazy-loaded specification tables
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(2)
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(3)
                
                html_content = await page.content()
                tree = HTMLParser(html_content)
                
                # Noon usually uses standard tables for specifications
                rows = tree.css('table tr, tbody tr')
                for row in rows:
                    tds = row.css('td')
                    # Expecting two columns: Key (e.g., "Processor") and Value (e.g., "Core i5")
                    if len(tds) >= 2:
                        key = tds[0].text(strip=True)
                        val = tds[1].text(strip=True)
                        if key and val:
                            specs[key] = val

            except Exception as e:
                logger.error(f"[NoonSpecScraper] Error scraping details: {e}")
            finally:
                await browser.close()
                
        logger.success(f"[NoonSpecScraper] Extracted {len(specs)} spec points.")
        return specs