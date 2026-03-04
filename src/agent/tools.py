import asyncio
from langchain_core.tools import tool
from loguru import logger

# Import our powerful scrapers!
from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.btech_scraper import BtechScraper
from src.scrapers.noon_scraper import NoonScraper

@tool
async def search_ecommerce_sites(query: str, max_price: float = None) -> str:
    """
    Searches Amazon, B.TECH, and Noon for products matching the user's request.
    Call this tool ONLY ONCE after you have completely gathered all the user's requirements 
    (product type, usage, and budget) and you are ready to fetch real data.
    
    Args:
        query: A concise, optimized search query (e.g., "Lenovo IdeaPad Core i5").
        max_price: The maximum budget in EGP (optional).
    """
    logger.warning(f"🚀 [TOOL TRIGGERED] Fetching REAL DATA for: '{query}' | Budget: {max_price}")
    
    # Initialize scrapers in Headless mode (invisible to the user)
    amazon = AmazonScraper(headless=True)
    btech = BtechScraper(headless=True)
    noon = NoonScraper(headless=True)
    
    # Run all scrapers concurrently to save time
    logger.info("Firing up Amazon, B.TECH, and Noon scrapers concurrently...")
    
    # asyncio.gather runs them in parallel. return_exceptions=True prevents one crash from stopping the others
    results = await asyncio.gather(
        amazon.scrape(query),
        btech.scrape(query),
        noon.scrape(query),
        return_exceptions=True
    )
    
    amazon_data, btech_data, noon_data = results
    
    # Helper function to format the Pydantic models into a clean text for the LLM
    def format_results(platform_name: str, data) -> str:
        if isinstance(data, Exception):
            logger.error(f"[{platform_name}] Scraper failed: {data}")
            return f"### {platform_name}\nError fetching data from this platform.\n"
        
        if not data:
            return f"### {platform_name}\nNo products found.\n"
        
        formatted = f"### {platform_name}\n"
        # Limit to top 3 products per platform to keep the LLM context window clean
        for idx, prod in enumerate(data[:3]):
            # Apply budget filtering if max_price is provided by the LLM
            if max_price and prod.price > max_price:
                continue
                
            formatted += f"{idx+1}. **{prod.product_name}**\n"
            formatted += f"   - Price: {prod.price} EGP\n"
            formatted += f"   - URL: {prod.url}\n"
        return formatted + "\n"

    # Compile the final report for the LLM
    final_report = f"Real Search Results for '{query}':\n\n"
    final_report += format_results("Amazon", amazon_data)
    final_report += format_results("B.TECH", btech_data)
    final_report += format_results("Noon", noon_data)
    
    logger.success("Data successfully fetched and formatted for the LLM!")
    return final_report