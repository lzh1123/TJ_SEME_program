from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    AppSettings,
    AuthContext,
    DbSession,
    RedisClient,
    get_auth_context,
    get_optional_auth_context,
    require_internal_service,
)
from app.core.security import transport_hash_password
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ClientLoginRequest,
    ClientRegisterRequest,
    ClientResetPasswordRequest,
    AuthorizeRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenBundle,
    VerifyCodeCheckRequest,
    VerifyCodeSendRequest,
)
from app.schemas.common import AuthorizeDecision, IntrospectResponse, UserSubject
from app.services.auth_service import AuthService
from app.services.code_service import VerifyCodeService
from app.services.rbac_service import AuthorizationService

router = APIRouter()


def get_auth_service(db: DbSession, redis_client: RedisClient, settings: AppSettings) -> AuthService:
    return AuthService(db=db, redis_client=redis_client, settings=settings)


def get_code_service(db: DbSession) -> VerifyCodeService:
    return VerifyCodeService(db)


def get_authorization_service(db: DbSession) -> AuthorizationService:
    return AuthorizationService(db)


@router.post("/verify-code/send")
def send_verify_code(
    payload: VerifyCodeSendRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.code_service.send_code(email=payload.email, purpose=payload.purpose)
    return {"message": "verification code sent"}


@router.post("/verify-code/check")
def check_verify_code(
    payload: VerifyCodeCheckRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.code_service.verify_code(
        email=payload.email, purpose=payload.purpose, code=payload.code, consume=False
    )
    return {"message": "verification code valid"}


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    return service.register(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        verification_code=payload.verification_code,
    )


@router.post("/client-register", response_model=AuthResponse)
def client_register(
    payload: ClientRegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return service.register(
        email=payload.email,
        username=payload.username,
        password=transport_hash_password(payload.password),
        verification_code=payload.verification_code,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    return service.login(account=payload.account, password=payload.password)


@router.post("/client-login", response_model=AuthResponse)
def client_login(
    payload: ClientLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return service.login(
        account=payload.account,
        password=transport_hash_password(payload.password),
    )


@router.post("/refresh", response_model=TokenBundle)
def refresh(
    payload: RefreshRequest,
    auth: AuthContext | None = Depends(get_optional_auth_context),
    service: AuthService = Depends(get_auth_service),
) -> TokenBundle:
    if payload.refresh_token:
        return service.refresh(refresh_token=payload.refresh_token)
    if auth and auth.session_id:
        return service.refresh_session(user=auth.user, session_id=auth.session_id)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token or session required")


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.logout(
        user=auth.user,
        refresh_token=payload.refresh_token,
        all_sessions=payload.all_sessions,
        current_session_id=auth.session_id,
    )
    return {"message": "logged out"}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.send_password_reset_code(email=payload.email)
    return {"message": "reset code sent"}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.reset_password(
        email=payload.email,
        verification_code=payload.verification_code,
        new_password=payload.new_password,
    )
    return {"message": "password reset"}


@router.post("/client-reset-password")
def client_reset_password(
    payload: ClientResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.reset_password(
        email=payload.email,
        verification_code=payload.verification_code,
        new_password=transport_hash_password(payload.new_password),
    )
    return {"message": "password reset"}


@router.get("/me", response_model=UserSubject)
def me(auth: AuthContext = Depends(get_auth_context), authorization: AuthorizationService = Depends(get_authorization_service)) -> UserSubject:
    return UserSubject.model_validate(authorization.build_subject(auth.user))


@router.post("/introspect", response_model=IntrospectResponse)
def introspect(
    payload: dict[str, Any],
    db: DbSession,
    _: None = Depends(require_internal_service),
) -> IntrospectResponse:
    token = payload.get("token")
    if not token:
        return IntrospectResponse(active=False)

    try:
        from app.core.security import decode_token

        data = decode_token(token)
    except Exception:  # noqa: BLE001
        return IntrospectResponse(active=False)

    if data.get("type") != "access":
        return IntrospectResponse(active=False)

    user = db.get(User, int(data["sub"]))
    if not user or user.status != "active":
        return IntrospectResponse(active=False)

    authorization = AuthorizationService(db)
    return IntrospectResponse(
        active=True,
        subject=UserSubject.model_validate(authorization.build_subject(user)),
        token_type=data.get("type"),
        expires_at=data.get("exp"),
    )


@router.post("/authorize", response_model=AuthorizeDecision)
def authorize(
    payload: AuthorizeRequest,
    auth: AuthContext | None = Depends(get_optional_auth_context),
    _: None = Depends(require_internal_service),
    authorization: AuthorizationService = Depends(get_authorization_service),
) -> AuthorizeDecision:
    if payload.subject:
        subject = payload.subject.model_dump()
    elif auth:
        subject = authorization.build_subject(auth.user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="subject is required when no user authentication is provided",
        )
    allowed, reason, matched = authorization.authorize(
        subject=subject,
        action=payload.action,
        resource=payload.resource.model_dump(),
        context=payload.context.model_dump(),
    )
    return AuthorizeDecision(allowed=allowed, reason=reason, matched_permissions=matched)


@router.get("/permissions")
def permissions(
    auth: AuthContext = Depends(get_auth_context),
    authorization: AuthorizationService = Depends(get_authorization_service),
) -> dict[str, list[str]]:
    return {
        "roles": authorization.get_roles(auth.user.id),
        "permissions": authorization.get_permissions(auth.user.id),
    }


@router.get("/roles")
def roles(
    auth: AuthContext = Depends(get_auth_context),
    authorization: AuthorizationService = Depends(get_authorization_service),
) -> dict[str, list[str]]:
    return {"roles": authorization.get_roles(auth.user.id)}
