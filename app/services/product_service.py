from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Business logic for product operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Product], int]:
        """Return a paginated list of products and the total count."""
        count_result = await self.db.execute(select(func.count(Product.id)))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Product).order_by(Product.id).offset(skip).limit(limit)
        )
        products = list(result.scalars().all())
        return products, total

    async def get_by_id(self, product_id: int) -> Product | None:
        """Return a single product by primary key, or None."""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ProductCreate) -> Product:
        """Persist a new product and return it."""
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(
        self, product_id: int, data: ProductUpdate
    ) -> Product | None:
        """Apply partial updates to an existing product and return it."""
        product = await self.get_by_id(product_id)
        if product is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: int) -> bool:
        """Delete a product by id. Returns True if deleted, False if not found."""
        result = await self.db.execute(
            delete(Product).where(Product.id == product_id)
        )
        return result.rowcount > 0

    async def adjust_stock(
        self, product_id: int, delta: int, *, allow_negative: bool = False
    ) -> Product | None:
        """
        Atomically adjust stock by `delta` (can be negative for deductions).
        Returns the updated product or None if not found / insufficient stock.
        """
        product = await self.get_by_id(product_id)
        if product is None:
            return None

        new_stock = product.stock + delta
        if not allow_negative and new_stock < 0:
            return None

        await self.db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(stock=new_stock)
        )
        await self.db.flush()
        await self.db.refresh(product)
        return product
