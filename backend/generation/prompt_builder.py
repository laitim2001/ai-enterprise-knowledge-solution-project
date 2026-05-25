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
6. For overview / aggregate queries (e.g. "show me all X", "list all Y", "describe the integration scenarios"), synthesize what IS available from the chunks even if coverage is partial; explicitly note any gaps via "Based on available documentation:" framing rather than refusing entirely. Only emit the refusal phrase (Rule 2) when chunks are COMPLETELY off-topic — not when partial coverage exists. (CH-005 — R14 mitigation 2026-05-24)"""


@dataclass(slots=True, frozen=True)
class PromptMessages:
    """OpenAI chat.completions messages — system + user only (no history yet)."""

    messages: list[dict]


def _format_chunk(chunk: RetrievedChunk) -> str:
    """Format a chunk for LLM context.

    Dispatch chain (ADR-0037 W26 F2 extends ADR-0020):
    1. `parent_section_text` — siblings aggregated by Parent-Document Retriever
       (`backend/generation/parent_doc_retriever.py`); supersedes `expanded_text`
       for the anchor chunk when `enable_parent_doc_retrieval=True`.
    2. `expanded_text` — prev/next ±1 chunk window per ADR-0020 Context Expander.
    3. `chunk_text` — raw chunk text (W2 baseline) when neither expansion applied.

    Citation invariant preserved: even when LLM sees parent_section_text, the
    cited chunk_id references the original anchor (parent section is LLM-input-
    only enrichment per architecture.md §3.5 Citation contract).
    """
    cid = str(chunk.fields.get("chunk_id", ""))
    title = str(chunk.fields.get("chunk_title", "") or "(untitled)")
    section = " > ".join(chunk.fields.get("section_path") or [])
    text = str(
        chunk.fields.get("parent_section_text")
        or chunk.fields.get("expanded_text")
        or chunk.fields.get("chunk_text", "")
    )
    section_line = f"  Section: {section}\n" if section else ""
    return (
        f"[chunk-{cid}] {title}\n"
        f"{section_line}"
        f"  Text: {text}"
    )


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> PromptMessages:
    """Build system+user messages with formatted chunk context."""
    if not chunks:
        chunk_block = "(no chunks retrieved)"
    else:
        chunk_block = "\n\n".join(_format_chunk(c) for c in chunks)

    user_msg = (
        f"Question: {query}\n\n"
        f"Retrieved chunks:\n{chunk_block}\n\n"
        f"Answer with citations."
    )
    return PromptMessages(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
    )
