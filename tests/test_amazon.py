import asyncio
import sys
import os
from loguru import logger

# Ensure the 'src' directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.amazon_scraper import AmazonScraper

async def main():
    logger.info("Initializing Amazon Scraper...")
    
    # Setting headless=False so you can watch the browser in action.
    # Once you confirm it works, you can change it back to True for production.
    scraper = AmazonScraper(headless=False)
    
    search_query = "Lenovo IdeaPad"
    logger.info(f"Searching for: '{search_query}' on Amazon Egypt")
    
    try:
        results = await scraper.scrape(search_query)
        
        if not results:
            logger.warning("No results returned. Amazon might still be blocking, or the selectors need another tweak.")
        else:
            logger.success(f"Successfully scraped {len(results)} products!")
            
            for index, product in enumerate(results, start=1):
                logger.info(f"--- Product {index} ---")
                logger.info(f"Name : {product.product_name}")
                logger.info(f"Price: {product.price} {product.currency}")
                logger.info(f"URL  : {product.url}")
                
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    finally:
        logger.info("Test finished. Keeping the browser open for 5 seconds to inspect...")
        # Keeps the browser open briefly so you can visually confirm the page state
        await asyncio.sleep(5)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())