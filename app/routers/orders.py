from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order from cart",
    description=(
        "Converts the user's current cart into an order. "
        "Stock is deducted atomically and the cart is cleared on success."
    ),
)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    service = OrderService(db)
    order = await service.create_from_cart(data)
    return OrderResponse.model_validate(order)


@router.get(
    "/user/{user_id}",
    response_model=list[OrderResponse],
    summary="List orders for a user",
)
async def list_user_orders(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[OrderResponse]:
    service = OrderService(db)
    orders = await service.get_orders_by_user(user_id)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order by ID",
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    service = OrderService(db)
    order = await service.get_order(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return OrderResponse.model_validate(order)


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description=(
        "Transitions an order to a new status. "
        "Valid transitions: pending→confirmed/cancelled, "
        "confirmed→shipped/cancelled, shipped→delivered."
    ),
)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    service = OrderService(db)
    order = await service.update_status(order_id, data)
    return OrderResponse.model_validate(order)
