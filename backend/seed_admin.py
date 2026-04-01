"""
Seed database with admin user.
Run: python seed_admin.py
"""
import sys

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


def seed_admin() -> None:
    """Create admin user if it does not exist."""
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()

        if admin:
            if not admin.hashed_password.startswith("$pbkdf2-sha256$"):
                admin.hashed_password = hash_password("admin123456")
                admin.is_active = True
                admin.is_admin = True
                db.commit()
                db.refresh(admin)
                print("Admin user password refreshed for the current environment")
                return

            print("Admin user already exists")
            print("  Username: admin")
            print("  Email: admin@link1die.com")
            print("  Password: admin123456")
            return

        admin_user = User(
            username="admin",
            email="admin@link1die.com",
            hashed_password=hash_password("admin123456"),
            is_active=True,
            is_admin=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("Admin user created successfully")
        print("\nLogin Credentials:")
        print("  Username: admin")
        print("  Email: admin@link1die.com")
        print("  Password: admin123456")
        print(f"  ID: {admin_user.id}")
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
