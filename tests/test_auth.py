def register_user(client, email="test@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "Test-Password-123!",
        },
    )


def login_user(client, email="test@example.com"):
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "Test-Password-123!",
        },
    )


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_duplicate_email_returns_409(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 409


def test_login_returns_access_token(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_wrong_password_returns_401(client):
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "Wrong-Password!",
        },
    )

    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_me_with_valid_token_returns_current_user(client):
    register_user(client)
    login_response = login_user(client)

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_regular_user_cannot_list_users(client):
    register_user(client)
    login_response = login_user(client)

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_can_list_users(client):
    from app.api.dependencies import get_db
    from app.core.security import create_access_token
    from app.models.user import User

    register_user(client)

    # Promote the registered user inside the test database.
    db_override = client.app.dependency_overrides[get_db]

    with next(db_override()) as db:
        user = db.query(User).filter_by(
            email="test@example.com"
        ).first()

        assert user is not None

        user.role = "admin"
        user_id = user.id
        db.commit()

    # Create a token after the session has been closed.
    admin_token = create_access_token(subject=str(user_id))

    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)