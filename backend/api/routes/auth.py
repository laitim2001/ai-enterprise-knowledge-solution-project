"""C11 + C12 — auth endpoints (W7 D3 F1.5 + W13 D5 F5 hybrid auth cascade).

W7 baseline (protected, require valid bearer):
  `POST /auth/refresh` — issue a fresh bearer (mock no-op return same dev-token;
                         real MSAL exchanges refresh token W8 D2-D3 cascade).
  `POST /auth/logout`  — invalidate session (mock + real MSAL); W13 F5 extends
                         to also revoke the in-memory session token if present.

W13 F5 self-register (PUBLIC — no Depends auth):
  `POST /auth/register`             — create account + generate verification code
                                       + dispatch via C13 EmailProvider stub
  `POST /auth/verify-email`         — match 6-digit code, flip verified=True
  `POST /auth/login`                — verify password, issue 7-day session token
  `POST /auth/resend-verification`  — regenerate code (60s rate limit)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth import users_repo
from api.auth.cookies import SESSION_COOKIE, clear_session_cookies, set_session_cookies
from api.auth.dependency import get_current_user
from api.auth.email_provider import (
    EmailProvider,
    EmailSendError,
    get_email_provider,
)
from api.auth.models import AuthenticatedUser
from api.auth.security import (
    RESEND_COOLDOWN_SEC,
    SESSION_TOKEN_TTL_SEC,
    VERIFICATION_CODE_LENGTH,
    validate_email,
    validate_password_strength,
    verify_password,
)
from api.auth.users_repo import SELF_REGISTER_TID, UserRecord
from api.schemas.auth import (
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    RegisterResponse,
    ResendVerificationResponse,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
    UserResendVerificationRequest,
    UserVerifyEmailRequest,
    VerifyEmailResponse,
)
from api.schemas.errors import ErrorCodes
from storage.settings import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

_log = structlog.get_logger(__name__)

CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
EmailProviderDep = Annotated[EmailProvider, Depends(get_email_provider)]

_logout_bearer = HTTPBearer(auto_error=False)
LogoutBearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_logout_bearer)]

_MOCK_EXPIRES_IN_SECONDS = 3600


def _to_public(user: UserRecord) -> UserPublic:
    return UserPublic(
        oid=user.oid,
        email=user.email,
        display_name=user.display_name,
        verified=user.verified,
    )


def _api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    hint: str | None = None,
) -> HTTPException:
    """Raise route-specific error codes through the W7 ApiError envelope.

    W13 F5 extension to error_handlers.http_exception_handler decodes the
    structured `detail` dict so the response carries the precise code (e.g.
    `auth.email_already_exists`) rather than the generic 409 → resource.conflict
    fallback. Backwards compatible — string-detail HTTPException keeps W7 path.
    """
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "hint": hint},
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    user: CurrentUserDep,
    settings: SettingsDep,
    credentials: LogoutBearerDep,
) -> RefreshResponse:
    """Reissue the session credential without re-prompting for credentials.

    W17 F2 (per ADR-0022) — for a self-register session (presented via the
    `ekp_session` cookie or a legacy session bearer), rotate the token: revoke
    the old one, mint a new one, and re-set both cookies. Requires a valid
    existing session (the `Depends(get_current_user)` gate handles the 401 — no
    unauthenticated session bootstrap). Closes carry-over CO_F5_refresh.

    Mock dev mode returns the same fixed dev-token + 1h expiry (no cookie). Real
    MSAL (W8 D4 onwards) would call `acquire_token_by_refresh_token` against
    Entra ID — still 503 until that lands.
    """
    if user.tid == SELF_REGISTER_TID and not user.is_mock:
        old_token = request.cookies.get(SESSION_COOKIE)
        if (
            old_token is None
            and credentials is not None
            and credentials.scheme.lower() == "bearer"
        ):
            old_token = credentials.credentials
        if old_token is not None:
            users_repo.revoke_session(old_token)
        new_session = users_repo.create_session(user.oid)
        set_session_cookies(response, settings, new_session.token)
        return RefreshResponse(
            access_token=new_session.token,
            expires_in=SESSION_TOKEN_TTL_SEC,
            is_mock=False,
        )
    if settings.feature_auth_mock:
        return RefreshResponse(
            access_token=settings.auth_mock_bearer_token,
            expires_in=_MOCK_EXPIRES_IN_SECONDS,
            is_mock=True,
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Real MSAL refresh endpoint not yet wired (W8 D2-D3 trigger). "
            "Set Settings.feature_auth_mock=True for W7 dev mode."
        ),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    user: CurrentUserDep,
    settings: SettingsDep,
    credentials: LogoutBearerDep,
) -> LogoutResponse:
    """Invalidate the current session — revoke the self-register session token
    (whether presented via the `ekp_session` cookie or a bearer) and clear both
    auth cookies. Mock + real MSAL paths stay stateless server-side (frontend
    store clears local user state); the cookie-clear is harmless there.
    """
    cookie_token = request.cookies.get(SESSION_COOKIE)
    if cookie_token:
        users_repo.revoke_session(cookie_token)
    if credentials is not None and credentials.scheme.lower() == "bearer":
        users_repo.revoke_session(credentials.credentials)
    clear_session_cookies(response)
    return LogoutResponse(is_mock=settings.feature_auth_mock)


# --- W13 F5 self-register endpoints (public — no Depends auth) ---------------


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegisterRequest,
    email_provider: EmailProviderDep,
) -> RegisterResponse:
    """Create new self-register account + dispatch verification email.

    Validates email + password strength + display name; rejects duplicate email
    via 409 with `auth.email_already_exists`. Verification code is a 6-digit
    numeric OTP per V9 wireframe — stored on the user record + sent via the
    EmailProvider (F5 stub logs to backend; F6 swaps to ACS).
    """
    if not validate_email(payload.email):
        raise _api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCodes.VALIDATION_INVALID_EMAIL,
            message="Email format is invalid.",
        )
    pwd_error = validate_password_strength(payload.password)
    if pwd_error is not None:
        raise _api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCodes.VALIDATION_WEAK_PASSWORD,
            message=pwd_error,
        )
    if not payload.display_name.strip():
        raise _api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCodes.VALIDATION_INVALID_PAYLOAD,
            message="Display name is required.",
        )
    if users_repo.find_by_email(payload.email) is not None:
        raise _api_error(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCodes.AUTH_EMAIL_ALREADY_EXISTS,
            message="An account with that email already exists.",
            hint="Sign in instead, or use a different email.",
        )
    record = users_repo.register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    assert record.verification_code is not None  # mypy: register() always populates
    # F6.4 fail-soft — register flow stays green even if ACS is degraded; user
    # sees V9 Step 2 "Check your inbox" + Resend Button regardless. Operations
    # failure goes to structured log only so account creation isn't blocked.
    try:
        await email_provider.send_verification(
            to_email=record.email,
            code=record.verification_code,
            display_name=record.display_name,
        )
    except EmailSendError as exc:
        _log.warning(
            "verification_email_send_failed",
            stage="register",
            user_oid=record.oid,
            error=str(exc),
        )
    return RegisterResponse(user=_to_public(record))


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    payload: UserVerifyEmailRequest,
    response: Response,
    settings: SettingsDep,
) -> VerifyEmailResponse:
    """Validate the 6-digit code, flip verified=True, and auto-log-in.

    On the verified-transition a fresh session is minted and the `ekp_session`
    + `ekp_csrf` cookies are set (per ADR-0022 §1) so the V9 wireframe's Step 3
    "Start asking" lands on `/chat` already authenticated. Idempotent on an
    already-verified user (no new session — `access_token` stays None).
    """
    if len(payload.code) != VERIFICATION_CODE_LENGTH or not payload.code.isdigit():
        raise _api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodes.AUTH_VERIFICATION_FAILED,
            message="Verification code is malformed.",
            hint="Re-enter the 6-digit code from your email.",
        )
    user = users_repo.find_by_email(payload.email)
    if user is None:
        raise _api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodes.AUTH_VERIFICATION_FAILED,
            message="Verification failed.",
        )
    if user.verified:
        return VerifyEmailResponse(user=_to_public(user))
    if (
        user.verification_code is None
        or user.verification_code_expires_at is None
        or user.verification_code_expires_at < datetime.now(UTC)
    ):
        raise _api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodes.AUTH_VERIFICATION_EXPIRED,
            message="Verification code has expired.",
            hint="Request a new code via Resend.",
        )
    if user.verification_code != payload.code:
        raise _api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodes.AUTH_VERIFICATION_FAILED,
            message="Verification code is incorrect.",
        )
    updated = users_repo.mark_verified(user.oid)
    assert updated is not None  # mypy: oid resolved via find_by_email above
    session = users_repo.create_session(updated.oid)
    set_session_cookies(response, settings, session.token)
    return VerifyEmailResponse(
        user=_to_public(updated),
        access_token=session.token,
        expires_in=SESSION_TOKEN_TTL_SEC,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: UserLoginRequest,
    response: Response,
    settings: SettingsDep,
) -> LoginResponse:
    """Verify password + email-verified status and issue a 7-day session.

    Returns 401 on missing user OR password mismatch (constant-time comparison
    inside `verify_password`); 403 on unverified email. The session token is a
    256-bit URL-safe random string; W17 F2 (per ADR-0022) also sets it as the
    httpOnly `ekp_session` cookie + an `ekp_csrf` double-submit cookie. The
    token is still returned in the body for API/CLI clients (Bearer transport).
    """
    user = users_repo.find_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise _api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
            message="Email or password is incorrect.",
        )
    if not user.verified:
        raise _api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCodes.AUTH_EMAIL_NOT_VERIFIED,
            message="Email address has not been verified.",
            hint="Check your inbox for the verification email or resend it.",
        )
    session = users_repo.create_session(user.oid)
    set_session_cookies(response, settings, session.token)
    return LoginResponse(
        access_token=session.token,
        expires_in=SESSION_TOKEN_TTL_SEC,
        user=_to_public(user),
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    payload: UserResendVerificationRequest,
    email_provider: EmailProviderDep,
) -> ResendVerificationResponse:
    """Mint a fresh verification code with 60s anti-spam cooldown.

    Returns 429 if the last resend was less than RESEND_COOLDOWN_SEC ago. To
    avoid leaking which emails are registered, returns the same message body
    even when the email is unknown OR already verified — only the rate-limit
    case differentiates (security-by-obscurity is incomplete, but combined with
    F2 IP rate-limit middleware it is acceptable Tier 1 hardening).
    """
    user = users_repo.find_by_email(payload.email)
    if user is None or user.verified:
        return ResendVerificationResponse(cooldown_seconds=RESEND_COOLDOWN_SEC)
    now = datetime.now(UTC)
    if user.last_resend_at is not None:
        elapsed = (now - user.last_resend_at).total_seconds()
        if elapsed < RESEND_COOLDOWN_SEC:
            raise _api_error(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code=ErrorCodes.AUTH_RESEND_RATE_LIMITED,
                message="Resend rate limit hit — try again shortly.",
                hint=f"Wait {int(RESEND_COOLDOWN_SEC - elapsed)}s before requesting another code.",
            )
    updated = users_repo.regenerate_verification_code(user.oid)
    assert updated is not None and updated.verification_code is not None
    # F6.4 fail-soft — same rationale as register; user can press Resend again
    # if delivery actually failed. Truthful 502 here would create UX confusion
    # vs the exact same outcome (no email arrived) the user already perceives.
    try:
        await email_provider.send_verification(
            to_email=updated.email,
            code=updated.verification_code,
            display_name=updated.display_name,
        )
    except EmailSendError as exc:
        _log.warning(
            "verification_email_send_failed",
            stage="resend",
            user_oid=updated.oid,
            error=str(exc),
        )
    return ResendVerificationResponse(cooldown_seconds=RESEND_COOLDOWN_SEC)
