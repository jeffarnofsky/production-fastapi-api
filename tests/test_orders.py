from sqlalchemy import select

from app.api.dependencies import get_db
from app.models.user import User


PASSWORD = "Test-Password-123!"


def register_user(client, email: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Order Test User",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201, response.text


def login_user(client, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def register_and_login(client, email: str) -> str:
    register_user(client, email)
    return login_user(client, email)


def promote_user_to_admin(client, email: str) -> None:
    db_override = client.app.dependency_overrides[get_db]

    with next(db_override()) as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )
        assert user is not None, f"User {email} was not found"

        user.role = "admin"
        db.commit()


def create_admin_and_login(client, email: str) -> str:
    register_user(client, email)
    promote_user_to_admin(client, email)
    return login_user(client, email)


def create_product(
    client,
    admin_token: str,
    *,
    name: str = "Test Product",
    price: str = "19.99",
    stock: int = 10,
) -> int:
    response = client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": name,
            "description": "Product used in order tests",
            "price": price,
            "stock": stock,
        },
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_order(client, token: str, product_id: int, quantity: int = 1):
    return client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            ]
        },
    )


def promote_to_admin(client, email: str) -> str:
    token = register_and_login(client, email)

    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None

        user.role = "admin"
        db.commit()
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

    return token

def test_create_order_saves_price_and_reduces_stock(client):
    admin_token = create_admin_and_login(
        client, "admin-order-test@example.com"
    )
    product_id = create_product(
        client, admin_token, price="19.99", stock=10
    )

    user_token = register_and_login(
        client, "customer-order-test@example.com"
    )

    response = create_order(client, user_token, product_id, 2)

    assert response.status_code == 201, response.text
    order = response.json()

    assert order["status"] == "pending"
    assert order["items"][0]["product_id"] == product_id
    assert order["items"][0]["quantity"] == 2
    assert order["items"][0]["unit_price"] == "19.99"

    product_response = client.get("/api/v1/products")
    assert product_response.status_code == 200

    product = next(
        item for item in product_response.json()
        if item["id"] == product_id
    )
    assert product["stock"] == 8


def test_order_rejects_insufficient_stock(client):
    admin_token = create_admin_and_login(
        client, "admin-stock-test@example.com"
    )
    product_id = create_product(
        client, admin_token, stock=2
    )
    user_token = register_and_login(
        client, "customer-stock-test@example.com"
    )

    response = create_order(client, user_token, product_id, 3)

    assert response.status_code == 409


def test_create_order_requires_authentication(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"product_id": 1, "quantity": 1}
            ]
        },
    )

    assert response.status_code in (401, 403)


def test_user_cannot_read_another_users_order(client):
    admin_token = create_admin_and_login(
        client, "admin-ownership-test@example.com"
    )
    product_id = create_product(client, admin_token)

    owner_token = register_and_login(
        client, "owner-order-test@example.com"
    )
    other_token = register_and_login(
        client, "other-order-test@example.com"
    )

    create_response = create_order(
        client, owner_token, product_id
    )
    assert create_response.status_code == 201, create_response.text

    order_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_admin_can_list_all_orders(client):
    admin_token = create_admin_and_login(
        client, "admin-list-orders@example.com"
    )
    product_id = create_product(client, admin_token)

    user_token = register_and_login(
        client, "customer-list-orders@example.com"
    )

    create_response = create_order(
        client, user_token, product_id
    )
    assert create_response.status_code == 201, create_response.text

    response = client.get(
        "/api/v1/orders/admin/all",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    assert len(response.json()) >= 1


def test_regular_user_cannot_list_all_orders(client):
    user_token = register_and_login(
        client, "regular-user-orders@example.com"
    )

    response = client.get(
        "/api/v1/orders/admin/all",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403



def test_order_rolls_back_stock_if_any_product_is_missing(client):
    admin_token = promote_to_admin(
        client,
        "rollback-admin@example.com",
    )
    product_id = create_product(
        client,
        admin_token,
        stock=10,
    )
    user_token = register_and_login(
        client,
        "rollback-user@example.com",
    )

    response = client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "items": [
                {"product_id": product_id, "quantity": 2},
                {"product_id": product_id + 100000, "quantity": 1},
            ],
        },
    )

    assert response.status_code == 404, response.text

    products_response = client.get("/api/v1/products")
    assert products_response.status_code == 200

    product = next(
        item for item in products_response.json()
        if item["id"] == product_id
    )
    assert product["stock"] == 10