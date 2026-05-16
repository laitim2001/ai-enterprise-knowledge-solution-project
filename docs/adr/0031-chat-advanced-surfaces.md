# ADR-0031: Chat advanced surfaces — Conversation History(Beta+) + 3 citation placement modes + FeedbackBar(**option set on Conversation History scope — Chris pick at W19 F6**)

**Date**: 2026-05-16
**Status**: **Accepted (Option B server-side Tier 1)** — W19 F6 Chris pick 2026-05-16。Chris selected Option B over Option A localStorage-only Tier 1(W19 F2 §6 recommendation + C10 §7 spec)和 Option C Tier 2 defer。**Implications**:promotes C10 §7 Tier 2 server-side persistence to Tier 1;Postgres `conversations` + `messages` tables + 6 `/conversations` CRUD endpoints + ~3 backend days extends Wave A backend budget(~5-7 → ~8-10 days)+ cross-device + cross-browser availability for users
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §5.2 Chat`(per ADR-0024)spec covers basic chat:KB selector + message bubble + streaming text + inline citation card + screenshot modal + thumbs feedback。

`references/design-mockups/ekp-page-chat.jsx PageChat`(per W19 F1 audit) implements significant Tier 1 enhancements beyond spec:

1. **Conversation History sidebar(Beta+ scope per C10 §7)** — `ConversationHistoryPanel` left sidebar(260px)with:
   - New chat button + search box
   - Privacy notice("Private to {user}" + "localStorage")
   - Conversations grouped today / yesterday / this-week / older
   - `ConversationItem` with title + KB badge + message count + starred indicator
   - 8 mock conversations(`MOCK_CONVERSATIONS`)matching backend schema(NEW)— currently no `Conversation` schema in `backend/api/schemas/`
2. **3 citation placement modes** via `tweaks.citationPlacement`:
   - `sidebar`(default) — `CitationPanel` right sidebar 400px with full source cards
   - `inline` — `SourcesStrip` at end of answer with 2-col SourceDocCard grid
   - `hover` — only `CitationPill` markers `[1][2][3]` in answer text + hover popover with chunk preview
3. **InlineImageCard** — figure block embedded in answer body with `SyntheticScreenshot` SVG + caption + "Full size" button → ScreenshotModal
4. **ImageGallery** — when 2+ images cited,grid of clickable thumbnails appears below answer
5. **CitationPill with hover popover** — `[N]` markers in answer text,hover shows chunk preview with doc title + section_path + relevance_score + chunk_text_preview
6. **FeedbackBar with comment reveal** — `POST /feedback` per C06 + thumbs_up/down buttons + comment box that appears after rating + "Skip" / "Submit feedback"
7. **CRAG strip indicator** — appears above answer body when `crag_triggered: true`,shows "CRAG L2 re-retrieve · confidence X.XX < 0.70 threshold · added N chunks via query_decomposition" + "View trace →" link

Per W19 F1 audit §2.1 D7,these 7 surfaces are a substantial Tier 1 enhancement — sufficiently large to warrant a dedicated ADR rather than absorbing into ADR-0024 unified shell scope。Per W19 F2 §6 recommendation,**promote to 6th ADR(ADR-0031 NEW)** alongside ADR-0025-0029。

Strategic question:**Conversation History scope** — Tier 1 localStorage-only vs Tier 1 server-side persistence vs Tier 2 defer。

Per CLAUDE.md §5.1 H1 — `architecture.md v6 §5.2 Chat` content additions(Conversation History sidebar + citation modes + advanced surfaces)= architectural addition → requires ADR per H1。

## Decision

Adopt the **Chat advanced surfaces bundle** per prototype。Amend `architecture.md v6 §5.2` to include:

- **Conversation History sidebar**(scope option set — see below)
- **3 citation placement modes**(tweaks-driven UI variant)
- **Inline image cards + image gallery + citation pill hover popover**(citation render enrichment)
- **FeedbackBar with comment reveal**(extends existing thumbs_up/down)
- **CRAG strip indicator**(extends existing response render)

### Conversation History scope(option set — Chris pick at W19 F6)

#### Option A — localStorage-only Tier 1(Beta+ scope per C10 §7)

- Per-user conversation history persists in browser localStorage(client-side only)
- Privacy notice "Private to {user} · localStorage" surface
- No backend `/conversations` endpoint group
- Backend scope:**0 NEW endpoints**
- Trade-off:user loses history on browser change / device switch / cookie clear;Beta cohort small scale tolerates this
- Tier 2 promotes to server-side persistence(`/conversations` CRUD + Postgres `conversations` table)

#### Option B — server-side Tier 1(promote C10 §7 to active)

- Per-user conversation history persists in Postgres `conversations` table per ADR-0023 extension
- Cross-device + cross-browser availability
- Backend scope:`/conversations` CRUD endpoint group ~= **6 NEW endpoints + 1 NEW table**:
  - `GET /conversations?user_id={id}` → list[ConversationSummary]
  - `GET /conversations/{id}` → ConversationDetail(messages + citations)
  - `POST /conversations` → ConversationCreate response
  - `PATCH /conversations/{id}` → title rename + starred toggle
  - `DELETE /conversations/{id}`
  - `POST /conversations/{id}/messages` → append message + citations
- Postgres migration:`conversations` table + `messages` table(replaces in-memory)
- Effort:~3 backend days
- Tier 2 promotes to multi-user share + URL share

#### Option C — Tier 2 defer entirely

- Conversation History sidebar NOT shipped Tier 1(disabled affordance "Conversation history coming Tier 2" with rolling chat reset on page reload — current behavior)
- Backend scope:**0 NEW**
- Tier 2 promotes per C10 §7 schedule

**Recommended pick**:**Option A localStorage-only Tier 1**。Rationale:
- C10 §7 explicitly schedules localStorage Beta+ Tier 1 + server-side Tier 2(prototype design matches spec)
- Beta cohort small scale + internal Ricoh users typically single-device per Q7 — cross-device benefit marginal
- Backend cost 0 days vs Option B 3 days — frees Wave A backend budget for ADR-0025 Images + Chunking Lab + KbConfig multimodal additions
- Tier 2 path clear:Postgres `conversations` + `messages` migration is additive when promoted post-Beta governance

### 3 citation placement modes

- **All 3 modes Tier 1**(frontend-only,no backend)
- Default = **sidebar**(per `<CitationPanel>` right sidebar 400px,full source cards with image thumbnail + relevance bar + open-source + screenshot buttons)
- Tweaks-driven via `tweaks.citationPlacement` query param or per-user preference(localStorage persistence)
- Trade-off:additional rendering modes increase frontend code complexity ~30%,but provide operator UX flexibility for different scenarios(dense citation = sidebar / read-flow = inline / minimal = hover popover only)

### Inline image cards + gallery + citation pill hover popover

- All Tier 1(frontend-only,no backend)
- `InlineImageCard` figure block:image thumbnail + caption + "Full size" button(opens ScreenshotModal)
- `ImageGallery`:appears below answer when 2+ images cited(grid layout `auto-fill, minmax(180px, 1fr)`)
- `CitationPill` hover popover:shows chunk_title + section_path + relevance_score + chunk_text_preview without leaving answer context

### FeedbackBar with comment reveal

- Tier 1,extends existing `POST /feedback` per C06 schema
- Adds:thumbs_up/down state preservation + comment box reveal post-rating + Skip/Submit actions
- Backend impact:`FeedbackRequest` schema(`schemas/feedback.py:8`)already accepts `comment?: str` field per W7-W8 spec — verify with W19 F2 grep

### CRAG strip indicator

- Tier 1,reads `QueryResponse.crag_triggered: bool` + `crag_iterations: int`(per W19 F2 §3.1 item 5 — needs verify in `schemas/query.py:52`)
- Frontend renders accent-colored strip above answer body when `crag_triggered: true`
- "View trace →" link → `/traces/[traceId]` for full 9-stage debug

## Alternatives Considered

1. **Drop Conversation History sidebar entirely Tier 1**(Option C above) — rejected。Operator usability regression — chat reset on page reload is poor UX for Beta cohort doing extended ERP-manual queries(per Q7 + Q14 D365 F&O ERP scope)。
2. **Server-side Conversation History Tier 1**(Option B above)— rejected per recommendation。3 backend days exceeds Wave A budget for marginal Beta cohort benefit;Tier 2 promotion path clear。
3. **Single citation placement mode only**(drop tweaks-driven variants) — rejected。Different audiences(internal user reading flow / power user dense citation / minimal mode for screen sharing)benefit from placement choice;prototype design includes the variants explicitly per UX iteration value。
4. **Drop InlineImageCard + ImageGallery + CitationPill hover popover**(simpler citation render) — rejected。Image-grounded citations are EKP's "not another chatbot" signature(per technical-highlight Q10 answer)+ stakeholder W18 closeout signal;hiding the multimodal capability defeats the differentiator。
5. **Drop FeedbackBar comment reveal** — rejected。Feedback with comment context is operationally valuable(Eval tuning loop relies on qualitative feedback per Q15 weekly signal report)— minor frontend addition,worth keeping。
6. **Drop CRAG strip indicator**(per spec §5.2 no mention) — rejected。CRAG visualization is the technical-highlight Q10 answer #1(Chris-confirmed Q10 selection);hiding it defeats the differentiator + reduces operator trust signal("how did EKP arrive at this answer?" question)。

## Consequences

**Per Option A(recommended)**:

**Positive**:
- Tier 1 chat experience matches stakeholder W18 closeout signal「rich chat with history + citation modes + multimodal viz」without backend scope cost
- Conversation History sidebar covers C10 §7 spec exactly(localStorage Tier 1 + server-side Tier 2)— no premature promotion
- 3 citation placement modes provide UX flexibility for different operator scenarios
- CRAG strip indicator + InlineImageCard + ImageGallery demonstrate EKP's multimodal + self-correcting RAG technical highlights to operators(per Q10)
- FeedbackBar with comment reveal feeds Eval tuning loop(per Q15 weekly signal)
- Backend changes minimal:verify `FeedbackRequest.comment` + verify `QueryResponse.crag_*` fields — no NEW endpoints

**Negative**:
- Operator loses conversation history on browser change / device switch / cookie clear — Beta cohort tolerates per small scale;Tier 2 server-side promotion lifts this constraint
- Frontend code complexity ~30% above baseline chat(3 citation modes + history sidebar + image cards + gallery + pill popover + feedback comment + CRAG strip)— accept per high UX value;Wave A frontend effort estimate ~5-7 days for chat polish alone
- SyntheticScreenshot SVG mockups in prototype are design-time only;real `frontend/` impl uses ImageRef.blob_url with real images — confirms `frontend/components/chat/CitationCard` already handles per W3 D4 C10 §3 design notes

**Neutral**:
- `architecture.md v6 §5.2` extension(history sidebar + citation modes + image cards + CRAG strip)inline-tagged at W20-frontend-wave-a kickoff
- `COMPONENT_CATALOG.md` C10 Chat Interface UI row gets「ADR-0031 Chat advanced surfaces — Conversation History localStorage Tier 1 + citation modes + image cards」status note
- `tests/unit/` Vitest scope:CitationPill hover popover + FeedbackBar comment reveal + CRAG strip rendering = 3 NEW test cases per W17 F6 baseline expansion

## References

- `architecture.md v6 §5.2` Chat(spec basis per ADR-0024)+ C10 §7 Future Evolution(Conversation History Tier 1/2 schedule)
- `references/design-mockups/ekp-page-chat.jsx`(`PageChat` lines 72-132;ConversationHistoryPanel lines 136-220;ChatHeader lines 257-299;ChatThread lines 301-373;FeedbackBar lines 377-440;AnswerBody lines 443-500;CitationPill lines 516-578;InlineImageCard lines 581-618;ImageGallery lines 621-664;SourcesStrip lines 667-697;CitationPanel lines 799-828;SyntheticScreenshot lines 912-1065;ScreenshotModal lines 1068-1121;ChatComposer lines 1124-1150)
- `references/design-mockups/ekp-data.jsx`(`MOCK_CONVERSATIONS` lines 449-547 with 8 conversations grouped today/yesterday/this-week/older + starred)
- W19 F1 audit §2.1 D7(Chat advanced surfaces — 7 enhancements)
- W19 F2 backend gap map §3.5 item 22(Conversation History Beta+ localStorage)+ §5 ADR-0031 row + §6 Recommendation #4(NEW 6th ADR)
- C10 design notes `docs/02-architecture/components/C10-chat-ui.md` §7 Future Evolution(Conversation History Tier 1 localStorage + Tier 2 server-side persistence)
- ADR-0024 unified shell IA(`/chat` rendered inside `<AppShell>` with focus-mode toggle)
- ADR-0021 Retrieval Testing(`HybridSearcher.search()` mode param — related but distinct surface)
- W3 D4 C10 streaming + citation card + screenshot modal implementation(existing chat baseline)
- W4 CRAG L2 + W5 D4 NON-STICKY 0.70 threshold(CRAG strip rationale)
- W8 D? POST /feedback per C06(FeedbackBar foundation)
- Q10 visual identity(coral accent for technical highlights + Tier 2 preview)
