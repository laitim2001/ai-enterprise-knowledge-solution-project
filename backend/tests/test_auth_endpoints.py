"""W7 D3 F1.5 — /auth/refresh + /auth/logout endpoint tests."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.auth import router as auth_router
from storage.settings import Settings, get_settings


def _build_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.include_router(auth_router)
    return app


def test_refresh_returns_dev_token_when_mock_enabled() -> None:
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {settings.auth_mock_bearer_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == settings.auth_mock_bearer_token
    assert body["token_type"] == "Bearer"
    assert body["is_mock"] is True
    assert body["expires_in"] > 0


def test_refresh_rejects_unauth() -> None:
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.post("/auth/refresh")
    assert response.status_code == 401


def test_refresh_503_when_mock_disabled_skeleton_not_wired() -> None:
    settings = Settings(feature_auth_mock=False)
    client = TestClient(_build_app(settings))

    # When mock disabled, Depends(get_current_user) routes to msal_provider
    # which fail-closed 503 — never reaches the route body.
    response = client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 503


def test_me_returns_user_with_role_when_authenticated() -> None:
    settings = Settings(feature_auth_mock=True, auth_mock_role="editor")
    client = TestClient(_build_app(settings))

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {settings.auth_mock_bearer_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["oid"] == settings.auth_mock_oid
    assert body["role"] == "editor"
    assert body["is_mock"] is True


def test_me_rejects_unauthenticated() -> None:
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_defaults_role_to_admin_in_mock_mode() -> None:
    # mock auth_mock_role defaults to 'admin' (W24c F3.3) — dev walks every gate.
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {settings.auth_mock_bearer_token}"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_logout_returns_ok_when_authenticated() -> None:
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {settings.auth_mock_bearer_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["is_mock"] is True


def test_logout_rejects_unauth() -> None:
    settings = Settings(feature_auth_mock=True)
    client = TestClient(_build_app(settings))

    response = client.post("/auth/logout")
    assert response.status_code == 401
