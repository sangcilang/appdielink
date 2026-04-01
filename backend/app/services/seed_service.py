"""
Database Seeding Service
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repo import UserRepository


def seed_admin_user(db: Session) -> None:
    """
    Create default admin user if it doesn't exist.

    Default credentials:
    - Username: admin
    - Email: admin@link1die.com
    - Password: admin123456
    """
    user_repo = UserRepository(db)

    admin_user = user_repo.get_by_username("admin")
    if admin_user:
        if not admin_user.hashed_password.startswith("$pbkdf2-sha256$"):
            user_repo.update(
                admin_user.id,
                hashed_password=hash_password("admin123456"),
                is_active=True,
                is_admin=True,
            )
            print("Admin user password refreshed for the current environment")
            return

        print("Admin user already exists")
        return

    admin = user_repo.create(
        username="admin",
        email="admin@link1die.com",
        hashed_password=hash_password("admin123456"),
        is_admin=True,
    )

    print("Admin user created successfully")
    print("  Username: admin")
    print("  Email: admin@link1die.com")
    print("  Password: admin123456")
    print(f"  ID: {admin.id}")
