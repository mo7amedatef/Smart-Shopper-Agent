import asyncio
import sys
import os
from loguru import logger

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.btech_scraper import BtechScraper
from src.scrapers.btech_spec_scraper import BtechSpecScraper
from src.database.db_manager import DatabaseManager

async def main():
    logger.info("Starting Full B.TECH Integration Flow with Database...")
    
    # Initialize Tools and DB
    search_tool = BtechScraper(headless=True)
    spec_tool = BtechSpecScraper(headless=True)
    db = DatabaseManager() 
    await db.init_db()     
    
    search_query = "Lenovo IdeaPad"
    logger.info(f"Step 1: Searching for '{search_query}' on B.TECH...")
    
    search_results = await search_tool.scrape(search_query)
    
    if not search_results:
        logger.error("Search failed or no results found.")
        return
        
    top_product = search_results[0]
    logger.success(f"Found Top Product: {top_product.product_name} | Price: {top_product.price} EGP")
    
    logger.info(f"Step 2: Deep diving into URL to extract specifications...")
    deep_specs = await spec_tool.get_specs(str(top_product.url))
    
    if deep_specs:
        top_product.specifications.update(deep_specs)
        logger.success("Specifications merged successfully!")
    else:
        logger.warning("No specs found, but continuing with basic data...")
        
    # --- Step 3: Saving to Database ---
    logger.info("Step 3: Saving enriched B.TECH data to the Database...")
    await db.upsert_product(top_product)
    logger.success("B.TECH Data securely stored in ecommerce_data.db! 🎉")

if __name__ == "__main__":
    asyncio.run(main())