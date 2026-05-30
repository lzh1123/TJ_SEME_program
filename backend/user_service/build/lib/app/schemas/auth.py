from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ABACContext, ABACResource, UserSubject


class VerifyCodeSendRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern="^(register|forgot_password|reset_password)$")


class VerifyCodeCheckRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern="^(register|forgot_password|reset_password)$")
    code: str = Field(min_length=4, max_length=12)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=32, max_length=256)
    verification_code: str = Field(min_length=4, max_length=12)


class LoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=32, max_length=256)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=32, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_sessions: bool = False


class TokenBundle(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    session_id: str | None = None


class AuthResponse(BaseModel):
    user: UserSubject
    auth: TokenBundle


class ClientRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    verification_code: str = Field(min_length=4, max_length=12)


class ClientLoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class ClientResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=8, max_length=128)


class AuthorizeRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject: UserSubject | None = None
    action: str = Field(min_length=1, max_length=128)
    resource: ABACResource
    context: ABACContext = Field(default_factory=ABACContext)
