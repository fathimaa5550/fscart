from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CartService:
    """Business logic for cart operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_or_create_cart(self, user_id: str) -> Cart:
        """Return the cart for a user, creating it if it does not exist."""
        result = await self.db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        cart = result.scalar_one_or_none()
        if cart is None:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()
            await self.db.refresh(cart)
        return cart

    async def get_cart(self, user_id: str) -> Cart:
        """Return the cart for a user (creates empty cart on first access)."""
        return await self._get_or_create_cart(user_id)

    async def add_item(self, user_id: str, data: CartItemCreate) -> Cart:
        """
        Add a product to the cart.
        If the item already exists its quantity is incremented.
        Raises 404 if the product does not exist.
        Raises 400 if insufficient stock.
        """
        # Validate product exists and has stock
        product_result = await self.db.execute(
            select(Product).where(Product.id == data.product_id)
        )
        product = product_result.scalar_one_or_none()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {data.product_id} not found",
            )

        cart = await self._get_or_create_cart(user_id)

        # Check whether the item already exists in the cart
        existing_result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == data.product_id,
            )
        )
        existing_item = existing_result.scalar_one_or_none()

        new_quantity = data.quantity
        if existing_item is not None:
            new_quantity += existing_item.quantity

        if product.stock < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock. Available: {product.stock},"
                    f" requested total: {new_quantity}"
                ),
            )

        if existing_item is not None:
            existing_item.quantity = new_quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                quantity=data.quantity,
            )
            self.db.add(new_item)

        await self.db.flush()

        # Reload cart with fresh data
        return await self._reload_cart(cart.id)

    async def update_item(
        self, user_id: str, item_id: int, data: CartItemUpdate
    ) -> Cart:
        """
        Update the quantity of a specific cart item.
        Raises 404 if the cart or item is not found.
        Raises 400 if insufficient stock.
        """
        cart = await self._get_or_create_cart(user_id)

        item_result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id,
            )
        )
        item = item_result.scalar_one_or_none()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item {item_id} not found",
            )

        # Validate stock
        product_result = await self.db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one_or_none()
        if product is not None and product.stock < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock. Available: {product.stock},"
                    f" requested: {data.quantity}"
                ),
            )

        item.quantity = data.quantity
        await self.db.flush()

        return await self._reload_cart(cart.id)

    async def remove_item(self, user_id: str, item_id: int) -> Cart:
        """
        Remove a specific item from the cart.
        Raises 404 if the cart or item is not found.
        """
        cart = await self._get_or_create_cart(user_id)

        result = await self.db.execute(
            delete(CartItem).where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id,
            )
        )
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item {item_id} not found",
            )

        await self.db.flush()
        return await self._reload_cart(cart.id)

    async def clear_cart(self, user_id: str) -> Cart:
        """Remove all items from the user's cart."""
        cart = await self._get_or_create_cart(user_id)

        await self.db.execute(
            delete(CartItem).where(CartItem.cart_id == cart.id)
        )
        await self.db.flush()

        return await self._reload_cart(cart.id)

    # ──────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────

    async def _reload_cart(self, cart_id: int) -> Cart:
        """
        Re-fetch the cart with all items and products loaded.

        expire_all() is called first so SQLAlchemy discards any stale
        identity-map entries and issues fresh SELECT statements, correctly
        reflecting newly inserted / deleted CartItem rows within the same
        request session.
        """
        self.db.expire_all()
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        return result.scalar_one()
