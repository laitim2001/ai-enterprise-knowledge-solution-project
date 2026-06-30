"""F1 — capability model + degradation rules (§3.4) for C17 Source Abstraction.

Pure-logic tests: no network, no provider. They pin the framework-side contract
that lets one import lifecycle serve connectors with different capabilities.
"""

from __future__ import annotations

from integration.connector import (
    ConnectorCapabilities,
    SourceConnector,
    resolve_behaviour,
)
from integration.models import Principal, SourceContainer, SourceDocumentRef

# A SharePoint-shaped capability set (matches integration/sharepoint F3.1).
SHAREPOINT_CAPS = ConnectorCapabilities(
    auth_kind="app_registration",
    supports_browse=True,
    supports_acl=True,
    supports_delta=False,
    acl_granularity="document",
)


def test_sharepoint_behaviour_is_manual_doc_trimming_tree() -> None:
    b = resolve_behaviour(SHAREPOINT_CAPS)
    assert b.sync_mode == "manual_only"  # supports_delta=False → no auto-sync
    assert b.acl_mode == "document_trimming"  # acl document → fill allowed_principals
    assert b.browse_mode == "tree"  # supports_browse=True → tree picker


def test_delta_capable_connector_gets_auto_sync() -> None:
    caps = ConnectorCapabilities(
        auth_kind="oauth",
        supports_browse=True,
        supports_acl=True,
        supports_delta=True,
        acl_granularity="document",
    )
    assert resolve_behaviour(caps).sync_mode == "auto"


def test_no_acl_falls_back_to_kb_layer() -> None:
    caps = ConnectorCapabilities(
        auth_kind="api_key",
        supports_browse=True,
        supports_acl=False,
        supports_delta=False,
        acl_granularity="none",
    )
    assert resolve_behaviour(caps).acl_mode == "kb_fallback"


def test_acl_supported_but_kb_granularity_falls_back() -> None:
    # supports_acl=True but only KB-level granularity → still KB fallback, not
    # document trimming (document_trimming requires document granularity).
    caps = ConnectorCapabilities(
        auth_kind="oauth",
        supports_browse=True,
        supports_acl=True,
        supports_delta=False,
        acl_granularity="kb",
    )
    assert resolve_behaviour(caps).acl_mode == "kb_fallback"


def test_no_browse_requires_manual_container_id() -> None:
    caps = ConnectorCapabilities(
        auth_kind="api_key",
        supports_browse=False,
        supports_acl=False,
        supports_delta=False,
        acl_granularity="none",
    )
    assert resolve_behaviour(caps).browse_mode == "manual_id"


def test_models_construct_with_change_detection_fields() -> None:
    # SourceDocumentRef carries change-detection (③); optional fields default None.
    ref = SourceDocumentRef(id="i", name="n.docx", path="/n.docx", container_id="c")
    assert ref.etag is None and ref.size is None
    ref2 = SourceDocumentRef(
        id="i", name="n", path="/n", container_id="c", etag="e1", size=1024
    )
    assert ref2.etag == "e1" and ref2.size == 1024

    c = SourceContainer(id="s", name="Site", type="site")
    assert c.parent_id is None
    p = Principal(kind="group", id="guid-1", display_name="Engineering")
    assert p.kind == "group" and p.id == "guid-1"


def test_source_connector_is_runtime_checkable_protocol() -> None:
    # A minimal duck-typed object exposing `capabilities` is structurally a
    # SourceConnector for isinstance (runtime_checkable only checks attribute
    # presence, which is enough to gate "is this a connector?" at the framework).
    class _Stub:
        capabilities = SHAREPOINT_CAPS

        async def connect(self): ...  # noqa: ANN201
        def browse(self, handle, container_id=None): ...  # noqa: ANN001, ANN201
        def list_documents(self, handle, container_id): ...  # noqa: ANN001, ANN201
        async def fetch_document(self, handle, ref): ...  # noqa: ANN001, ANN201
        async def get_principals(self, handle, ref): ...  # noqa: ANN001, ANN201
        async def delta(self, handle, container_id, token): ...  # noqa: ANN001, ANN201

    assert isinstance(_Stub(), SourceConnector)
