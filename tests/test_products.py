from sqlalchemy import select

from app.api.dependencies import get_db
from app.models.user import User


def create_registered_user_and_token(client):
    email = "product-admin@example.com"
    password = "Test-Password-123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Product Tester",
            "password": password,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    db_override = client.app.dependency_overrides[get_db]
    db_generator = db_override()
    db = next(db_generator)

    try:
        user = db.scalar(
            select(User).where(User.email == email)
        )
        assert user is not None

        user.role = "admin"
        db.commit()
    finally:
        db_generator.close()

    return token


def test_list_products_is_public(client):
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.json() == []


def test_regular_user_cannot_create_product(client):
    email = "regular@example.com"
    password = "Test-Password-123!"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Regular User",
            "password": password,
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Keyboard",
            "description": "Test product",
            "price": "49.99",
            "stock": 10,
        },
    )

    assert response.status_code == 403


def test_admin_can_create_and_list_product(client):
    token = create_registered_user_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Mechanical Keyboard",
            "description": "Test product",
            "price": "79.99",
            "stock": 25,
        },
    )

    assert create_response.status_code == 201
    product = create_response.json()
    assert product["name"] == "Mechanical Keyboard"
    assert product["price"] == "79.99"
    assert product["stock"] == 25

    list_response = client.get("/api/v1/products")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == product["id"]


def test_negative_price_is_rejected(client):
    token = create_registered_user_and_token(client)

    response = client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Invalid Product",
            "price": "-5.00",
            "stock": 1,
        },
    )

    assert response.status_code == 422
