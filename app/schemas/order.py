from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderItemResponse(BaseModel):
    """Schema for returning a single order item."""
    id: int
    order_id: int
    product_id: int | None
    product_name: str
    unit_price: Decimal
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Schema for creating an order from a user's cart."""
    user_id: str = Field(..., min_length=1, max_length=255, examples=["user-42"])


class OrderStatusUpdate(BaseModel):
    """Schema for updating an order's status."""
    status: OrderStatus = Field(..., examples=[OrderStatus.confirmed])


class OrderResponse(BaseModel):
    """Schema for returning a complete order."""
    id: int
    user_id: str
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
