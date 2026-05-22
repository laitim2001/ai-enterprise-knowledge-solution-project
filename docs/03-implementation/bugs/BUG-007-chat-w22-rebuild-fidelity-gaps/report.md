---
bug_id: BUG-007
title: "Chat W22 F4 presentation rebuild dropped 3 mockup-spec'd surfaces — meta-row model+cost, sources-panel toggle, ImageGallery"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "User (Chris) — frontend chat test 2026-05-22 (3 screenshots)"
affects_components: [C10, C05, C07]   # C10 Chat UI · C05 Generation (stream_composer) · C07 Observability (realtime_cost)
spec_refs:
  - architecture.md §5                              # UI Specifications — Chat view
  - references/design-mockups/ekp-page-chat.jsx     # canonical visual spec (H7)
  - CLAUDE.md §5.7 H7                               # Design Fidelity Constraint
---

# BUG-007 — Chat W22 F4 rebuild dropped 3 mockup-spec'd surfaces

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3**(3 H7 design-fidelity regressions introduced by the W22 F4 chat presentation rebuild;chat functions, no data loss, but `/chat` deviates from the canonical mockup);**Chris confirmed Sev3 + Bug-fix BUG-007 workflow(report + checklist + progress;Sev3 → no postmortem)via chat 2026-05-22**。Cost-display sub-decision confirmed:**backend computes + emits**(reuse `realtime_cost.py` `_PRICING_TABLE`)。

## 1. Symptom

用戶喺 `/chat`(localhost dev)對一個真實 KB 發問,留意到 3 處同 mockup(`references/design-mockups/ekp-page-chat.jsx`)唔對齊:

1. **AI 回應 meta 行** — mockup 係 `EKP gpt-5.5 · cohere-v4.0-pro · 5 citations · 2 with screenshots` … `4.13s · $0.029`;實作係 `EKP cohere-v4.0-pro · 3 citations` … `12.20s` —— **缺 model name(`gpt-5.5`)**、**缺 cost(`$0.029`)**。
2. **冇 sources-panel toggle** — `/chat` header 冇 mockup 嗰個 toggle 掣,亦冇右側 Sources panel。
3. **答案底部** — 實作只有「Sources」section;mockup 仲有一個「Referenced screenshots」section(responsive image-card grid)。

## 2. Reproduction Steps

1. `/chat`,KB 下拉揀一個真實 KB,發任何 query
2. Observed:assistant message meta 行 = `EKP cohere-v4.0-pro · N citations` + 右側 latency,**冇 model name、冇 cost**
3. header 右側 = `CRAG` switch + `Show images` switch + focus eye —— **冇 sources-panel toggle**(`BookOpen` 掣)
4. 答案底部只渲染「Sources」strip —— **冇「Referenced screenshots」gallery**

**Reproduction reliability**:Always(deterministic — 全部係靜態 render 邏輯 / 預設值差異)。

**Environment**:local dev frontend + backend(real Azure AI Search)。

## 3. Expected vs Actual

### 問題 1 — meta 行

| 子項 | Expected(mockup `:324-329`) | Actual(`page.tsx:1075-1087`) | 判定 |
|---|---|---|---|
| Model name | `gpt-5.5 · ` 前綴 | 缺 | **真 bug** — backend `done` event **有** send `model`(`stream_composer.py:48`),但前端 `done` handler 冇 capture `evt.model`,`Message` type 冇 `model` field |
| Cost | `· $0.029` | 缺 | **真 bug** — backend `done` event **冇** cost field(只有 `input_tokens`/`output_tokens`);`Message.costUsd` 已宣告但從未 populate |
| Latency 數值 | `4.13s`(sample) | `12.20s`(real) | **正常** — 真實 latency,顯示邏輯本身正確 |
| `N with screenshots` | `2 with screenshots` | 省略 | **正常(data-driven)** — real docx KB 冇 embedded screenshots → `imageCitations.length=0` → 實作正確噉省略;mockup 嗰句係 sample data |

### 問題 2 — sources-panel toggle

| 範疇 | Expected(mockup) | Actual |
|---|---|---|
| 預設 citation placement | `sidebar`(mockup `:79` `tweaks.citationPlacement \|\| "sidebar"`)| `inline`(`page.tsx:159` `useState<CitationMode>('inline')`)|
| Header sources toggle | sidebar mode 顯示 `BookOpen` toggle(mockup `:290-295`)| toggle 只喺 `citationMode==='sidebar'` render(`page.tsx:912`)→ inline 預設下永不顯示 |
| 右側 Sources panel | sidebar 預設 → `CitationPanel` 400px 顯示 | 永不顯示;亦無任何 UI 可切回 sidebar mode → 用戶 permanently lock 喺 inline |

### 問題 3 — 答案底部

