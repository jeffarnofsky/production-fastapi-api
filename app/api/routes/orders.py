from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import (
    create_order,
    get_all_orders,
    get_user_order,
    get_user_orders,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_endpoint(
    order_data: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return create_order(db, current_user.id, order_data)


@router.get("", response_model=list[OrderResponse])
def list_my_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return get_user_orders(db, current_user.id)


@router.get("/{order_id}", response_model=OrderResponse)
def read_my_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    order = get_user_order(db, current_user.id, order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.get("/admin/all", response_model=list[OrderResponse])
def list_all_orders(
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    return get_all_orders(db)
