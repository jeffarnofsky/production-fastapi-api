import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.promote_admin EMAIL")
        raise SystemExit(1)

    email = sys.argv[1].strip().lower()

    if not email:
        print("Email cannot be empty.")
        raise SystemExit(1)

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is None:
            print("User not found. Register this user first.")
            raise SystemExit(1)

        if user.role == "admin":
            print("User is already an admin.")
            return

        user.role = "admin"
        db.commit()

        print(f"Admin role granted to {user.email}.")


if __name__ == "__main__":
    main()
