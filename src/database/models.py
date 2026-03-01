from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Float, Boolean, JSON, DateTime
from datetime import datetime

Base = declarative_base()

class ProductModel(Base):
    """
    SQLAlchemy Model representing the 'products' table in the database.
    Matches the fields from the Pydantic ProductDetail schema.
    """
    __tablename__ = "products"

    # We use the URL as the Primary Key because it's unique per product
    url: Mapped[str] = mapped_column(String, primary_key=True)
    
    source_website: Mapped[str] = mapped_column(String, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="EGP")
    
    # SQLAlchemy's JSON type handles Python dictionaries automatically
    specifications: Mapped[dict] = mapped_column(JSON, default=dict)
    
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)