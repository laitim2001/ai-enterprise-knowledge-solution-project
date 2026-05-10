"""C11 — auth endpoint request/response schemas (W7 D3 F1.5 + W13 D5 F5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RefreshResponse(BaseModel):
    """Response payload for `POST /auth/refresh`.

    Mock mode reissues the same dev-token; real MSAL exchanges the refresh
    token via the Entra ID `/oauth2/v2.0/token` endpoint W8 D2-D3.
    """

    access_token: str = Field(..., description="Bearer token to put in Authorization header")
    token_type: str = Field(default="Bearer")
    expires_in: int = Field(..., description="Seconds until access_token expires")
    is_mock: bool = Field(default=False)


class LogoutResponse(BaseModel):
    status: str = Field(default="ok")
    is_mock: bool = Field(default=False)


# --- W13 F5 self-register hybrid auth (per ADR-0014) -------------------------
#
# Three new public endpoints:
#   POST /auth/register     → RegisterResponse(verified=False) + email sent
#   POST /auth/verify-email → VerifyEmailResponse(verified=True)
#   POST /auth/login        → LoginResponse(access_token + UserPublic)
# Plus resend helper:
#   POST /auth/resend-verification → ResendVerificationResponse


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="Login email — must be unique within the EKP self-register table")
    password: str = Field(..., description="Plaintext password — hashed via scrypt before storage (ADR-0016)")
    display_name: str = Field(..., description="Greeting name shown on /chat + admin views")


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserVerifyEmailRequest(BaseModel):
    email: str
    code: str = Field(..., description="6-digit numeric verification code from email (V9 wireframe Step 2)")


class UserResendVerificationRequest(BaseModel):
    email: str


class UserPublic(BaseModel):
    """Sanitised user model returned to clients — never contains password_hash
    or verification_code so accidental log/serialisation can't leak secrets."""

    oid: str
    email: str
    display_name: str
    verified: bool
    is_mock: bool = Field(default=False)


class RegisterResponse(BaseModel):
    user: UserPublic
    message: str = Field(default="Verification email sent — check your inbox.")


class VerifyEmailResponse(BaseModel):
    """Issued by `POST /auth/verify-email`. On the verified-transition the user
    is auto-logged-in (per ADR-0022 §1 "the email-verify step ... set ekp_session"):
    `access_token` + `expires_in` are populated and an `ekp_session` cookie is
    set on the response. On the idempotent already-verified branch both are None
    (no new session minted)."""

    user: UserPublic
    message: str = Field(default="Email verified. You can sign in now.")
    access_token: str | None = Field(
        default=None, description="Session token (also set as the ekp_session cookie); None if already verified"
    )
    expires_in: int | None = Field(
        default=None, description="Seconds until access_token expires (7 days); None if already verified"
    )


class LoginResponse(BaseModel):
    """Issued by `POST /auth/login` for self-register users (per ADR-0014).

    `access_token` is a server-side session token (not a JWT) — stored in the
    in-memory sessions repo per Tier 1 scope (W11 retro CO18 → Beta hardening).
    """

    access_token: str
    token_type: str = Field(default="Bearer")
    expires_in: int = Field(..., description="Seconds until access_token expires (7 days)")
    user: UserPublic


class ResendVerificationResponse(BaseModel):
    message: str = Field(default="Verification email resent.")
    cooldown_seconds: int = Field(..., description="Seconds the client should disable Resend before next attempt")
