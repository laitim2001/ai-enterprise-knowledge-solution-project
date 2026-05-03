---
phase: W02-multi-format-ingestion
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress    # in-progress | closed (set on retro signoff)
---

# Phase W02 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-02: Kickoff(prepared during W1 D4)

**Action**:Phase W02 kickoff(per Chris call to prep during W1 D4-D5 capacity)

- Folder `docs/01-planning/W02-multi-format-ingestion/` created
- Templates copied from `_templates/phase/`(v2.0 unified naming `progress.md`)
- `plan.md` filled with status=`draft`(11 deliverables F1-F11,5 carry-overs from W1,Gate 1 R@5 ≥ 80% hard gate per `architecture.md §6.3`)
- `checklist.md` derived from plan deliverables(75+ atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over from W01-foundation retro**:
  - F1 Docling parser PoC(was W1 F8;Q2 unblocked D4,R8 still active)
  - F4 embedding pipeline(was W1 F10;HTTP REST fallback path)
  - F8 ground truth fill(was W1 F11;cascade after F1+F2+F5 for chunk_id)
  - F10 unit tests(was W1 F2+F7;R8 hard prerequisite)
  - Q3 outstanding minor cleanup(tier + region confirm)
  - R8 mitigation P1/P2 ops decision

**Status update 2026-05-02**(W1 D5 early closeout):Chris evening session sign-off W1 retro + approve W02 plan → `plan.md` status flipped `draft → active`(per Plan Changelog 2026-05-02 entry)。W2 D1 implementation start 仍按 plan 2026-05-05 Tue,early closeout 唔影響 sprint timeline。

**W1 carry-overs confirmed in W02 plan §6**:F8(W02 F1)/ F10(W02 F4)/ F11(W02 F8)/ F2 pytest(W02 F10)/ F7 unit tests(W02 F10)/ R8 P1/P2 ops decision(Chris W2 D1 morning)/ Q3 outstanding minor ✅ closed D5 / Langfuse health(W2 D1 morning Chris triage,候選 BUG-001)。

**Commits relevant**:
- `0468040` — `chore(planning): W1 D5 prep — retro draft + W02 kickoff (status=draft)`
- `dc7e37f` — `docs(planning): W1 closeout retro + W02 plan status=active`
- `241fa23` — `docs(planning): replace (this commit) placeholders with actual hashes`

---

### Day 0 evening update — 2026-05-02 (W2 D0 prep variant per Chris call)

**Context**:Chris confirmed 解讀 A 嘅 W2 D0 prep variant — implementation 仍按 plan W2 D1 = 2026-05-05 Tue;今日 evening 用 W1 D5 closeout 後嘅剩餘 capacity 處理 W02 D1 啟動之前嘅 critical path unblock(R11 Langfuse + R8 ops decision)。

#### Done

**BUG-001 instance opened**(per PROCESS.md §4.6 step 1-5):
- AI-classified W1 D5 finding `R11 Langfuse health degradation` 為 Bug-fix workflow → propose `report.md` draft → Chris confirm Sev3 + repro accuracy + reporter line(2026-05-02 evening session)
- mkdir `docs/03-implementation/bugs/BUG-001-langfuse-health-degradation/`(first BUG-NNN instance,sequential 001)
- `report.md` filled,status=`triaged`,Sev3,Chris approved
- `checklist.md` derived from `report.md §7` acceptance + investigation hypothesis paths
- `progress.md` Day 1 entry initialized
- **Investigation phase pending**(W2 D0 evening cont 或 W2 D1 morning,跟 Chris 取捨)

**R8 ops timeline confirmed**:
- Chris W1 D5 closeout session indicated R8 P1 VPN/hotspot window 要再等幾日(non today / non W2 D1 = 2026-05-05 Tue)
- W02 plan §6 dependency 維持:F1 Docling parser 需要 R8 unblock 才可以 pip install;若 W2 D2 plan date(2026-05-06)R8 仍 blocked → 觸發 F1 fallback path(python-docx + custom layout extractor per W02 plan §2 F1 acceptance)
- F4 embedding pipeline HTTP REST fallback path 已喺 W02 plan §2 F4 內 documented,bypass Azure SDK pip install,W2 D5 仍可 deliver

#### Decisions / OQ Resolved

- **Decision** — `R11 Langfuse health degradation` 升格為 BUG-001 instance per PROCESS.md §4.6(Bug-fix workflow,Sev3 minor degraded)。RISK_REGISTER R11 entry stays 🔴 Open until BUG-001 fix verify
- **Decision** — W2 D1 implementation start date 仍按 plan 2026-05-05 Tue,today 屬 W2 D0 evening prep(non implementation start)。W02 plan day breakdown unchanged
- **Decision** — F1 fallback path activation contingency 提早 surface:若 W2 D2(2026-05-06)R8 仍 blocked → switch to python-docx + custom layout extractor;W02 plan §2 F1 acceptance criteria 已 cover both paths,non plan changelog
- **No OQ resolved this entry**(R8 ops 仲未 finalize,Q5/Q11/Q15-21 仍 Open per W2 spread)

#### Blockers

- 🔴 **R8 Ricoh corp proxy**:仍 active,Chris ops decision pending(timeline = "再等幾天")。F1 Docling install path 待 W2 D2 重新 evaluate
- 🟡 **BUG-001 investigation phase pending**(R11 root cause TBD)

#### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| BUG-001 triage(report draft + Chris round-trip + mkdir + 3 docs fill)| 0.5 | 0.4 | -0.1h | Template-driven |
| W02 progress D0 evening update(this entry)| 0.2 | 0.2 | 0 | — |
| **Total D0 evening** | **0.7** | **0.6** | **-0.1h** | Pre-investigation only |

#### Commits

| Hash | Subject |
|---|---|
| `c4473b2` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |

---

### Day 0 evening update — 2026-05-03 (R8 mitigation via home network)

#### Done

**R8 unblock investigation + execution**(home network 2026-05-03):
- Chris pivot home network(disconnect GlobalProtect VPN + connect HKBN home WiFi)
- Network diagnostics confirm:default gateway `192.168.50.1` + public IP `119.247.237.123`(HKBN consumer range)+ no GlobalProtect tunnel in route table
- Test pip download mypy 1.20.2 (10.9MB) → ✅ **15.5 MB/s success first-try**(同 W1 D1/D2/D5 期間 corp 網絡 0 bytes read 完全相反)
- **Root cause refined**:R8 真 root cause 唔係 corp proxy 本身,而係 corp VPN(GlobalProtect)SSL inspection / stream-level interception layer。Disconnect VPN + home ISP direct → R8 disappear
- Batch installed all W2 deps:`pip install -e backend[dev]`(dev tools mypy + pytest + ruff)+ `pip install docling`(W2 F1 Docling parser ~100MB)+ `pip install azure-search-documents azure-identity openai`(W2/W3 Azure cloud SDK)
- **All wheels cached locally** — future corp 網絡 install 可用 `--no-index --find-links` from `.venv\Lib\site-packages` cache bypass

**F2 W1 D1 deferred verification unblocked**(commit batch this session):
- `pytest tests/test_api_skeleton.py` first run → **1 collection error**:`NameError: Fields must not use names with leading underscores`(Pydantic v2.13.3 strict naming on `documents.py:19 _file: UploadFile`)
- Investigated:5 stub routes 同樣 pattern — chunks/documents/eval/feedback/query 全部用 `_<name>` prefix suppress unused-arg linter,W1 D1 寫 stub 時 Pydantic v2.x 未 enforce strict 至 instantiation level
- Fix:rename to `payload` / `file`(match kb.py:22 既有 convention)+ 加 `_ = payload` suppress unused-arg → commit `c38710f`
- Re-run pytest → 1 fail:`test_kb_list_route_registered_returns_501` 預期 501 但 returns 200(W1 D2 F7 commit `c6ca6e3` upgrade `/kb` 做 in-memory CRUD;test 寫 W1 D1 stale)
- Fix:update test 為 `test_kb_list_route_returns_empty_in_memory` 預期 200 + empty list → commit `0a2673d`
- Final verify:**8/8 pass**(F2 W1 D1 deferred 完全 closed)

**Risk + Plan artifact updates this session**:
- RISK_REGISTER R8 status:🔴 Open → 🟢 **Mitigated 2026-05-03**(P1 home network)+ root cause refined entry + side-effect findings logged
- W02 checklist F10:`pre-condition R8 mitigated` ✅ + `pip install` ✅ + `pytest 8/8 pass` ✅;F7 unit tests仲 pending(implementation 期間補,non R8 blocker)
- W02 progress.md Day 0 evening cont entry(this entry)

#### Decisions / OQ Resolved

- **Decision** — R8 root cause refined to corp VPN SSL inspection(non corp proxy itself);home network direct = mitigation path verified。RISK_REGISTER R8 status flipped 🔴 → 🟢 mitigated
- **Decision** — Pydantic v2.13.3 strict naming compat fix 屬 trivial bug fix(< 30min,5 routes 一致 pattern,behavior unchanged 仍 raise 501)— per PROCESS.md §1.4 trivial workflow,non BUG-NNN instance(R1.bugfix exception condition met)
- **Decision** — Stale `test_kb_list` 屬 forgotten test sync after F7 implementation,fix in same commit batch(test/api scope)
- **Decision** — F7 unit tests(`tests/kb_management/`)defer 到 W2 D2-D3 KB Manager Azure backend swap 期間一併寫(per W02 checklist F10 partial close)
- **No new OQ resolved**(R8 status update non-OQ)

#### Blockers

- ✅ R8 cleared(P1 mitigated)
- 🟡 F7 unit tests pending W2 implementation 一併寫(non-blocking,W02 plan §6 carry-over轉化為 W02 F10 partial close)
- 🟡 R10 + Q5 + Q11 + Q15-21 仍 unchanged

#### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| R8 P1 home network attempt + diagnostics | 0.3 | 0.5 | +0.2h | PowerShell `curl` alias confusion + line-wrap retry |
| Batch pip install(dev + Docling + Azure SDK) | 0.5 | 0.3 | -0.2h | Home network fast 15.5 MB/s,5min total |
| Pydantic v2.13 compat fix(5 routes) | 0.5 | 0.4 | -0.1h | grep pattern + 5 parallel Edit batched |
| Stale kb test fix | 0.1 | 0.1 | 0 | 1-line update + docstring |
| RISK_REGISTER + W02 checklist + W02 progress update | 0.3 | 0.3 | 0 | Standard documentation |
| **Total D0 evening 2026-05-03** | **1.7** | **1.6** | **-0.1h** | Surface 2 side-effect bugs but trivial scope |

#### Commits

| Hash | Subject |
|---|---|
| `c38710f` | fix(api): rename _<name> → payload in 5 stub routes (Pydantic v2.13 compat) |
| `0a2673d` | test(api): update kb list test for W1 D2 F7 in-memory impl (no longer 501) |
| `740de4c` | chore(infra): R8 mitigated via home network — F2 W1 deferred unblocked |

---

### Day 0 cont — 2026-05-03 evening: Option A date-shift approved + W2 D1 immediate kick-off

**Context**:Chris call to start W2 D1 immediately — W2 D0 prerequisites all clear(R8 mitigated,Docling installed,F2 W1 verified,BUG-001 closed,Q3 minor closed)。Option A 揀(嚴格 5-working-day shift):D1-D5 整體提早 2 日,D1=2026-05-03 Sun → D5=2026-05-07 Thu。

**Plan artifact updates**(per CLAUDE.md §10 R3 no silent drift):
- `plan.md` frontmatter `start_date: 2026-05-05 → 2026-05-03`,`end_date: 2026-05-11 → 2026-05-07`
- `plan.md` §5 Day-by-Day Breakdown table 同步更新(D1 Sun ... D5 Thu)
- `plan.md` §7 Plan Changelog 加 2026-05-03 entry(Chris approved)
- `plan.md` lifecycle reminder 更新提及 D1 = 2026-05-03 Sun
- `progress.md` Day 1-5 entry headers 同步更新
- `progress.md` retro section header 改 W2 D5 末 / 2026-05-07

**Implementation start**:呢條 entry commit 後,即時 transition 入 Day 1 entry,start F1 Docling parser PoC implementation。

---

## Day 1 — 2026-05-03 (Sun)

### Done

**F1 Docling .docx parser PoC delivered(F1.a–F1.e all closed)**:
- F1.a — Ingestion package skeleton:`backend/ingestion/{__init__.py, parsers/__init__.py, parsers/base.py}`,base.py 定義 `Parser` Protocol + `ParserResult` / `Heading` / `EmbeddedImage` / `Table` dataclasses(per C01 §1 §2 contract)
- F1.b — `DoclingDocxParser` 實作 `Parser` Protocol(`backend/ingestion/parsers/docx_parser.py`),用 Docling `DocumentConverter` 處理 6 sample,提取 SECTION_HEADER(level 2/3/4,filter level=10 TOC anomaly)+ pictures(SHA256 dedup hash 內 parser 計)+ tables(via `export_to_dataframe`)
- F1.c — **Re-scoped to verification(non-implementation)**:Probe Docling output 後發現 SECTION_HEADER detection 已經內部用 visual layout heuristic(font-size + bold + visual cues),全 6 sample 平均 6.3% coverage(level 2/3/4 hierarchy 完整)= W1 D4 F6 raw Word style baseline 3% 嘅 2 倍。F1 acceptance 寫「chunker 必須 add font-size heuristic OR visual layout heuristic」,Docling 已滿足「OR」branch,**唔需要 standalone font-size heuristic code**(per Karpathy §1.2 Simplicity First — 唔重複 Docling 內部嘅工)。
- F1.d — Sanity script(`scripts/run_docx_parser_sanity.py`)+ report(`reports/w02_d1_docx_parser_sanity.yaml`):
  - 6/6 docs parse clean(0 failures)
  - 3,469 paragraphs total,217 headings(6.3% aggregate coverage)
  - 1,018 embedded images(872 unique SHA256 = ~14% same-doc dedup opportunity for F3 uploader)
  - 156 tables structured
  - 36.99 MB total image bytes
  - Level distribution {2: 41, 3: 24, 4: 152} consistent across 6 docs
- F1.e — `components/C01-ingestion.md` status `v0-draft → v1-active`(per CC-5);Open Items §8 同步更新 — R8/R10/F1 marked closed,新加 R7 DrawingML follow-up

**Pre-existing finding observed**:
- DrawingML elements(SmartArt / charts)warning logged by Docling — needs LibreOffice for extract,W2 baseline 暫不處理(per architecture R7 edge case);若 Gate 1 retrieval 顯示 SmartArt-rich pages 漏掉,W3+ 加 LibreOffice integration
- `raw_text` length aggregate ~95K chars across 6 docs(~24K tokens)= ~50 chunks at 500-token budget;比 plan §2 F2 estimated 2000-3000 chunks 細好多 ★ **F2 chunker design 需要決定 table cells 點 contribute to chunk count**(table cells 唔喺 raw_text;156 tables × ~10 rows = 可能 1500+ table-row chunks 如果按 row split)— W2 D2 chunker design 第一個 design call

### Decisions / OQ Resolved

- **Decision** — F1.c font-size heuristic re-scoped to verification(Docling visual layout heuristic adequate)。Rationale documented in W2 D1 progress(this entry)+ checklist F1 + C01-ingestion.md §8。Per F1 acceptance「OR」branch,non plan deviation(plan changelog 不需新 entry)
- **Decision** — F1 parser Protocol uses sync `parse()` method,non async。理由:parser 係 CPU/IO-bound(zipfile + XML),orchestrator 將會用 `asyncio.to_thread` wrap。CLAUDE.md §3.1「Async by default」strict rule 適用 FastAPI / httpx / Azure SDK,內部 CPU-bound 用 sync 較 simple
- **Decision** — `ParserResult` 用 `@dataclass(slots=True)` 而非 Pydantic BaseModel。理由:internal pipeline 中間型別,non API boundary;CLAUDE.md §3.1「Pydantic v2 for all schemas」suffix `(see backend/api/schemas/)` 指 API schemas;dataclass 更輕。`ChunkRecord`(F5 emit)會用 Pydantic
- **Decision** — `EmbeddedImage.position` / `Heading.anchor` 採用 ordinal string(`t{idx}` / `img{idx}` / `tbl{idx}`)而非 paragraph element ref。理由:F2 chunker 主要靠 document-order index 做 layout-aware chunk,ordinal 已 sufficient + stable per parse run
- **No OQ resolved this entry**(Q19 embedding dim 仍 W2 D3 decide)

### Blockers

- 🟡 **F2 chunker table cells handling**:Plan §2 F2 estimated 2000-3000 chunks 假設 table cells 入 chunks;parser raw_text 唔包 table cells。W2 D2 chunker design 第一決定 — 按 row chunk 定 per-table chunk 定 mix?需要 1 個 design call。Non blocking F1,but 影響 F2 acceptance 嘅 chunk count 預期
- 🟡 **R7 DrawingML / SmartArt edge case**:無 LibreOffice → 部分 chart / SmartArt 不 extract。W2 baseline 暫不處理;W3+ Gate 1 retrieval feedback 後決定。Non blocking F1
- ✅ R8 cleared / R10 cleared / F1 prerequisites all clear
- 🟡 R10/Q5/Q11/Q15-21 仍 unchanged(unrelated to F1)

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F1.a Ingestion skeleton + Parser Protocol | 1.0 | 0.6 | -0.4h | Clean Pydantic-style schema work |
| F1.b Docling docx_parser impl | 3.0 | 1.5 | -1.5h | Docling API surface clean,direct mapping;multi-sample probe drove faster design |
| F1.c Heading mitigation re-scope investigation | 2.0 | 0.4 | -1.6h | Saved by Docling baseline already adequate(verify-only) |
| F1.d Sanity script + run on 6 sample | 1.5 | 1.2 | -0.3h | Clean;Docling first cold-run ~30s/doc download model cache once |
| F1.e C01 status bump + open items refresh | 0.5 | 0.3 | -0.2h | Standard documentation |
| F1.f This entry + commit | 0 | 0.5 | +0.5h | Plan'd as part of D1 close |
| **Total D1** | **8.0** | **4.5** | **-3.5h** | F1.c re-scope + Docling API maturity drove most savings |

### Commits

| Hash | Subject |
|---|---|
| `f30f13a` | feat(c01): F1 Docling-based docx_parser PoC + 6-sample sanity report (W2 D1) |

---

## Day 2 — 2026-05-04 (Mon)

> Note:呢個 entry 喺 2026-05-03 Sun 晚 D1 完工後 same-session 完成 D2 work。D2 calendar date 仍 2026-05-04 per Option A shifted plan;但 implementation effort 喺 D1 evening 一氣呵成。

### Done

**F2 Layout-aware chunker delivered(F2.a–F2.g all closed)**:

- F2.a — `backend/pyproject.toml` hygiene update:
  - Added `docling>=2.0` + `tiktoken>=0.7` to direct dependencies(both 已 install via R8 mitigation;只係 declare to make explicit)
  - Added `ingestion*` to `[tool.setuptools.packages.find]` include list(F1 oversight fix:F1 commit 漏咗 register ingestion package for editable install)
- F2.b — `backend/ingestion/chunker/{__init__.py, base.py}`:
  - `ChunkSpec` dataclass intermediate type(F4 embedder + F5 orchestrator augment to emit final `ChunkRecord` per architecture.md §3.5)
  - Fields:`section_path` / `chunk_title` / `chunk_text` / `chunk_token_count` / `chunk_kind ('text'/'table')` / `chunk_index` / `low_value_flag` / `embedded_image_positions` / `heading_anchor`
  - `Chunker` Protocol contract(deterministic per input,`parse_failed=True` returns `[]`)
- F2.c — `backend/ingestion/chunker/layout_aware.py`:
  - Walks `ParserResult.paragraphs` + `tables` + `embedded_images` merged event stream sorted by `doc_order`
  - Heading-level stack maintained for `section_path` hierarchical traversal
  - Soft target 500 tokens / hard cap 1500 tokens(per architecture.md §3.3)
  - Tables = 1 chunk each(per architecture.md §3.3 「table 獨立 chunk」)+ section_path inheritance from current heading stack
  - Embedded images attached to open section accumulator by doc_order
  - `low_value_flag` heuristic:< 100 tokens(soft floor per spec)OR TOC pattern(en/ZH-Hant/JP)OR version/revision statement
  - tiktoken `cl100k_base` encoding(matches text-embedding-3-large)
- F2.d — `backend/ingestion/chunker/strategies.py`:
  - `select_chunker(doc_format, strategy)` returns Chunker instance
  - `auto` routing:docx/pdf → layout_aware,pptx → slide_based(W3 D1 scope,raises NotImplementedError until then)
  - `heading_aware` standalone strategy stub W3+(layout_aware already covers heading-bounded splitting for W2 baseline)
- F2.e — `scripts/run_chunker_sanity.py` + `reports/w02_d2_chunker_sanity.yaml`:
  - 6/6 docs chunked clean(0 failures)
  - **329 chunks total**(text=173,table=156)
  - low_value_rate 67.2%(221/329)— see Decisions §
  - Token dist:median=67,mean=102.8,p95=297,p99=536,max=813(全部 chunks 落 hard_cap 1500 內,**no chunks hit hard cap**)
  - section_path depth distribution:depth 1 = 14,depth 2 = 315(無 depth 3+,因為 6 sample doc 大多 H2 → H4 跳過 H3,leaf section 主要 H3 或 H4 直接接 H2 父)
  - Per-doc breakdown:0601(78)/ 0602(72)/ 0603(65)/ 0604(28)/ 0605(70)/ 0606(16)
- F2.f — `backend/tests/test_chunker.py` 12 tests all pass(synthetic ParserResult fixtures cover):
  - Three-section H2/H3/H3/H3 doc → 3 text chunks with correct section_path depth
  - Section < 100 tokens → low_value_flag=True
  - Section > target_tokens with multiple paragraphs → splits at paragraph boundaries respecting hard cap
  - Table → 1 chunk with chunk_kind='table' + section_path inheritance + pipe-delimited body format
  - Image at doc_order under section → recorded in `embedded_image_positions` as `img@{doc_order}`
  - parse_failed=True → empty chunk list
  - chunk_text format:title + "\n\n" + content per architecture.md §3.3
  - Strategy selector:auto+docx/pdf → layout_aware;auto+pptx → NotImplementedError;explicit `layout_aware` → LayoutAwareChunker
  - ChunkSpec has all fields F5 orchestrator needs to build ChunkRecord
  - Full test suite **20/20 pass**(8 API skeleton + 12 chunker)
- F2.g(this entry + commit)

**Parser refactor required by F2(side-effect of F1 design)**:
- F1 docx_parser.py originally emitted `raw_text + heading_tree + tables + images` — but `raw_text` lossy joined paragraphs lost heading-paragraph alignment
- F2 chunker needs to interleave tables/images with paragraph stream by document order
- **Solution**:Refactored `parsers/base.py` to emit `paragraphs: list[ParagraphItem]`(with `kind / heading_level / doc_order` per item)+ `tables` + `embedded_images`(each with `doc_order`)
- `ParserResult.raw_text` / `heading_tree` / `paragraphs_total` 變成 `@property` derivations(single source of truth)
- F1 sanity report re-run:still 217 headings / 1018 images / 156 tables;coverage adjusted from 6.3% → 8.9% because empty-text items 唔再算(non-meaningful paragraphs)— 更 meaningful denominator
- This is **F1 internal contract evolution within ingestion package boundary**,non plan deviation(non-public API,no consumer outside ingestion package as of W2 D2)

**Import path standardization**:
- Initial chunker code used `from backend.ingestion.<X>` — work for scripts(run from project root)but break test isinstance checks(test imports `from ingestion.<X>` so 2 different module objects loaded)
- Resolved:standardized chunker module imports to bare-prefix `from ingestion.<X>`(matches existing test convention `from api.server import app`,absolute import per ruff TID252)
- Scripts added sys.path bootstrap inserting `backend/` at front of `sys.path`(noqa E402 for post-bootstrap imports)
- All 20 tests pass + both sanity scripts work

### Decisions / OQ Resolved

- **Decision** — **Tables = 1 chunk per table**,non per-row。Architecture §3.3 explicitly mandates「table 獨立 chunk」。Plan §2 F2 estimate 2000-3000 chunks 隱含 per-row chunking,呢個 estimate **revised downward to ~300-500** for 6 docs(actual 329)。Non plan deviation:architecture spec authoritative per CLAUDE.md §13 "Spec wins"
- **Decision** — `low_value_flag` 用 architecture.md §3.3 spec 嘅 100-token soft floor(non checklist 提及嘅 50-token)。理由:spec wins(同 §13);Gate 1 retrieval 用 default filter `enabled eq true and low_value_flag eq false` 將排除 67.2% chunks ★ **W2 D5 F7 Gate 1 risk**:若 R@5 < 80% 因為 too few "valuable" chunks visible to retrieval,W3 retro 考慮:(a)lower threshold to 50-tokens,(b)disable filter for low_value_flag in retrieval baseline,(c)keep filter + augment short table chunks with surrounding section text。今日 W2 baseline 跟 spec
- **Decision** — `ChunkSpec` 用 `@dataclass(slots=True)` consistent with `ParagraphItem` / `Heading` / `EmbeddedImage` / `Table`。`ChunkRecord`(F5 emit boundary)會用 Pydantic
- **Decision** — Section path depth 平面化(全 doc depth ≤ 2)係文檔結構特性而非 chunker bug。6 sample 大多 H2→H4 跳過 H3 leaf,non bug
- **Decision** — Import path canonical:`from ingestion.<X>`(short prefix),consistent with existing tests + ruff TID252 satisfied;scripts use sys.path bootstrap
- **Decision** — `ParserResult` 結構演化(paragraphs 為 primary source)在 F1+F2 same-package boundary 內,non plan deviation。Internal contract evolution per Karpathy §1.3(F1 lossy raw_text 係 F2 之前嘅 design oversight,fix 係 surgical 而非 unrelated refactor)
- **No new OQ resolved**(Q19 embedding dim still W2 D3 decide)

### Blockers

- 🟡 **Gate 1 retrieval risk**(low_value 67.2% rate)— W2 D5 F7 verify if R@5 ≥ 80% achievable;若 fail,W3 retro adjust。Not blocking F3-F6 work
- 🟡 **R7 DrawingML / SmartArt edge case** — 無 LibreOffice → 部分 chart / SmartArt 不 extract。W2 baseline 暫不處理;同 W2 D1 carry-over,unchanged
- ✅ R8 cleared / R10 cleared / F1 + F2 prerequisites all clear
- 🟡 R10/Q5/Q11/Q15-21 unchanged(unrelated to F1/F2)

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F2.a pyproject hygiene | 0.2 | 0.2 | 0 | Clean |
| F2.b chunker base.py | 0.5 | 0.4 | -0.1h | Clean |
| F2.c layout_aware.py impl | 3.0 | 2.0 | -1.0h | Single-pass merged event stream design clean;Docling iterate_items API maturity helps |
| F2.d strategies.py | 0.5 | 0.3 | -0.2h | Minimal stub for W3+ |
| F2.e Sanity script + 6-sample run | 1.0 | 0.8 | -0.2h | Clean |
| F2.f Unit tests + import path debug | 1.0 | 1.5 | +0.5h | Surfaced + fixed dual-import isinstance issue;script bootstrap noqa需要 |
| F2.g This entry + commit | 0 | 0.5 | +0.5h | Plan'd as part of D2 close |
| Parser refactor(side-effect of F1 lossy raw_text)| 0(unplanned)| 0.7 | +0.7h | Required for F2 to interleave tables/images with text correctly |
| **Total D2** | **6.2** | **6.4** | **+0.2h** | Largely on-plan;parser refactor balanced by Docling API maturity savings |

### Commits

| Hash | Subject |
|---|---|
| `170e3db` | feat(c01): F2 layout-aware chunker + parser doc_order refactor (W2 D2) |

---

## Day 3 — 2026-05-05 (Tue)

_(同上)_

---

## Day 4 — 2026-05-06 (Wed)

_(同上)_

---

## Day 5 — 2026-05-07 (Thu)

_(同上 + retro draft 開始)_

---

## Retro(填於 W2 D5 末 / 2026-05-07)

### What worked
_(W2 D5 末 fill)_

### What didn't work / unexpected friction
_(W2 D5 末)_

### Surprises / discoveries
_(W2 D5 末)_

### Carry-overs to W03-chat-retrieval-citation
_(W2 D5 末)_

### ADR triggers
_(W2 D5 末)_

### Phase Gate result(per plan.md §3)
- **G1 Gate 1 R@5 ≥ 80%**:_(W2 D5 末 fill — pass/fail + value)_★ critical
- G2-G6:_(W2 D5 末)_

### Phase status
- Closeout commit:_(W2 D5 末)_
- Frontmatter status flipped to `closed`:_(W2 D5 末)_
- Phase W03 kickoff trigger:_(W2 D5 末)_

---

**End of W02 progress**(Day 0 prep stage,daily Day-N entries to follow W2 D1 onwards)