| 範疇 | Expected(mockup) | Actual |
|---|---|---|
| `ImageGallery`(「Referenced screenshots」)| mockup `:621-664` — header + count badge +「View all in Image Library →」+ responsive grid `repeat(auto-fill, minmax(180px,1fr))`;`imageCitations.length>=2` 先 render(`:355`)| **完全缺失** — `page.tsx:42-44` comment 將 `ImageGallery` 誤當「W20 custom abstraction」刪走 |
| `SourcesStrip`(「Sources」)| mockup `:667-697` — grid `1fr 1fr` 固定 2-col | **已正確存在且 faithful**(`page.tsx:1304` 同樣 `1fr 1fr`)— **非 bug**;用戶觀察到嘅「卡片固定大小」正是 mockup 行為,改成 responsive 反而 violate H7 |

## 4. Impact

- **Affected users / scenarios**:任何 user 喺 `/chat` 發問 —— meta 行資訊不全、無法切換 / 查看 Sources panel、有 embedded screenshots 嘅答案缺少 gallery。
- **Workaround available?**:N/A — chat 功能正常,純 presentation fidelity 缺陷,用戶無需 workaround。
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:3 處 H7 design-fidelity 缺陷,chat 核心功能(query / streaming / citation / conversation)完全正常,無 data loss、無 security 影響。非 Sev2(無 broken core flow)。但 per CLAUDE.md §5.7 H7「`references/design-mockups/` 100% reproduction」,實作偏離 canonical mockup = fidelity defect,需修正。Sev3 → **無需 postmortem**。

## 6. Initial Diagnosis（root cause confirmed）

**Confirmed via mockup + implementation + backend SSE 三方 trace(2026-05-22)**:

三項全部係 **W22 F4 chat presentation rebuild** 引入嘅 fidelity regression(`page.tsx` 開頭 docstring 自記當時決定):

- **問題 1a(model)**:`query.ts` `DoneEvent` 已含 `model: string`(`:69`);backend `stream_composer.py:48` `done` event emit `model = event.get("deployment")`。但 `page.tsx` `done` handler(`:357-365`)只 capture `isStreaming/refused/rerankerUsed/latencyMs`,**冇 `model`**;`Message` interface 亦無 `model` field。→ 純前端 wiring gap。
- **問題 1b(cost)**:backend `done` event 只 emit `input_tokens`/`output_tokens`,**無 cost**。`page.tsx` `Message.costUsd` field 已宣告但 `done` handler 從不 populate。`backend/observability/realtime_cost.py` `_PRICING_TABLE` 已有 `gpt-5-5` per-1k-token rate(`input 0.005 / output 0.015`)+ prefix-tolerant `_rate_for` lookup —— 但無 per-query 單值 helper。→ 需 backend 加 cost 計算 + emit、前端加 field + display。
- **問題 2**:mockup 預設 placement = `sidebar`(`:79`)。W22 F4 將 `citationMode` 預設由 `sidebar` flip 去 `inline`(`page.tsx:159` + `:26-29` docstring 寫明「to match no-toggle UX」)。但 sources toggle 同右 panel 都 gated 喺 `sidebar` mode → flip 之後兩者永不顯示。`ekp-citation-mode` localStorage key 喺呢頁係 read-only(從不寫入)→ 預設值實際永遠生效。→ 預設值改回 `sidebar` 即修正。
- **問題 3**:mockup **有** `ImageGallery` component(`:621-664`,名稱一致)。`page.tsx:42-44` docstring 將佢列入「Obsolete W20 separate components ... deleted」—— 誤判:`ImageGallery` 係 mockup 既有 component,W22 F4 rebuild 錯誤刪除。→ 重建 `ImageGallery`(thumbnail 用 real `blob_url` 而非 mockup 嘅 synthetic SVG,同 `ScreenshotModal` 既有 real-image adaptation 一致)。

**Root cause**:W22 F4「presentation layer rebuild」過程將部分 mockup-spec'd surface(model/cost wiring、sidebar 預設、`ImageGallery`)當作 W20-era custom abstraction 移除 / 簡化,引入 3 處 H7 fidelity regression。所有 W22 automated gate(`tsc`/`lint`/`[oklch`=0)皆綠 —— 但都不 measure presentation fidelity(同 W21 retro 揭示嘅 pattern 一致)。

