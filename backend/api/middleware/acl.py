"""C16/C08 — RBAC role-guard FastAPI dependency (W24c F3 per ADR-0027 Option A).

`require_role(*allowed)` builds a FastAPI dependency that 403s when the
authenticated user's role is not in `allowed`. It chains on `get_current_user`,
so it inherits that dependency's 401 (missing / invalid credentials) + CSRF
behaviour — a route guarded by `require_role` needs no separate
`Depends(get_current_user)`.

Usage — per-endpoint:

    @router.post("/users/invite")
    async def invite(
        actor: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ) -> InviteResult:
        ...

or router-level:

    APIRouter(prefix="/users", dependencies=[Depends(require_role("admin"))])

F3 ships `require_role`. The per-KB ACL guard (`require_kb_acl`) lands with F8,
alongside the `kb_acl` storage methods it must consult — wiring a guard whose
backing store has no read method yet would be a stub (Karpathy §1.2).

Per-endpoint application is opt-in (W24c plan §4 R-W24c-3): F4-F10 attach
`require_role(...)` as each `/users/*` + admin endpoint lands. F3 itself
delivers the mechanism + the 403 contract, not a blanket gate.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser


def require_role(*allowed: str) -> Callable[..., AuthenticatedUser]:
    """Build a dependency admitting only users whose role is in `allowed`.

    Returns the `AuthenticatedUser` on success so the guarded endpoint can
    consume the identity through the same `Depends` — no second auth
    dependency. Raises 403 (not 401) when the caller is authenticated but
    under-privileged, so the frontend can tell "log in" from "you can't".
    """

    def _guard(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the roles: {', '.join(allowed)}.",
            )
        return current_user

    return _guard
