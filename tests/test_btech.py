import asyncio
import sys
import os
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.btech_scraper import BtechScraper

async def main():
    # خليها False أول مرة عشان نشوف المتصفح بيفتح إزاي
    scraper = BtechScraper(headless=False)
    
    query = "Lenovo IdeaPad"
    results = await scraper.scrape(query)
    
    if results:
        for idx, res in enumerate(results, 1):
            logger.info(f"--- Product {idx} ---")
            logger.info(f"Name : {res.product_name}")
            logger.info(f"Price: {res.price} {res.currency}")
            logger.info(f"URL  : {res.url}")
    else:
        logger.warning("No products found. B.TECH might have changed their HTML classes.")
        
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())