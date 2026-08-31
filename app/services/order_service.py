from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate


class OrderService:
    """Business logic for order operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_from_cart(self, data: OrderCreate) -> Order:
        """
        Convert the user's cart into an order.

        Steps:
          1. Load cart with items.
          2. Validate stock for every item.
          3. Deduct stock from products.
          4. Create Order + OrderItems.
          5. Clear the cart.
        """
        # Load cart
        cart_result = await self.db.execute(
            select(Cart)
            .where(Cart.user_id == data.user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        cart = cart_result.scalar_one_or_none()

        if cart is None or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty or does not exist",
            )

        total_amount = Decimal("0.00")
        order_items: list[OrderItem] = []

        for cart_item in cart.items:
            product: Product | None = cart_item.product
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {cart_item.product_id} no longer exists",
                )
            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for '{product.name}'."
                        f" Available: {product.stock},"
                        f" requested: {cart_item.quantity}"
                    ),
                )

            line_total = product.price * cart_item.quantity
            total_amount += line_total

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=cart_item.quantity,
                )
            )

            # Deduct stock
            await self.db.execute(
                update(Product)
                .where(Product.id == product.id)
                .values(stock=product.stock - cart_item.quantity)
            )

        # Create order
        order = Order(user_id=data.user_id, total_amount=total_amount)
        self.db.add(order)
        await self.db.flush()

        for item in order_items:
            item.order_id = order.id
            self.db.add(item)

        # Clear the cart
        await self.db.execute(
            delete(CartItem).where(CartItem.cart_id == cart.id)
        )

        await self.db.flush()
        return await self._reload_order(order.id)

    async def get_order(self, order_id: int) -> Order | None:
        """Return a single order by id, or None."""
        return await self._reload_order(order_id)

    async def get_orders_by_user(self, user_id: str) -> list[Order]:
        """Return all orders for a given user, newest first."""
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
        )
        return list(result.scalars().all())

    async def update_status(
        self, order_id: int, data: OrderStatusUpdate
    ) -> Order:
        """
        Update order status with basic state-machine validation.
        Raises 404 if the order is not found.
        Raises 400 for invalid transitions.
        """
        order = await self._reload_order(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        self._validate_transition(order.status, data.status)

        await self.db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=data.status)
        )
        await self.db.flush()
        return await self._reload_order(order_id)

    # ──────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────

    async def _reload_order(self, order_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _validate_transition(
        current: OrderStatus, new: OrderStatus
    ) -> None:
        """Enforce valid status transitions."""
        valid_transitions: dict[OrderStatus, set[OrderStatus]] = {
            OrderStatus.pending: {
                OrderStatus.confirmed,
                OrderStatus.cancelled,
            },
            OrderStatus.confirmed: {
                OrderStatus.shipped,
                OrderStatus.cancelled,
            },
            OrderStatus.shipped: {
                OrderStatus.delivered,
            },
            OrderStatus.delivered: set(),
            OrderStatus.cancelled: set(),
        }

        if new == current:
            return  # no-op is fine

        allowed = valid_transitions.get(current, set())
        if new not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot transition order from '{current.value}'"
                    f" to '{new.value}'."
                    f" Allowed transitions: {[s.value for s in allowed]}"
                ),
            )
