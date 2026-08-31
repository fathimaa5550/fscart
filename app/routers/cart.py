from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get(
    "/{user_id}",
    response_model=CartResponse,
    summary="Get cart for a user",
    description="Returns the user's cart, creating an empty one on first access.",
)
async def get_cart(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db)
    cart = await service.get_cart(user_id)
    return CartResponse.model_validate(cart)


@router.post(
    "/{user_id}/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to the cart",
    description=(
        "Adds a product to the user's cart. "
        "If the product is already in the cart its quantity is incremented."
    ),
)
async def add_item(
    user_id: str,
    data: CartItemCreate,
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db)
    cart = await service.add_item(user_id, data)
    return CartResponse.model_validate(cart)


@router.put(
    "/{user_id}/items/{item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
)
async def update_item(
    user_id: str,
    item_id: int,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db)
    cart = await service.update_item(user_id, item_id, data)
    return CartResponse.model_validate(cart)


@router.delete(
    "/{user_id}/items/{item_id}",
    response_model=CartResponse,
    summary="Remove an item from the cart",
)
async def remove_item(
    user_id: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db)
    cart = await service.remove_item(user_id, item_id)
    return CartResponse.model_validate(cart)


@router.delete(
    "/{user_id}",
    response_model=CartResponse,
    summary="Clear the cart",
    description="Removes all items from the user's cart.",
)
async def clear_cart(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db)
    cart = await service.clear_cart(user_id)
    return CartResponse.model_validate(cart)
