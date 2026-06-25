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

SYSTEM_PROMPT_CONCISE = f"""You are Ricoh's internal Knowledge Assistant. Answer the user's question using ONLY the retrieved knowledge chunks below.

Rules:
1. Cite every fact with [chunk-{{chunk_id}}] markers immediately after the sentence that uses the chunk. Use the literal chunk_id from the chunk's header line; never invent or shorten one.
2. If the retrieved chunks do not contain enough information, reply with exactly the phrase: "{REFUSAL_PHRASE}" — do NOT hallucinate.
3. Lead with a direct one-sentence answer to the user's question; then provide supporting details only as needed (target <= 150 words total). Use ordered lists / steps when answering procedural questions.
4. Match the user's language (English / 繁體中文 / 日本語) — do not translate the chunks.
5. Never fabricate chunk_ids; only cite chunks shown below.
6. For overview / aggregate queries (e.g. "show me all X", "list all Y", "describe the integration scenarios"), synthesize what IS available from the chunks even if coverage is partial; explicitly note any gaps via "Based on available documentation:" framing rather than refusing entirely. Only emit the refusal phrase (Rule 2) when chunks are COMPLETELY off-topic — not when partial coverage exists. (CH-005 — R14 mitigation 2026-05-24)
7. For queries asking about specific sub-procedures, walkthroughs, or scenarios numbered with patterns like §X.M (e.g. §8.1, §8.2, §8.3, Scenario A walkthrough, Step 3.2), prefer citing those individually-numbered chunks over higher-level overview or coverage-summary chunks that aggregate them. An intro chunk that merely lists scenario names is insufficient — cite the specific §X.M chunks that describe each scenario's actual procedure. (W33 F1.1.a — Rule 7 v2 restored from W31 commit 16b9b3d per sequential ship on W32 (h') baseline)
8. When multiple retrieved chunks each contain partial information relevant to the answer, cite the chunks that support each fact (typically 1-2 per fact) — avoid citing multiple overlapping chunks that convey the same information. (W35 F1.7 — Rule 8 wording Option C re-tighten from Option B per F1.4 correctness -5pp regression side effect)"""

# CH-006 — backward-compat alias. Existing imports/tests reference `SYSTEM_PROMPT`;
# it stays pinned to the concise (W2 baseline) variant so behaviour + substring tests
# are unchanged when `detail_level` is not requested.
SYSTEM_PROMPT = SYSTEM_PROMPT_CONCISE

# CH-006 — the exact Rule 3 sentence (concise) + its detailed replacement. Deriving
# SYSTEM_PROMPT_DETAILED via .replace() guarantees it is byte-identical to CONCISE
# EXCEPT Rule 3 — no rule duplication, no drift. If _RULE_3_CONCISE ever stops matching
# the prompt text, the replace is a no-op and test_prompt_detail_level catches it
# (detailed would still contain "150 words").
_RULE_3_CONCISE = (
    "3. Lead with a direct one-sentence answer to the user's question; then provide "
    "supporting details only as needed (target <= 150 words total). Use ordered lists "
    "/ steps when answering procedural questions."
)
_RULE_3_DETAILED = (
    "3. Lead with a direct one-sentence answer to the user's question; then reproduce "
    "the FULL procedure in COMPLETE detail — enumerate EVERY DISTINCT step and sub-step "
    "exactly as the retrieved chunks describe, and do NOT summarize or omit any step. "
    "There is no word limit. Preserve the source's button / menu / field names verbatim.\n"
    "FORMAT — render the ENTIRE procedure as ONE single CONTINUOUS nested ordered "
    "(numbered) list that preserves the source's grouping as nesting levels:\n"
    "- Each top-level group (e.g. 'GL03-1. Create General Journal') is a level-1 numbered "
    "item; make its title bold.\n"
    "- Each sub-procedure (e.g. 'Create General Journal header', 'Prepare excel file', "
    "'Upload excel file') is a level-2 numbered item nested under its parent group; make "
    "its title bold.\n"
    "- Each individual step is a level-3 numbered item nested under its sub-procedure.\n"
    "Do NOT use Markdown headings (#, ##, ###) for any group or sub-procedure — group "
    "titles MUST be bold items inside the numbered hierarchy, never headings. Do NOT "
    "flatten the procedure into one long single-level decimal list, and do NOT restart "
    "the numbering per group as a separate list. Worked example (copy the STRUCTURE, not "
    "this content):\n"
    "1. **GL03-1. Create General Journal** — when excel file is used to upload records. [chunk-AAA]\n"
    "   1. **Create General Journal header** [chunk-AAA]\n"
    "      1. Click General ledger > Journal entries > General journals. [chunk-AAA]\n"
    "      2. Click New. [chunk-AAA]\n"
    "   2. **Prepare excel file outside of system** [chunk-AAA]\n"
    "      1. Prepare excel file. [chunk-AAA]\n"
    "      2. Sample file is here. [chunk-AAA]\n"
    "   3. **Upload excel file** [chunk-AAA]\n"
    "      1. Go to Workspaces > Data management. [chunk-AAA]\n"
    "DEDUP — the source manuals often repeat the SAME step in more than one form: a "
    "process-step-list / index table that names the steps, the section heading for that "
    "step, and a caption that restates it. List each distinct step ONLY ONCE: never "
    "repeat the same (or a trivially-reworded) step title on consecutive lines, and "
    "treat a summary / process-step-list table as the OUTLINE for the grouped steps "
    "rather than enumerating its entries as separate steps. (BUG-036)"
)

# Detailed variant: concise prompt with ONLY Rule 3 swapped (CH-006).
SYSTEM_PROMPT_DETAILED = SYSTEM_PROMPT_CONCISE.replace(_RULE_3_CONCISE, _RULE_3_DETAILED)

