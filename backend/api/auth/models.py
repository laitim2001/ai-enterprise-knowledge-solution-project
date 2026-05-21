"""C11 — authenticated user payload shared by mock + real MSAL paths.

Field names mirror the canonical Entra ID ID-token claims so F2 rate-key + F3
audit-tag don't need to know whether the upstream provider was mock or LIVE.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthenticatedUser(BaseModel):
    """Subset of Entra ID JWT claims the EKP API needs downstream.

    Real MSAL path populates from validated JWT; mock path populates from
    `Settings.auth_mock_*`. Either way, downstream code reads the same shape.
    """

    oid: str = Field(..., description="Stable principal id (Entra ID object id) — F2 rate-key + F3 audit user_id")
    tid: str = Field(..., description="Tenant id — F3 audit tenant_id")
    preferred_username: str = Field(..., description="UPN/email — F3 audit human-readable trail only")
    role: str = Field(
        default="user",
        description=(
            "RBAC role key (W24c F3 per ADR-0027) — admin/editor/user/power. "
            "Resolved server-side: self-register from users.role, mock from "
            "Settings.auth_mock_role, real MSAL from the Entra app-role claim. "
            "Defaults to 'user' (least privilege)."
        ),
    )
    is_mock: bool = Field(default=False, description="True iff issued via mock_msal dev mode (W7); never True in W8+ LIVE")
