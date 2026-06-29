from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, model_validator

from ..services.auth_service import AuthService
from ..services.ai.model_config import LLM_PROVIDERS
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

    username: Optional[str] = Field(None, min_length=1)
    account: Optional[str] = Field(None, min_length=1)
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def require_username_or_account(self):
        if not self.username and not self.account:
            raise ValueError("username or account is required")
        return self


class RefreshRequest(BaseModel):
    model_config = {"extra": "forbid", "populate_by_name": True}

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
    last_login_at: Optional[str] = Field(None, alias="lastLoginAt")


class UpdateProfileRequest(BaseModel):
    model_config = {"extra": "forbid"}

    display_name: Optional[str] = Field(None, max_length=100, alias="displayName")


class LLMConfigRequest(BaseModel):
    model_config = {"extra": "forbid"}

    provider: str = Field(..., max_length=50)
    model: str = Field(..., max_length=100)
    api_base: str = Field(..., max_length=500, alias="apiBase")
    api_key: Optional[str] = Field(None, max_length=1000, alias="apiKey")


class LLMConfigResponse(BaseModel):
    model_config = {"extra": "forbid"}

    provider: Optional[str] = None
    model: Optional[str] = None
    api_base: Optional[str] = Field(None, alias="apiBase")
    has_api_key: bool = Field(False, alias="hasApiKey")
    providers: list[dict]


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
        username=payload.username or payload.account or "",
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
        lastLoginAt=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.put("/me")
async def update_me(
    payload: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Update the current user's profile."""
    user = await auth.update_profile(
        user_id=current_user_id,
        display_name=payload.display_name,
    )


@router.get("/llm-config")
async def get_llm_config(
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> LLMConfigResponse:
    user = await auth.get_user_by_id(current_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    providers = [
        {
            "provider": spec.provider,
            "label": spec.label,
            "model": spec.model,
            "apiBase": spec.api_base,
        }
        for spec in LLM_PROVIDERS.values()
    ]
    return LLMConfigResponse(
        provider=user.llm_provider,
        model=user.llm_model,
        apiBase=user.llm_api_base,
        hasApiKey=bool(user.llm_api_key),
        providers=providers,
    )


@router.put("/llm-config")
async def update_llm_config(
    payload: LLMConfigRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> LLMConfigResponse:
    if payload.provider not in LLM_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported LLM provider")
    user = await auth.update_llm_config(
        user_id=current_user_id,
        provider=payload.provider,
        model=payload.model,
        api_base=payload.api_base,
        api_key=payload.api_key,
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    providers = [
        {
            "provider": spec.provider,
            "label": spec.label,
            "model": spec.model,
            "apiBase": spec.api_base,
        }
        for spec in LLM_PROVIDERS.values()
    ]
    return LLMConfigResponse(
        provider=user.llm_provider,
        model=user.llm_model,
        apiBase=user.llm_api_base,
        hasApiKey=bool(user.llm_api_key),
        providers=providers,
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        displayName=user.display_name,
        lastLoginAt=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Revoke all refresh tokens for the current user."""
    await auth.logout(current_user_id)
    return {"message": "Logged out successfully"}
