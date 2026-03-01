import asyncio
import sys
import os
import json
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.amazon_spec_scraper import AmazonSpecScraper

async def main():
    # We use headless=False so you can see it navigating to the product page
    scraper = AmazonSpecScraper(headless=False)
    
    # Using one of the URLs you successfully scraped earlier (Lenovo Laptop)
    test_url = "https://www.amazon.eg/dp/B0D3J7ZX58"
    
    logger.info("Initializing Spec Scraper Tool Test...")
    specs = await scraper.get_specs(test_url)
    
    if specs:
        logger.success("Specifications Extracted Successfully:")
        # Print as formatted JSON to see the key-value pairs clearly
        print(json.dumps(specs, indent=4, ensure_ascii=False))
    else:
        logger.warning("No specs found. Check the selectors or the URL.")
        
    await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())