from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate



def create_order(
    db: Session,
    user_id: int,
    order_data: OrderCreate,
) -> Order:
    # Combine repeated product IDs into one quantity.
    quantities: dict[int, int] = {}

    for item in order_data.items:
        quantities[item.product_id] = (
            quantities.get(item.product_id, 0) + item.quantity
        )

    try:
        order_items: list[OrderItem] = []

        # Lock products in a consistent order to reduce deadlock risk.
        for product_id in sorted(quantities):
            quantity = quantities[product_id]

            product = db.scalar(
                select(Product)
                .where(Product.id == product_id)
                .with_for_update()
            )

            if product is None or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {product_id} not found",
                )

            if product.stock < quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for product {product_id}",
                )

            product.stock -= quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

        order = Order(
            user_id=user_id,
            status="pending",
            items=order_items,
        )

        db.add(order)
        db.flush()

        # Keep the ID before committing.
        order_id = order.id
        db.commit()

        # Explicitly load the order and its items.
        saved_order = db.scalar(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )

        if saved_order is None:
            raise RuntimeError("Created order could not be reloaded")

        return saved_order

    except Exception:
        db.rollback()
        raise


def get_user_orders(
    db: Session,
    user_id: int,
) -> list[Order]:
    statement = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(db.scalars(statement).all())


def get_user_order(
    db: Session,
    user_id: int,
    order_id: int,
) -> Order | None:
    statement = select(Order).where(
        Order.id == order_id,
        Order.user_id == user_id,
    )
    return db.scalar(statement)


def get_all_orders(db: Session) -> list[Order]:
    statement = select(Order).order_by(
        Order.created_at.desc(),
        Order.id.desc(),
    )
    return list(db.scalars(statement).all())