import asyncio
import sqlite3
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool
from loguru import logger

# Import our powerful scrapers
from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.btech_scraper import BtechScraper
from src.scrapers.noon_scraper import NoonScraper

# Define Database Path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecommerce_cache.db")

def init_db():
    """Initializes the SQLite database for caching search results."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_cache (
            query TEXT,
            platform TEXT,
            product_name TEXT,
            price REAL,
            url TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Run DB initialization when this module loads
init_db()

def get_cached_results(query: str, max_price: float = None) -> str:
    """Checks if we have recent data (less than 24 hours old) for this exact query."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Calculate the time 24 hours ago
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    # We use LOWER() to make the search case-insensitive
    c.execute('''
        SELECT platform, product_name, price, url 
        FROM search_cache 
        WHERE LOWER(query) = ? AND timestamp > ?
    ''', (query.lower(), yesterday))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return None
        
    logger.success(f"📦 Found cached data for '{query}' in SQLite! Skipping live scraping.")
    
    # Format the cached data for the LLM
    formatted = f"Cached Search Results for '{query}':\n\n"
    platforms = set([row[0] for row in rows])
    
    for platform in platforms:
        formatted += f"### {platform}\n"
        platform_products = [r for r in rows if r[0] == platform]
        
        idx = 1
        for prod in platform_products[:3]: # Limit to top 3
            _, name, price, url = prod
            if max_price and price > max_price:
                continue
            formatted += f"{idx}. **{name}**\n   - Price: {price} EGP\n   - URL: {url}\n"
            idx += 1
        formatted += "\n"
        
    return formatted

def save_to_cache(query: str, platform: str, products):
    """Saves newly scraped products to the SQLite database for future use."""
    if not products or isinstance(products, Exception):
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for prod in products[:5]: # Save up to 5 products per platform to the cache
        c.execute('''
            INSERT INTO search_cache (query, platform, product_name, price, url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (query.lower(), platform, prod.product_name, prod.price, prod.url, now))
        
    conn.commit()
    conn.close()
    logger.info(f"💾 Saved {len(products[:5])} products from {platform} to cache.")


@tool
async def search_ecommerce_sites(query: str, max_price: float = None) -> str:
    """
    Searches Amazon, B.TECH, and Noon for products matching the user's request.
    Call this tool ONLY ONCE after gathering user requirements.
    
    Args:
        query: A concise, keyword-only search query (e.g., "Lenovo Thinkpad").
        max_price: The maximum budget in EGP (optional).
    """
    logger.warning(f"🚀 [TOOL TRIGGERED] Query: '{query}' | Budget: {max_price}")
    
    # 1. CHECK CACHE FIRST 🗄️
    cached_report = get_cached_results(query, max_price)
    if cached_report:
        return cached_report
        
    # 2. IF NOT IN CACHE, SCRAPE LIVE 🌐
    logger.info("No cache found. Firing up scrapers concurrently...")
    
    amazon = AmazonScraper(headless=True)
    btech = BtechScraper(headless=True)
    noon = NoonScraper(headless=True)
    
    results = await asyncio.gather(
        amazon.scrape(query),
        btech.scrape(query),
        noon.scrape(query),
        return_exceptions=True
    )
    
    amazon_data, btech_data, noon_data = results
    
    # 3. SAVE RESULTS TO CACHE 💾
    save_to_cache(query, "Amazon", amazon_data)
    save_to_cache(query, "B.TECH", btech_data)
    save_to_cache(query, "Noon", noon_data)
    
    # 4. FORMAT RESULTS FOR LLM 📝
    def format_results(platform_name: str, data) -> str:
        if isinstance(data, Exception):
            return f"### {platform_name}\nError fetching data.\n"
        if not data:
            return f"### {platform_name}\nNo products found.\n"
            
        formatted = f"### {platform_name}\n"
        for idx, prod in enumerate(data[:3]):
            if max_price and prod.price > max_price:
                continue
            formatted += f"{idx+1}. **{prod.product_name}**\n   - Price: {prod.price} EGP\n   - URL: {prod.url}\n"
        return formatted + "\n"

    final_report = f"Live Search Results for '{query}':\n\n"
    final_report += format_results("Amazon", amazon_data)
    final_report += format_results("B.TECH", btech_data)
    final_report += format_results("Noon", noon_data)
    
    return final_report