import asyncio
import sys
import os
import json
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.btech_spec_scraper import BtechSpecScraper

async def main():
    # بنخليه False عشان نتفرج على المتصفح وهو بينزل لجدول المواصفات
    scraper = BtechSpecScraper(headless=False)
    
    # حطيت هنا أول لينك لابتوب طلعلك في التست الأخير
    test_url = "https://btech.com/en/p/lenovo-ideapad-slim-3-15iru8-laptop-intel-i3-1315u-256gb-ssd-8gb-ram-15-6-dos-grey?offering_id=84d57b15-d6b3-4ebe-b09d-a0642bf4c4da"
    
    logger.info("Initializing B.TECH Spec Scraper Tool...")
    specs = await scraper.get_specs(test_url)
    
    if specs:
        logger.success("Specifications Extracted Successfully:")
        print(json.dumps(specs, indent=4, ensure_ascii=False))
    else:
        logger.warning("No specs found. We might need to inspect the Specs Table CSS classes!")
        
    await asyncio.sleep(4)

if __name__ == "__main__":
    asyncio.run(main())