"""
User Repository - Data Access Layer
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, username: str, email: str, hashed_password: str, is_admin: bool = False) -> User:
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user"""
        user = self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
    
    def user_exists(self, username: str = None, email: str = None) -> bool:
        """Check if user exists by username or email"""
        query = self.db.query(User)
        if username:
            return query.filter(User.username == username).first() is not None
        if email:
            return query.filter(User.email == email).first() is not None
        return False