# W70 / ADR-0055 — appended as Rule 9 ONLY when inline image markers are active
# (`build_prompt(inline_image_markers=True)`); the knob-off system prompt stays
# byte-identical to pre-W70.
_MARKER_RULE = (
    "9. Some chunk texts contain inline image markers like [IMG#a1b2c3d4] marking where "
    "a screenshot appears in the source document. When you reproduce a step or passage "
    "from a chunk, copy each [IMG#...] marker with it, keeping the marker at its original "
    "position relative to the surrounding text (immediately after the step it follows in "
    "the source). NEVER invent, alter, duplicate, or move markers across steps; only emit "
    "markers that literally appear in the chunks. Do not describe or mention the markers "
    "in prose."
)

# W97 / ADR-0069 — appended ONLY when `build_prompt(complete_coverage=True)` AND
# `detail_level == "detailed"` (no-op under concise). Targets 乙類 over-summarisation:
# the detailed prompt already enumerates main-line steps but drops CONDITIONAL VARIANTS
# / ALTERNATIVE BRANCHES / SCENARIO sub-procedures (W96 gate F8 C003 dropped 9 nuggets,
# all of this kind). The rule is additive (mirror `_MARKER_RULE`); the knob-off prompt
# stays byte-identical to pre-W97. Labelled (not digit-numbered) so it composes after
# the optional Rule 9 marker rule without a numbering collision. It also calibrates the
# Rule 3 DEDUP clause so a genuine variant is never folded away as a「duplicate」.
_COVERAGE_RULE = (
    "COVERAGE — beyond the main-line procedure, the retrieved chunks often describe "
    "CONDITIONAL VARIANTS, ALTERNATIVE BRANCHES, and SCENARIO sub-procedures (e.g. "
    "'for a single customer', 'for multiple customers', 'for RMS only', 'for the approval "
    "workflow', 'if the journal is reversed'). You MUST enumerate EVERY such variant / "
    "branch / scenario that appears in the chunks — render each as its own bold branch "
    "title followed by its steps — even when it is optional, parallel, or an exception "
    "path, and even when it shares its opening steps with the main path. Do NOT collapse "
    "distinct branches into one, and do NOT silently pick only the most common path. This "
    "REFINES the DEDUP rule: DEDUP removes only restatements of the SAME step (a "
    "process-step-list entry, a heading, a caption) — a genuinely different conditional "
    "branch is NEVER a duplicate and must be kept. Also reproduce any short Overview / "
    "summary passage that introduces a section's scenarios."
)


def _system_prompt_for(detail_level: str) -> str:
    """Pick the synthesis system-prompt variant (CH-006).

    `"detailed"` → no-word-cap full-enumeration prompt; anything else (incl. the
    default `"concise"`) → the W2 baseline prompt. Unknown values fall back to concise
    so a stray config value never breaks synthesis.
    """
    return SYSTEM_PROMPT_DETAILED if detail_level == "detailed" else SYSTEM_PROMPT_CONCISE


@dataclass(slots=True, frozen=True)
class PromptMessages:
    """OpenAI chat.completions messages — system + user only (no history yet)."""

    messages: list[dict]


def _format_chunk(
    chunk: RetrievedChunk,
    *,
    dispatch_mode: str = "replace",
    use_marked: bool = False,
) -> str:
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
    if use_marked:
        # W70 / ADR-0055 — raw-text path switches to the marked variant; "" (chunk
        # has no markers OR pre-W70 index without the field) falls back to clean
        # text. parent_section_text / expanded_text are already marked variants
        # when the knob is on (assembled upstream with use_marked threading).
        chunk_text = str(chunk.fields.get("chunk_text_marked") or "") or chunk_text

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
    detail_level: str = "concise",
    inline_image_markers: bool = False,
    complete_coverage: bool = False,
) -> PromptMessages:
    """Build system+user messages with formatted chunk context.

    dispatch_mode: "replace" (W26 F2 baseline default) | "append" (W27 F1 candidate)
    — passed through to `_format_chunk` per Settings.parent_doc_dispatch_mode.
    Default "replace" preserves W26 F2 G semantics + existing 7 test invariants.

    detail_level: "concise" (default, W2 baseline 150-word system prompt) | "detailed"
    (CH-006 — no-word-cap, full sub-step enumeration). Default preserves existing
    behaviour + system-prompt substring tests.

    inline_image_markers: W70 / ADR-0055 — True switches the raw chunk-text path to
    `chunk_text_marked` (falling back to clean text per chunk) AND appends the
    keep-markers system rule. Default False = pre-W70 byte-identical prompts.

    complete_coverage: W97 / ADR-0069 — True appends the additive COVERAGE rule
    (enumerate conditional variants / branches / scenarios) ONLY when detail_level is
    "detailed"; a no-op under concise. Default False = pre-W97 byte-identical prompts.
    """
    if not chunks:
        chunk_block = "(no chunks retrieved)"
    else:
        chunk_block = "\n\n".join(
            _format_chunk(c, dispatch_mode=dispatch_mode, use_marked=inline_image_markers)
            for c in chunks
        )

    system_prompt = _system_prompt_for(detail_level)
    if inline_image_markers:
        system_prompt = f"{system_prompt}\n{_MARKER_RULE}"
    # W97 / ADR-0069 — the coverage rule only makes sense atop the full-enumeration
    # detailed prompt (it refines that prompt's DEDUP clause); under concise it is a
    # no-op so the 150-word baseline answer shape is untouched.
    if complete_coverage and detail_level == "detailed":
        system_prompt = f"{system_prompt}\n{_COVERAGE_RULE}"

    user_msg = f"Question: {query}\n\nRetrieved chunks:\n{chunk_block}\n\nAnswer with citations."
    return PromptMessages(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]
    )
