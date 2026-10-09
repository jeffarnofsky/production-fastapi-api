from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(Product.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_product_by_id(
    db: Session,
    product_id: int,
) -> Product | None:
    statement = select(Product).where(
        Product.id == product_id,
        Product.is_active.is_(True),
    )
    return db.scalar(statement)


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:
    product = Product(**product_data.model_dump())

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:
    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


def deactivate_product(
    db: Session,
    product: Product,
) -> None:
    product.is_active = False
    db.commit()