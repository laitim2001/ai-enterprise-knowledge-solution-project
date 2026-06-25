"""W96 F2 — completeness judge parse-helper unit tests (per §5.6 H6).

Tests the pure, I/O-free parse helpers of ``backend/eval/completeness_judge.py``
(no live judge needed):
- _parse_nuggets: plain JSON / ```json fence / dedup / empty-list vs malformed (None)
- _parse_presence: text-aligned / positional fallback / dropped-nugget = not present /
  reordered judge reply / malformed (None)
- make_completeness_judge: None when no credential (skip path)
"""

from __future__ import annotations

from eval.completeness_judge import (
    _parse_nuggets,
    _parse_presence,
    make_completeness_judge,
)
from storage.settings import Settings


def test_parse_nuggets_plain() -> None:
    out = _parse_nuggets('{"nuggets": ["post the journal", "confirm voucher"]}')
    assert out == ["post the journal", "confirm voucher"]


def test_parse_nuggets_json_fence_and_dedup() -> None:
    raw = '```json\n{"nuggets": ["a", "a", " b ", ""]}\n```'
    assert _parse_nuggets(raw) == ["a", "b"]


def test_parse_nuggets_empty_list_is_not_none() -> None:
    # explicit "nothing relevant" → [] (distinct from a parse failure)
    assert _parse_nuggets('{"nuggets": []}') == []


def test_parse_nuggets_malformed_is_none() -> None:
    assert _parse_nuggets(None) is None
    assert _parse_nuggets("not json") is None
    assert _parse_nuggets('{"wrong_key": []}') is None
    assert _parse_nuggets("[1, 2, 3]") is None  # not a dict


def test_parse_presence_text_aligned() -> None:
    nuggets = ["step a", "variant b", "overview c"]
    content = (
        '{"judgements": ['
        '{"nugget": "step a", "present": true},'
        '{"nugget": "variant b", "present": false},'
        '{"nugget": "overview c", "present": false}]}'
    )
    assert _parse_presence(content, nuggets) == [True, False, False]


def test_parse_presence_reordered_reply_realigns_by_text() -> None:
    nuggets = ["step a", "variant b"]
    # judge echoes in REVERSE order — text alignment must fix it back to nugget order
    content = (
        '{"judgements": ['
        '{"nugget": "variant b", "present": true},'
        '{"nugget": "step a", "present": false}]}'
    )
    assert _parse_presence(content, nuggets) == [False, True]


def test_parse_presence_dropped_nugget_counts_as_absent() -> None:
    nuggets = ["step a", "variant b", "overview c"]
    # judge omits "overview c" → it must default to NOT present (never silently covered)
    content = (
        '{"judgements": ['
        '{"nugget": "step a", "present": true},'
        '{"nugget": "variant b", "present": true}]}'
    )
    assert _parse_presence(content, nuggets) == [True, True, False]


def test_parse_presence_positional_fallback_when_no_text_echo() -> None:
    nuggets = ["step a", "variant b"]
    # no echoed nugget text matches → fall back to positional (length matches)
    content = '{"judgements": [{"present": true}, {"present": false}]}'
    assert _parse_presence(content, nuggets) == [True, False]


def test_parse_presence_malformed_is_none() -> None:
    assert _parse_presence(None, ["a"]) is None
    assert _parse_presence("not json", ["a"]) is None
    assert _parse_presence('{"wrong": []}', ["a"]) is None


def test_make_judge_none_without_credential() -> None:
    settings = Settings(azure_openai_api_key="")
    assert make_completeness_judge(settings) is None
