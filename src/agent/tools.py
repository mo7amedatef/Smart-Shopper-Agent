import asyncio
import sqlite3
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool
from loguru import logger

# Import our scrapers
from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.btech_scraper import BtechScraper
from src.scrapers.noon_scraper import NoonScraper

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecommerce_cache.db")

def init_db():
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

init_db()

def get_cached_results(query: str, max_price: float = None) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('''
        SELECT platform, product_name, price, url 
        FROM search_cache 
        WHERE LOWER(query) = ? AND timestamp > ?
    ''', (str(query).lower(), yesterday))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return None
        
    logger.success(f"📦 Cache HIT for '{query}'! Skipping live scraping.")
    
    formatted = f"Cached Search Results for '{query}':\n\n"
    platforms = set([row[0] for row in rows])
    
    for platform in platforms:
        formatted += f"### {platform}\n"
        platform_products = [r for r in rows if r[0] == platform]
        
        idx = 1
        for prod in platform_products[:3]: 
            _, name, price, url = prod
            if max_price and price > max_price:
                continue
            formatted += f"{idx}. **{name}**\n   - Price: {price} EGP\n   - URL: {url}\n"
            idx += 1
        formatted += "\n"
        
    return formatted

def save_to_cache(query: str, platform: str, products):
    if not products or isinstance(products, Exception):
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for prod in products[:5]: 
        # Forcing primitive types to safely store in SQLite
        safe_url = str(prod.url)
        safe_name = str(prod.product_name)
        safe_price = float(prod.price)
        
        c.execute('''
            INSERT INTO search_cache (query, platform, product_name, price, url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(query).lower(), str(platform), safe_name, safe_price, safe_url, now))
        
    conn.commit()
    conn.close()
    logger.info(f"💾 Saved products from {platform} to cache.")

@tool
async def search_ecommerce_sites(query: str, max_price: float = None) -> str:
    """
    Searches Amazon, B.TECH, and Noon for products matching the request.
    """
    logger.warning(f"🚀 [TOOL TRIGGERED] Query: '{query}' | Budget: {max_price}")
    
    cached_report = get_cached_results(query, max_price)
    if cached_report:
        return cached_report
        
    logger.info("No cache found. Running scrapers concurrently...")
    
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
    
    save_to_cache(query, "Amazon", amazon_data)
    save_to_cache(query, "B.TECH", btech_data)
    save_to_cache(query, "Noon", noon_data)
    
    def format_results(platform_name: str, data) -> str:
        if isinstance(data, Exception):
            return f"### {platform_name}\nError fetching data.\n"
        if not data:
            return f"### {platform_name}\nNo products found.\n"
            
        formatted = f"### {platform_name}\n"
        for idx, prod in enumerate(data[:3]):
            if max_price and prod.price > max_price:
                continue
            safe_url = str(prod.url)
            formatted += f"{idx+1}. **{prod.product_name}**\n   - Price: {prod.price} EGP\n   - URL: {safe_url}\n"
        return formatted + "\n"

    final_report = f"Live Search Results for '{query}':\n\n"
    final_report += format_results("Amazon", amazon_data)
    final_report += format_results("B.TECH", btech_data)
    final_report += format_results("Noon", noon_data)
    
    return final_report