from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CartItemBase(BaseModel):
    product_id: int = Field(..., gt=0, examples=[1])
    quantity: int = Field(default=1, gt=0, examples=[2])


class CartItemCreate(CartItemBase):
    """Schema for adding an item to a cart."""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item quantity."""
    quantity: int = Field(..., gt=0, examples=[3])


class CartItemResponse(BaseModel):
    """Schema for returning a single cart item."""
    id: int
    cart_id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime
    product: ProductResponse | None = None

    @property
    def subtotal(self) -> Decimal | None:
        if self.product:
            return self.product.price * self.quantity
        return None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Schema for returning a complete cart with all items."""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse] = []

    @property
    def total(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items:
            if item.product:
                total += item.product.price * item.quantity
        return total

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    model_config = ConfigDict(from_attributes=True)
