import asyncio
import sys
import os
import json
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.noon_spec_scraper import NoonSpecScraper

async def main():
   
    scraper = NoonSpecScraper(headless=False)
    
    
    test_url = "https://www.noon.com/egypt-en/ideapad-5-laptop-with-15-6-inch-display-core-i5-1235u-processor-16gb-ram-512gb-ssd-2gb-nvidia-geforce-mx550-graphics-card-windows-11-home-english-arabic-storm-grey/N70048443V/p/?o=b3aa78e1e41a164c"
    
    logger.info("Initializing Noon Spec Scraper Tool...")
    specs = await scraper.get_specs(test_url)
    
    if specs:
        logger.success("Specifications Extracted Successfully:")
        print(json.dumps(specs, indent=4, ensure_ascii=False))
    else:
        logger.warning("No specs found. We might need to inspect the Specs Table CSS classes!")
        
    await asyncio.sleep(4)

if __name__ == "__main__":
    asyncio.run(main())