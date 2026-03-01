from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from loguru import logger
from datetime import datetime

from src.database.models import Base, ProductModel
from src.schemas.product import ProductDetail

class DatabaseManager:
    """
    Handles asynchronous database connections and CRUD operations using SQLAlchemy.
    """
    def __init__(self, db_url: str = "sqlite+aiosqlite:///ecommerce_data.db"):
        # We use aiosqlite for asynchronous SQLite operations
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, 
            expire_on_commit=False, 
            class_=AsyncSession
        )

    async def init_db(self):
        """Creates tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[DatabaseManager] Database initialized successfully.")

    async def upsert_product(self, product_data: ProductDetail):
        """
        Inserts a new product or updates an existing one based on the URL.
        """
        async with self.SessionLocal() as session:
            # 1. Check if the product already exists by URL
            stmt = select(ProductModel).where(ProductModel.url == str(product_data.url))
            result = await session.execute(stmt)
            existing_product = result.scalars().first()

            # Parse the ISO format string back to a Python datetime object
            parsed_date = datetime.fromisoformat(product_data.scraped_at)

            if existing_product:
                # 2. Update existing product
                existing_product.price = product_data.price
                existing_product.is_available = product_data.is_available
                existing_product.specifications = product_data.specifications
                existing_product.scraped_at = parsed_date
                logger.debug(f"[DatabaseManager] UPDATED existing product: {product_data.product_name[:30]}...")
            else:
                # 3. Insert new product
                new_product = ProductModel(
                    url=str(product_data.url),
                    source_website=product_data.source_website,
                    product_name=product_data.product_name,
                    price=product_data.price,
                    currency=product_data.currency,
                    specifications=product_data.specifications,
                    is_available=product_data.is_available,
                    scraped_at=parsed_date
                )
                session.add(new_product)
                logger.debug(f"[DatabaseManager] INSERTED new product: {product_data.product_name[:30]}...")

            # 4. Commit the transaction (Safely at the end!)
            await session.commit()