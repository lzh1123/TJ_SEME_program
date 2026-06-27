from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from ..services.auth_service import AuthService
from .deps import get_auth_service, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response models ──────────────────────────────


class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    model_config = {"extra": "forbid"}

    refresh_token: str = Field(..., alias="refreshToken")


class TokenResponse(BaseModel):
    model_config = {"extra": "forbid"}

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(alias="tokenType")


class UserResponse(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    username: str
    email: str
    display_name: Optional[str] = Field(None, alias="displayName")


# ── Endpoints ──────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account."""
    try:
        user = await auth.register(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        displayName=user.display_name,
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Authenticate user and return tokens."""
    user = await auth.authenticate(
        username=payload.username,
        password=payload.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )

    tokens = await auth.create_tokens(
        user,
        device_info=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    return {
        **tokens,
        "user": UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            displayName=user.display_name,
        ).model_dump(by_alias=True),
    }


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Exchange a refresh token for a new token pair."""
    tokens = await auth.refresh_access_token(payload.refresh_token)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return tokens


@router.get("/me")
async def get_me(
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Return the currently authenticated user's profile."""
    user = await auth.get_user_by_id(current_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        displayName=user.display_name,
    )


@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Revoke all refresh tokens for the current user."""
    await auth.logout(current_user_id)
    return {"message": "Logged out successfully"}
