"""kb_naming helper unit tests (ADR-0018 W16+ Phase 3 P0.1; per CLAUDE.md §5.6 H6).

Tier 1 multi-KB invariant per ADR-0018 closure of audit-W15-d5-vs-spec.md §CC-1:
- kb_id_to_index_name: legacy alias for drive_user_manuals + ADR-0005 convention for future KBs
- kb_id_to_screenshot_container: parallel pattern for blob container
- kb_id_filter_clause: OData scoping (mandatory per ADR-0018)
"""

from __future__ import annotations

from storage.kb_naming import (
    kb_id_filter_clause,
    kb_id_to_index_name,
    kb_id_to_screenshot_container,
)

# kb_id_to_index_name


def test_kb_id_to_index_name_legacy_alias_drive_user_manuals() -> None:
    """kb_id='drive_user_manuals' returns legacy default (Tier 1 deployed alias)."""
    assert kb_id_to_index_name("drive_user_manuals") == "ekp-kb-drive-v1"


def test_kb_id_to_index_name_legacy_alias_uses_caller_default() -> None:
    """Caller can override legacy default (e.g. test fixture, alternate deploy)."""
    assert (
        kb_id_to_index_name("drive_user_manuals", legacy_default_index="custom-idx-v2")
        == "custom-idx-v2"
    )


def test_kb_id_to_index_name_new_kb_follows_adr_0005_convention() -> None:
    """Non-legacy kb_id maps to ekp-kb-{kb_id}-v1 per ADR-0005."""
    assert kb_id_to_index_name("finance_dept") == "ekp-kb-finance_dept-v1"
    assert kb_id_to_index_name("hr_handbook") == "ekp-kb-hr_handbook-v1"
    assert kb_id_to_index_name("rapo_internal") == "ekp-kb-rapo_internal-v1"


# kb_id_to_screenshot_container


def test_kb_id_to_screenshot_container_legacy_alias() -> None:
    """kb_id='drive_user_manuals' returns legacy default container."""
    assert kb_id_to_screenshot_container("drive_user_manuals") == "ekp-kb-drive-screenshots"


def test_kb_id_to_screenshot_container_new_kb_follows_convention() -> None:
    """Non-legacy kb_id maps to ekp-kb-{kb_id}-screenshots per ADR-0005."""
    assert kb_id_to_screenshot_container("finance_dept") == "ekp-kb-finance_dept-screenshots"


# kb_id_filter_clause


def test_kb_id_filter_clause_format() -> None:
    """OData filter clause format per ADR-0018 multi-KB invariant."""
    assert kb_id_filter_clause("drive_user_manuals") == "kb_id eq 'drive_user_manuals'"
    assert kb_id_filter_clause("finance_dept") == "kb_id eq 'finance_dept'"


def test_kb_id_filter_clause_includes_quoted_value() -> None:
    """OData string literal requires single quotes around kb_id value."""
    clause = kb_id_filter_clause("test_kb")
    assert "'test_kb'" in clause
    assert clause.startswith("kb_id eq")
