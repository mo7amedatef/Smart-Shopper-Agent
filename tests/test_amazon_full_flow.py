import asyncio
import sys
import os
import json
from loguru import logger

# Ensure the 'src' directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.amazon_spec_scraper import AmazonSpecScraper

async def main():
    logger.info("Starting Full Amazon Integration Flow...")
    
    # 1. Initialize both tools
    search_tool = AmazonScraper(headless=True)
    spec_tool = AmazonSpecScraper(headless=True)
    
    search_query = "Lenovo IdeaPad"
    logger.info(f"Step 1: Searching for '{search_query}'...")
    
    # 2. Execute Search
    search_results = await search_tool.scrape(search_query)
    
    if not search_results:
        logger.error("Search failed or no results found.")
        return
        
    # Get the best (first) result
    top_product = search_results[0]
    logger.success(f"Found Top Product: {top_product.product_name} | Price: {top_product.price} EGP")
    
    # 3. Deep Dive for Specs
    logger.info(f"Step 2: Deep diving into URL to extract specifications...")
    deep_specs = await spec_tool.get_specs(str(top_product.url))
    
    # 4. Merge deep specs into our Pydantic model
    if deep_specs:
        # Update the specifications dictionary inside the Pydantic model
        top_product.specifications.update(deep_specs)
        logger.success("Specifications merged successfully!")
    else:
        logger.warning("Could not extract deep specifications.")
        
    # 5. Final Output Showcase
    logger.info("=== FINAL ENRICHED PRODUCT DATA ===")
    # Using model_dump_json() from Pydantic to get a clean JSON string
    print(top_product.model_dump_json(indent=4))

if __name__ == "__main__":
    asyncio.run(main())