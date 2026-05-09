"""KB id naming convention helpers per ADR-0005 + ADR-0018 multi-KB invariant.

Multi-KB invariant per ADR-0018 (W15 D5 audit Major Drift #4 / CC-1 closure):
- Search index name: f"ekp-kb-{kb_id}-v1" (ADR-0005 convention)
- Blob screenshot container: f"ekp-kb-{kb_id}-screenshots" (ADR-0005 convention)
- OData filter clause: f"kb_id eq '{kb_id}'" (multi-KB scoping; required on every search)

Tier 1 legacy alias: kb_id="drive_user_manuals" maps to deployed legacy names
("ekp-kb-drive-v1" + "ekp-kb-drive-screenshots") that predate strict ADR-0005
convention. Future KBs follow the convention exactly. Spec amendment cleaning up
the legacy alias deferred to Tier 2 per ADR-0018 Consequences Neutral.
"""

from __future__ import annotations

_LEGACY_KB_ID = "drive_user_manuals"


def kb_id_to_index_name(kb_id: str, legacy_default_index: str = "ekp-kb-drive-v1") -> str:
    """Map kb_id → Azure AI Search index name per ADR-0005 + Tier 1 legacy alias.

    Tier 1 legacy: kb_id="drive_user_manuals" → legacy_default_index
    (deployed name "ekp-kb-drive-v1" per Q3 Resolved 2026-05-02).
    Future KBs: ekp-kb-{kb_id}-v1 per ADR-0005 convention.
    """
    if kb_id == _LEGACY_KB_ID:
        return legacy_default_index
    return f"ekp-kb-{kb_id}-v1"


def kb_id_to_screenshot_container(
    kb_id: str,
    legacy_default_container: str = "ekp-kb-drive-screenshots",
) -> str:
    """Map kb_id → Azure Blob screenshot container name per ADR-0005 + Tier 1 legacy alias.

    Tier 1 legacy: kb_id="drive_user_manuals" → legacy_default_container.
    Future KBs: ekp-kb-{kb_id}-screenshots per ADR-0005 convention.
    """
    if kb_id == _LEGACY_KB_ID:
        return legacy_default_container
    return f"ekp-kb-{kb_id}-screenshots"


def kb_id_filter_clause(kb_id: str) -> str:
    """OData filter clause to scope Azure AI Search query to a single KB.

    Per ADR-0018 multi-KB invariant: this clause prepends to any caller-supplied
    filter via " and " conjunction, making kb_id scoping mandatory on every search.
    """
    return f"kb_id eq '{kb_id}'"
