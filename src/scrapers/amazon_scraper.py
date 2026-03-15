import asyncio
import re
from playwright.async_api import async_playwright
from pydantic import BaseModel, HttpUrl
from loguru import logger

class Product(BaseModel):
    product_name: str
    price: float
    url: HttpUrl

class AmazonScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape(self, query: str):
        logger.info(f"[AmazonScraper] Searching for '{query}'...")
        products = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                search_url = f"https://www.amazon.eg/s?k={query.replace(' ', '+')}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                
                try:
                    await page.wait_for_selector("div[data-component-type='s-search-result']", timeout=10000)
                except:
                    logger.warning("[AmazonScraper] Blocked or no results.")
                    await browser.close()
                    return products
                    
                items = await page.query_selector_all("div[data-component-type='s-search-result']")
                
                # Increased to 8 to ensure we catch valid non-sponsored products
                for item in items[:8]: 
                    try:
                        # 1. Ultra-resilient Title extraction (Just look for the h2 tag)
                        title_el = await item.query_selector("h2")
                        if not title_el:
                            continue
                        full_title = await title_el.inner_text()
                        
                        # 2. Resilient Price extraction
                        price_el = await item.query_selector(".a-price-whole")
                        if not price_el:
                            continue
                        price_text = await price_el.inner_text()
                        
                        clean_price = re.sub(r'[^\d.]', '', price_text)
                        if not clean_price or clean_price == '.':
                            continue
                        price = float(clean_price)
                        
                        # 3. Resilient Link extraction (Fallback added)
                        link_el = await item.query_selector("h2 a")
                        if not link_el:
                            link_el = await item.query_selector("a.a-link-normal")
                            
                        if not link_el:
                            continue
                            
                        link_href = await link_el.get_attribute("href")
                        full_url = link_href if link_href.startswith("http") else f"https://www.amazon.eg{link_href}"
                        
                        products.append(Product(
                            product_name=full_title.strip(),
                            price=price,
                            url=full_url
                        ))
                    except Exception as e:
                        continue
                        
                await browser.close()
                logger.success(f"[AmazonScraper] Successfully scraped {len(products)} products with full specs!")
                return products
        except Exception as e:
            logger.error(f"[AmazonScraper] Error: {e}")
            return e