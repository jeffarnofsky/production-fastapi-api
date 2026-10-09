# Production-Style FastAPI Backend

A RESTful backend API built with **FastAPI, SQLAlchemy, PostgreSQL, and JWT authentication**. This project demonstrates backend development practices including database migrations, role-based access control, automated testing, and CI with GitHub Actions.


![CI](https://github.com/jeffarnofsky/production-fastapi-api/actions/workflows/ci.yml/badge.svg)

## Features

* **Authentication:** User registration and login with JWT access tokens.
* **Password Security:** Password hashing using Argon2.
* **Role-Based Access Control:** Separate permissions for regular users and administrators.
* **Product Management:** Public product listing and detail endpoints, with admin-only management operations.
* **Order Management:** Create orders, track order items, and preserve product prices at the time of purchase.
* **Inventory Management:** Validate stock availability and decrease stock when orders are created.
* **Database Migrations:** Schema versioning with Alembic.
* **Automated Tests:** API tests using pytest and an isolated SQLite test database.
* **Continuous Integration:** GitHub Actions runs the test suite automatically.
* **Containerized Database:** PostgreSQL can be started using Docker Compose.

## Tech Stack

* Python 3.12
* FastAPI
* SQLAlchemy 2
* PostgreSQL
* Alembic
* JWT authentication
* Argon2 password hashing
* pytest
* Docker Compose
* GitHub Actions

## API Documentation

When the application is running, interactive API documentation is available at:

* Swagger UI: `/docs`
* ReDoc: `/redoc`

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/jeffarnofsky/production-fastapi-api.git
cd production-fastapi-api
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root and configure the variables required by the application, including:

```env
DATABASE_URL=your_database_connection_url
SECRET_KEY=replace_with_a_secure_secret
```

Use your local PostgreSQL connection details for `DATABASE_URL`. Generate a strong, private value for `SECRET_KEY`.

**Never commit `.env` files, production credentials, or real secret keys to Git.**

### 5. Start PostgreSQL

If you use the included Docker Compose configuration:

```bash
docker compose up -d db
```

Make sure the database settings in your `.env` file match your local PostgreSQL configuration.

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Run the API

```bash
uvicorn app.main:app --reload
```

The development server should be available at `http://127.0.0.1:8000`.

Open `http://127.0.0.1:8000/docs` to explore the API.

## Running Tests

Run the automated test suite with:

```bash
python -m pytest -q
```

The test suite covers authentication, product operations, order creation, inventory validation, and access control.

The project also uses GitHub Actions to run tests on pushes and pull requests.

## Main API Areas

| Area           | Capabilities                                       |
| -------------- | -------------------------------------------------- |
| Health         | Health check endpoint                              |
| Authentication | Registration, login, current-user access           |
| Products       | Public listing and detail; admin management        |
| Orders         | Order creation, order history, admin order listing |

The API uses versioned routes under `/api/v1`.

## Engineering Practices

* Separation of API routes, schemas, services, and database models.
* Password hashing and token-based authentication.
* Authorization checks for protected operations.
* Database migrations managed with Alembic.
* Transaction-aware order creation and stock validation.
* Automated tests and continuous integration.

## Project Status

This project is an ongoing backend portfolio project. Its goal is to demonstrate practical API development, database design, authentication, testing, and maintainable code organization.

## License

No license has been specified yet. Add a license before explicitly granting others permission to reuse or redistribute this project.
