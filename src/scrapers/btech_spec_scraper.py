import asyncio
from typing import Dict
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from loguru import logger

class BtechSpecScraper:
    """
    Extracts detailed specifications from a specific B.TECH product URL.
    Updated to handle Custom Tailwind CSS Tables.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def get_specs(self, url: str) -> Dict[str, str]:
        logger.info(f"[BtechSpecScraper] Fetching specs for: {url}")
        specs: Dict[str, str] = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Scroll down to ensure the Specs section renders
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(3)
                
                html_content = await page.content()
                tree = HTMLParser(html_content)
                
                # --- Updated Strategy: Extracting from all table rows ---
                rows = tree.css('table tr, tbody tr')
                for row in rows:
                    tds = row.css('td')
                    th = row.css_first('th')
                    
                    key, val = None, None
                    
                    # Case 1: Standard Table (<th> for key, <td> for value)
                    if th and len(tds) >= 1:
                        key = th.text(strip=True)
                        val = tds[0].text(strip=True)
                    # Case 2: B.TECH's Tailwind format (Two <td> tags in a row)
                    elif len(tds) == 2:
                        key = tds[0].text(strip=True)
                        val = tds[1].text(strip=True)
                        
                    if key and val:
                        specs[key] = val
                            
                # --- Strategy 2: Definition Lists (Fallback) ---
                if not specs:
                    dts = tree.css('dt')
                    dds = tree.css('dd')
                    if len(dts) == len(dds) and len(dts) > 0:
                        for i in range(len(dts)):
                            specs[dts[i].text(strip=True)] = dds[i].text(strip=True)

            except Exception as e:
                logger.error(f"[BtechSpecScraper] Error scraping details: {e}")
            finally:
                await browser.close()
                
        logger.success(f"[BtechSpecScraper] Extracted {len(specs)} spec points.")
        return specs