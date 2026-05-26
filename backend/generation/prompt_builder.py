"""Citation-required prompt builder per architecture.md §3.2.

System prompt enforces:
- Answer only from retrieved chunks (no hallucination)
- Cite every fact via `[chunk-{chunk_id}]` markers right after the sentence
- Refuse with explicit message if chunks insufficient (R4 hallucination guard)
- Match user's language

Refusal phrase is fixed (`REFUSAL_PHRASE`) so post-processor can detect refusal.
"""

from __future__ import annotations

from dataclasses import dataclass

from retrieval.retrieval_engine import RetrievedChunk

REFUSAL_PHRASE = "I cannot find this in the available documentation"

SYSTEM_PROMPT = f"""You are Ricoh's internal Knowledge Assistant. Answer the user's question using ONLY the retrieved knowledge chunks below.

Rules:
1. Cite every fact with [chunk-{{chunk_id}}] markers immediately after the sentence that uses the chunk. Use the literal chunk_id from the chunk's header line; never invent or shorten one.
2. If the retrieved chunks do not contain enough information, reply with exactly the phrase: "{REFUSAL_PHRASE}" — do NOT hallucinate.
3. Lead with a direct one-sentence answer to the user's question; then provide supporting details only as needed (target <= 150 words total). Use ordered lists / steps when answering procedural questions.
4. Match the user's language (English / 繁體中文 / 日本語) — do not translate the chunks.
5. Never fabricate chunk_ids; only cite chunks shown below.
6. For overview / aggregate queries (e.g. "show me all X", "list all Y", "describe the integration scenarios"), synthesize what IS available from the chunks even if coverage is partial; explicitly note any gaps via "Based on available documentation:" framing rather than refusing entirely. Only emit the refusal phrase (Rule 2) when chunks are COMPLETELY off-topic — not when partial coverage exists. (CH-005 — R14 mitigation 2026-05-24)
7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure. (W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)
8. When multiple retrieved chunks each contain partial information relevant to the answer, cite ALL of them (not just the most representative one) — each fact in the answer should be backed by every chunk that supports it. If two chunks describe the same scenario from different angles, both warrant a citation marker. (W33 F1.1.b — Rule 8 restored from W31 commit 16b9b3d per sequential ship layered on W32 (h') backend)"""


@dataclass(slots=True, frozen=True)
class PromptMessages:
    """OpenAI chat.completions messages — system + user only (no history yet)."""

    messages: list[dict]


def _format_chunk(chunk: RetrievedChunk, *, dispatch_mode: str = "replace") -> str:
    """Format a chunk for LLM context.

    Dispatch chain (ADR-0037 W26 F2 extends ADR-0020; W27 F1 adds enum branching
    per Settings.parent_doc_dispatch_mode "replace" | "append"):

    replace branch (W26 F2 baseline, default — top-priority-wins `or` chain):
    1. `parent_section_text` — siblings aggregated by Parent-Document Retriever
       (`backend/generation/parent_doc_retriever.py`); supersedes `expanded_text`
       for the anchor chunk when `enable_parent_doc_retrieval=True`.
    2. `expanded_text` — prev/next ±1 chunk window per ADR-0020 Context Expander.
    3. `chunk_text` — raw chunk text (W2 baseline) when neither expansion applied.

    append branch (W27 F1 amendment candidate, behind Settings flag — render
    BOTH anchor text + parent section context as 2 segments to preserve citation
    invariant against RAGAs faithfulness judge mismatch per W26 D1.35 hypothesis):
       當 `parent_section_text` 存在 → render 2-segment format —
         `Text: <chunk_text>` 主段(anchor raw)+ delimiter + `Parent section context:` 段。
       若 `parent_section_text` 不存在 → 退回 replace chain (`expanded_text > chunk_text`)。

    Citation invariant preserved on both branches: cited chunk_id references
    original anchor (per architecture.md §3.5 Citation contract). Append mode
    重複 anchor 一次(主段 + parent section 內)— acceptable token cost for
    judge-mismatch elimination hypothesis test.
    """
    cid = str(chunk.fields.get("chunk_id", ""))
    title = str(chunk.fields.get("chunk_title", "") or "(untitled)")
    section = " > ".join(chunk.fields.get("section_path") or [])
    section_line = f"  Section: {section}\n" if section else ""

    parent_section_text = str(chunk.fields.get("parent_section_text") or "")
    expanded_text = str(chunk.fields.get("expanded_text") or "")
    chunk_text = str(chunk.fields.get("chunk_text", "") or "")

    if dispatch_mode == "append" and parent_section_text:
        # W27 F1 append branch — 2-segment render preserves citation invariant.
        # Main text = chunk_text (anchor raw) per Karpathy §1.2 simplicity —
        # expanded_text's prev/next functionally redundant with parent section
        # per ADR-0037 §6.1.
        text_block = f"  Text: {chunk_text}\n\n  Parent section context:\n  {parent_section_text}"
    else:
        # replace branch — W26 F2 baseline top-priority-wins
        text = parent_section_text or expanded_text or chunk_text
        text_block = f"  Text: {text}"

    return f"[chunk-{cid}] {title}\n{section_line}{text_block}"


def build_prompt(
    query: str,
    chunks: list[RetrievedChunk],
    *,
    dispatch_mode: str = "replace",
) -> PromptMessages:
    """Build system+user messages with formatted chunk context.

    dispatch_mode: "replace" (W26 F2 baseline default) | "append" (W27 F1 candidate)
    — passed through to `_format_chunk` per Settings.parent_doc_dispatch_mode.
    Default "replace" preserves W26 F2 G semantics + existing 7 test invariants.
    """
    if not chunks:
        chunk_block = "(no chunks retrieved)"
    else:
        chunk_block = "\n\n".join(_format_chunk(c, dispatch_mode=dispatch_mode) for c in chunks)

    user_msg = f"Question: {query}\n\nRetrieved chunks:\n{chunk_block}\n\nAnswer with citations."
    return PromptMessages(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
    )
