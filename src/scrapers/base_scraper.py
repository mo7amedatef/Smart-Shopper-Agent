from abc import ABC, abstractmethod
from typing import List
from src.schemas.product import ProductDetail

class BaseScraper(ABC):
    """
    Abstract Base Class for all e-commerce scrapers.
    Forces all child classes to implement the 'scrape' method.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless

    @abstractmethod
    async def scrape(self, product_query: str) -> List[ProductDetail]:
        """
        Searches for a product and returns a list of parsed product details.
        
        Args:
            product_query (str): The search term entered by the user.
            
        Returns:
            List[ProductDetail]: A list of validated product objects.
        """
        pass

    def clean_price(self, price_str: str) -> float:
        """
        Utility method to extract a float price from a raw string.
        Example: '1,250.50 EGP' -> 1250.50
        """
        import re
        try:
            # Remove everything except digits and the decimal point
            clean_str = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
            return float(clean_str) if clean_str else 0.0
        except (ValueError, TypeError):
            return 0.0