**Fix scope**:backend(問題 1b cost — `realtime_cost.py` NEW helper + `stream_composer.py` `done` event)+ frontend(問題 1a/1b/2/3 — `query.ts` `DoneEvent` + `page.tsx`)。Backend 不改 vendor / storage / component → 非 H1;無新 dependency → 非 H2;`done` event 加 additive field 同 W20 F2.1 `/health` payload 擴充先例一致,非 architectural change。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — 3 處 W22 F4 fidelity regression,via mockup + impl + backend SSE 三方 trace
- [ ] **問題 1b backend** — `realtime_cost.py` NEW public `estimate_query_cost(model, input_tokens, output_tokens) -> float | None`,reuse `_rate_for` + `_PRICING_TABLE`(單一 pricing source)
- [ ] **問題 1b backend** — `stream_composer.py` `done` event 加 `cost` field(用 `estimate_query_cost` 計;deployment 無 rate row 時 `cost=null`)
- [ ] **問題 1a/1b frontend** — `query.ts` `DoneEvent` 加 `cost: number | null`;`page.tsx` `Message` 加 `model`、`done` handler populate `model`+`costUsd`、meta 行 render `{model} · {reranker} · {N} citations[ · {N} with screenshots]` … `{latency}s · ${cost}`
- [ ] **問題 2 frontend** — `page.tsx` `citationMode` 預設 `'inline'` → `'sidebar'`(對齊 mockup `:79`);更新 `:26-29` docstring
- [ ] **問題 3 frontend** — `page.tsx` 重建 `ImageGallery` component(「Referenced screenshots」header + count badge +「View all in Image Library →」inert + responsive grid;`imageCitations.length>=2` render;thumbnail 用 `blob_url`);更新 `:42-44` docstring
- [ ] **Test** — backend:`test_realtime_cost.py` + `test_stream_composer.py` 加 case(`estimate_query_cost` + `done` event `cost`);frontend:Vitest 加 meta-row(model+cost)+ ImageGallery render case
- [ ] verify gates — backend `pytest` no regression + `mypy` 改動 module clean;frontend `tsc` exit 0 + `next lint` clean + `[oklch`=0 + Vitest no regression
- [ ] **H7 self-verify** — 3 處改動逐項對齊 mockup(meta 行 `:324-329` / sidebar 預設 `:79` / `ImageGallery` `:621-664`);改動方向 = implementation → mockup(per §5.7「修正 visual drift bug」非 H7 trigger)
- [ ] **Out of scope（不修）**:`SourcesStrip` `1fr 1fr` grid(已 faithful,改 responsive 反 violate H7);CRAG strip 喺 streaming chat 不顯示(streaming path 無 CRAG per `query.py:134-136`「non-stream path only」— architectural 既定,非 bug);`ImageGallery` 喺真實 docx KB(無 embedded images)latent 不顯示(需有 screenshots 嘅 KB 先見);`backend/observability` 的 Langfuse-based realtime cost 聚合(無關)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev3)+ root cause confirmed via mockup + implementation + backend SSE 三方 trace（3 處 W22 F4 fidelity regression）+ cost-display sub-decision = backend computes + emits（reuse `realtime_cost.py` `_PRICING_TABLE`）| User(Chris)reported 3 處 `/chat` 同 mockup 唔對齊 2026-05-22;Chris confirmed Bug-fix BUG-007 + Sev3 + cost A+B(backend 計+emit)| Chris(chat-confirm 2026-05-22)|
| 2026-05-22 | Fix landed + verified → status `triaged → done`。Backend:`realtime_cost.py` NEW `estimate_query_cost` + `stream_composer.py` `done` event `cost`。Frontend:`query.ts` `DoneEvent.cost`;`page.tsx` meta-row model+cost wiring + `citationMode` 預設 `sidebar` + `ImageGallery` 重建。Tests:backend +5(test_stream_composer +2 / test_realtime_cost +4 — 實 +5 含既有 case assertion)、frontend NEW `chat-meta-row.test.tsx`(2 cases)。Verify:backend pytest **919 passed / 11 skipped**(914 baseline +5,exit 0)+ `mypy` changed modules 0 error + `ruff` clean;frontend `tsc` exit 0 + `next lint` clean + `[oklch`=0 + Vitest **23 files / 91 tests / 0 fail**(deterministic 3-batch)。| BUG-007 single-sitting close | Chris |
| 2026-05-22 | **Amendment** — 用戶重測 `/chat` 3 問題仍在,root-cause 出 3 個 residual defect(詳見 `progress.md` amendment 段 A1-A3):A1 `_rate_for` dot/dash mismatch(`gpt-5.5` vs `gpt-5-5`)→ cost null → dot/dash normalization;A2 stale `ekp-citation-mode` localStorage override `sidebar` 預設 → 移除 `citationMode` hydration;A3 `SourcesStrip` grid `1fr 1fr` real-data overflow → `minmax(0,1fr)`(BUG-007 原 D5 mis-judgment 更正)。Verify:backend 60 passed(affected files,+3 NEW test)+ ruff/mypy clean;frontend tsc/lint/`[oklch`=0 + Vitest chat 4 passed。| Chris confirmed BUG-007 amendment(chat 2026-05-22)| Chris |

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
