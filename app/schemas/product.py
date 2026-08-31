from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Wireless Mouse"])
    description: str | None = Field(
        default=None, examples=["A comfortable wireless mouse"]
    )
    price: Decimal = Field(..., gt=0, decimal_places=2, examples=[29.99])
    stock: int = Field(default=0, ge=0, examples=[100])

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("price must be greater than zero")
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for partially updating a product (all fields optional)."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("price must be greater than zero")
        return v


class ProductResponse(ProductBase):
    """Schema for returning a product from the API."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
