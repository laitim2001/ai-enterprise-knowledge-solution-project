"""W7 D2 F1.3 + F1.6 partial — auth wired routes integration tests.

Verifies the FastAPI Depends switching point on protected routers. Uses a
fresh FastAPI sub-app rather than the global `api.server.app` so module-level
dependency_overrides in test_api_skeleton.py do not leak in.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.auth.models import AuthenticatedUser
from storage.settings import Settings, get_settings


def _build_app(settings: Settings) -> FastAPI:
    """Build a minimal app exposing one protected + one public route."""
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings

    @app.get("/public")
    def public_route() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protected")
    def protected_route(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, str]:  # noqa: B008
        return {"oid": user.oid, "tid": user.tid, "is_mock": str(user.is_mock)}

    return app


def test_public_route_no_auth_required() -> None:
    app = _build_app(Settings(feature_auth_mock=True))
    client = TestClient(app)
    response = client.get("/public")
    assert response.status_code == 200


def test_protected_route_rejects_no_bearer_when_mock_enabled() -> None:
    app = _build_app(Settings(feature_auth_mock=True))
    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_protected_route_accepts_dev_token_when_mock_enabled() -> None:
    settings = Settings(feature_auth_mock=True)
    app = _build_app(settings)
    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {settings.auth_mock_bearer_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["oid"] == settings.auth_mock_oid
    assert body["tid"] == settings.auth_mock_tid
    assert body["is_mock"] == "True"


def test_protected_route_rejects_wrong_token_when_mock_enabled() -> None:
    app = _build_app(Settings(feature_auth_mock=True))
    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer not-the-token"},
    )
    assert response.status_code == 401


def test_protected_route_503_when_mock_disabled_msal_skeleton_not_wired() -> None:
    """W7 D1 msal_provider fail-closed contract: dev never silently bypasses."""
    app = _build_app(Settings(feature_auth_mock=False))
    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 503
