"""
Authentication Endpoints
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import verify_password
from app.schemas.token import TokenResponse, RefreshTokenRequest
from app.schemas.user import LoginRequest, UserResponse
from app.services.token_service import TokenService
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint
    - **username**: User login username or email
    - **password**: User password
    """
    user_repo = UserRepository(db)
    
    # Try to find user by username or email
    user = user_repo.get_by_username(request.username)
    if not user:
        user = user_repo.get_by_email(request.username)
    
    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    token_repo = TokenRepository(db)
    token_service = TokenService(token_repo)
    tokens = token_service.create_tokens(user.id)
    
    return TokenResponse(**tokens)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    token_repo = TokenRepository(db)
    token_service = TokenService(token_repo)

    stored_token = token_repo.get_by_token(request.refresh_token)
    if (
        not stored_token
        or stored_token.is_revoked
        or stored_token.expires_at <= datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    payload = token_service.verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("user_id")
    if str(stored_token.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token does not match the current user"
        )

    parsed_user_id = UUID(str(user_id))
    token_service.revoke_token(stored_token.user_id, request.refresh_token)
    tokens = token_service.create_tokens(parsed_user_id)
    return TokenResponse(**tokens)

@router.post("/logout")
async def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Logout and revoke refresh token
    """
    token_repo = TokenRepository(db)
    token_service = TokenService(token_repo)

    payload = token_service.verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload"
        )

    success = token_service.revoke_token(
        user_id=UUID(str(user_id)),
        token=request.refresh_token,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout"
        )
    
    return {"message": "Successfully logged out"}
