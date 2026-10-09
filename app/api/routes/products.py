from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.product import (
    create_product,
    deactivate_product,
    get_product_by_id,
    get_products,
    update_product,
)
from app.models.user import User

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductResponse])
def list_products(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    return get_products(db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(
    product_data: ProductCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    return create_product(db, product_data)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product_endpoint(
    product_id: int,
    product_data: ProductUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return update_product(db, product, product_data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_endpoint(
    product_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    deactivate_product(db, product)