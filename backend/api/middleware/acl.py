"""C16/C08 — RBAC authorization guards (W24c F3 + F8 per ADR-0027 Option A).

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

`require_role` (F3) gates by workspace role. `require_kb_acl` (F8) gates by
per-KB access: it consults the `kb_acl` store via `app.state.rbac_backend`.
Workspace admins pass `require_kb_acl` unconditionally (ADR-0027); other users
need a direct `kb_acl` grant at the required role or higher — group-inherited
access resolves once F6 member sync lands.

Per-endpoint application is opt-in (W24c plan §4 R-W24c-3): routers attach
`require_role(...)` / `require_kb_acl(...)` as each endpoint lands, rather than
a blanket gate.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

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


# Per-KB role rank — manage outranks edit outranks query.
_KB_ACL_RANK: dict[str, int] = {"query": 1, "edit": 2, "manage": 3}


def require_kb_acl(min_role: str) -> Callable[..., Awaitable[AuthenticatedUser]]:
    """Build a dependency requiring `min_role`+ access on the path's `kb_id`.

    Workspace admins always pass (full access per ADR-0027). Every other user
    needs a direct `kb_acl` grant on that KB at `min_role` or higher. Group-
    inherited access resolves once F6 group-member sync lands — until then only
    direct user grants count (W24c F8).

    Reads `app.state.rbac_backend`, so a KB-ACL-guarded route needs a wired
    RBAC backend (503 otherwise).
    """

    async def _guard(
        kb_id: str,
        request: Request,
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if current_user.role == "admin":
            return current_user
        backend = getattr(request.app.state, "rbac_backend", None)
        if backend is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="rbac_backend not initialized — check lifespan logs",
            )
        access = await backend.get_kb_access(kb_id, current_user.oid)
        if access is None or _KB_ACL_RANK[access] < _KB_ACL_RANK[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{min_role}' access to this KB.",
            )
        return current_user

    return _guard
