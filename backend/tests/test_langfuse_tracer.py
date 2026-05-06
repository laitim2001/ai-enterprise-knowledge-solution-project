"""W8 D5 F5.1 — Langfuse SDK init + flush + accessor coverage.

Per W08-beta-deploy-sprint2 plan §2 F5.1 acceptance:
  - Real Langfuse SDK wired when public_key + secret_key populated
  - Singleton stays None when keys missing (local dev / CI no-op)
  - Import failure / init failure surface structured warnings, NEVER raise
  - flush_tracer drains queued events; safe to call when client is None

Tests mock the `langfuse.Langfuse` constructor at the module boundary so the
real SDK is never imported in CI.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

from observability import langfuse_tracer
from storage.settings import Settings


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    """Each test starts with the singleton cleared."""
    langfuse_tracer._set_langfuse_client_for_tests(None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)


def _settings_with_keys() -> Settings:
    return Settings(
        langfuse_host="https://langfuse.example",
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
    )


def _settings_without_keys() -> Settings:
    return Settings(
        langfuse_host="https://langfuse.example",
        langfuse_public_key="",
        langfuse_secret_key="",
    )


def test_init_without_keys_leaves_client_none() -> None:
    """Local dev / CI path — no keys → no SDK init."""
    langfuse_tracer.init_tracer(_settings_without_keys())
    assert langfuse_tracer.get_langfuse_client() is None


def test_init_with_keys_wires_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both keys present → Langfuse client constructed with host + creds."""
    constructed: dict[str, Any] = {}

    class _FakeLangfuse:
        def __init__(self, **kwargs: Any) -> None:
            constructed.update(kwargs)
            self.flush = MagicMock()

    fake_module = ModuleType("langfuse")
    fake_module.Langfuse = _FakeLangfuse  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)

    langfuse_tracer.init_tracer(_settings_with_keys())

    client = langfuse_tracer.get_langfuse_client()
    assert client is not None
    assert isinstance(client, _FakeLangfuse)
    assert constructed == {
        "host": "https://langfuse.example",
        "public_key": "pk-test",
        "secret_key": "sk-test",
    }


def test_init_handles_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing langfuse package → singleton stays None, no exception."""
    # Plant a sentinel module that lacks the `Langfuse` attribute. The
    # `from langfuse import Langfuse` line then raises ImportError naturally,
    # exercising the same except branch as a totally absent package.
    fake_module = ModuleType("langfuse")
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)

    langfuse_tracer.init_tracer(_settings_with_keys())
    assert langfuse_tracer.get_langfuse_client() is None


def test_init_handles_constructor_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """SDK init raises → singleton stays None, structured error logged."""

    class _FailingLangfuse:
        def __init__(self, **_kwargs: Any) -> None:
            raise RuntimeError("connection refused")

    fake_module = ModuleType("langfuse")
    fake_module.Langfuse = _FailingLangfuse  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)

    langfuse_tracer.init_tracer(_settings_with_keys())
    assert langfuse_tracer.get_langfuse_client() is None


def test_flush_with_no_client_is_noop() -> None:
    """flush_tracer when singleton None — no exception, no work."""
    langfuse_tracer._set_langfuse_client_for_tests(None)
    langfuse_tracer.flush_tracer()  # should not raise


def test_flush_invokes_client_flush() -> None:
    """flush_tracer calls client.flush() when present."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    langfuse_tracer.flush_tracer()

    fake_client.flush.assert_called_once_with()


def test_flush_swallows_client_exception() -> None:
    """flush errors must never block process shutdown."""
    fake_client = MagicMock()
    fake_client.flush.side_effect = RuntimeError("network down")
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    langfuse_tracer.flush_tracer()  # must NOT raise

    fake_client.flush.assert_called_once_with()


def test_flush_when_client_lacks_flush_method() -> None:
    """Client without flush attribute — silently skip."""
    fake_client = object()  # bare object — no .flush
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    langfuse_tracer.flush_tracer()  # must NOT raise
