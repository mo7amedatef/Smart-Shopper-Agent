from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Optional
from datetime import datetime

class ProductDetail(BaseModel):
    source_website: str = Field(
        ..., 
        description="The name of the e-commerce website (e.g., Amazon, Noon, B.TECH)."
    )
    product_name: str = Field(
        ..., 
        description="The full title of the product as listed on the website."
    )
    price: float = Field(
        ..., 
        description="The final price of the product as a float value."
    )
    currency: str = Field(
        default="EGP", 
        description="The currency of the price (default is EGP)."
    )
    url: HttpUrl = Field(
        ..., 
        description="The direct product URL."
    )
    specifications: Dict[str, str] = Field(
        default_factory=dict, 
        description="Technical specifications of the product (e.g., RAM, Storage, Color)."
    )
    is_available: bool = Field(
        default=True, 
        description="Availability status of the product (True if in stock)."
    )
    scraped_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), 
        description="ISO 8601 timestamp indicating when the data was scraped."
    )