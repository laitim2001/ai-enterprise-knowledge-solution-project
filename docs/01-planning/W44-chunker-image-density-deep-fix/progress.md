# W44 — Chunker Image-Density Deep Fix · Progress

> Daily progress + decisions + commits;結尾 retro。

---

## Day 0 — 2026-06-03(kickoff,F0 gate pending)

### 做咗乜
- **三方 roadmap audit 收斂**(本 session)→ 用戶 pick (a) 開 W44 深度優先。
- **根因 live-verify**:Read `layout_aware.py` 全文,確認圖洪 ingestion 根因 = 圖按 section accumulator pile-on,text flush(`:207` hard-cap / `:213-218` soft-target)**唔 reset** `image_positions`,`_build_text_chunk:248` copy 全部 + `_merge_adjacent_shorts:323` concat → 圖密短 section 單 chunk carry 全部圖(實測 `ci=15=57`,memory #7)。全 file 零 per-chunk 圖數 cap。
- **doc-level reindex 非 stub** 確認(`documents.py:786-884`,真刪 + `_run_ingest_pipeline`)→ W44 驗證唔卡 Track A([AUDIT-B])。
- **ADR-0041 draft 建立**(Status: Proposed)+ ADR README index 更新(0041 row + next=0042)。
- **W44 plan / checklist / progress 建立**(R1 plan-before-implement)。

### 決定
- 切法 recommended = **A(image-aware flush + `max_images_per_chunk` soft cap)**,Alternatives B(sub-heading)/ C(image-anchored)/ D(hybrid)/ runtime-cap-only(W43 已做,不足)記 ADR-0041。**最終切法 + cap default 待 F0 gate Chris 拍板(決策 2)**。
- **F1+ code GATED on F0 gate**(H1 per §5.1 — chunker §3.3 change + re-index)。本日只 docs housekeeping。

### F0 gate — PASS 2026-06-03
Chris(AskUserQuestion)揀 **切法 D(混合:sub-heading 細分 + image cap 兜底)** + `max_images_per_chunk` default **8**(對齊前端 `INLINE_IMAGE_CAP=8`)+ approve H1 + ADR-0041 Proposed→Accepted。F1 code gate open。
- 切法 D 實際 scope(Karpathy §1.1 surface):heading 細分**已由現有 chunker 處理**,W44 重心 = image pile-on 修 + `_should_merge` image-guard + cap force-split;**唔重寫 heading 邏輯**(避免 over-build)。
- ⚠️ cap default 8 ≠ ADR-0037/0040 OFF-default,但對正常文件 no-op、只 cap flood、且 re-index 後先生效(影響面限圖密 chunk,intentional)。

### Blockers / carry-over
- Top risk(R6 已記 plan §4):重切改變所有 chunk 邊界 → eval no-regression gate(G3/G4)必過。

### Commits
- `e5d8830` docs(planning): W44 kickoff — ADR-0041 draft + phase artifacts(F0.1)
- `c219dfa` docs(adr): W44 F0 gate PASS — ADR-0041 Accepted(切法 D + cap 8)

---

## Day 1 — 2026-06-03(F1 + F2 — chunker 切法 D code + test)

### 做咗乜
- **F1 chunker 切法 D**(`layout_aware.py`):① `_reset_images_on_flush`(text flush 按 doc_order 分配圖,修 `:207` pile-on 根因)② `_force_flush_images`(image cap 8 force-split,延續 section_path)③ `_should_merge` image-count guard(防 ADR-0033 merge re-pile)④ `_flush_text_section` residual-image guard(force-split 後殘圖唔丟)。全部 gated on `max_images_per_chunk is not None` → cap=None 完全 bit-identical(pre-W44 pile-on)。
- **Settings**:`chunker_max_images_per_chunk: int | None = 8`;`server.py:99` startup 傳落 injected chunker(override seam)。
- **F2 test**(`test_chunker.py` +6):force-split / no-image-loss / cap=None pile-on / merge image-guard / residual flush / under-cap no-op。

### 驗證
- **pytest 30 passed**(6 新切法 D + 24 既有 regression 全綠 — ADR-0033 merge + BUG-017 image isolation 零 regression)。
- **ruff**:我新增 code clean(`layout_aware` reformatted)。`server.py` E402 ×30(truststore import pattern)+ `test_chunker` `import pytest` F401 = **pre-existing 非本次引入**(git diff 證 server 只改 line 99;test 純 append + 0 `pytest.` 用法),按 Karpathy §1.3 不刪。
- **mypy --strict**:我新增 method/field clean;17 pre-existing errors(parsers docling stub + `layout_aware` 既有 `object→ParagraphItem/Table` assign)非本次引入。

### Blockers / 下一步
- **F3 re-index + F4 eval 待做** — 需 backend venv restart 載新 chunker code(`python -m api.server` 無 reload)+ doc-level reindex 圖密文件 + eval no-regression(G3/G4)。涉及 stateful + eval ~18min。
- ⚠️ 重切 risk(R6):chunker 改變所有 chunk 邊界 → G3/G4 必過先算 PASS。

### Commits
- `8145656` feat(ingestion): W44 F1+F2 chunker image-density deep fix(切法 D)
- `64b78f6` docs(planning): roadmap A-E audit calibration(順手 commit,另一 session work)

---

## Day 1 cont — F3 re-index G1/G2 PASS

- **pre-flight** ✅ Langfuse 200 / Postgres SELECT 1 / backend venv restart(kill PID 18552 venv + 43128 system-python dual-process → venv cold start ready ~100s,全 component ok,新 chunker 載入)。
- **F3 reindex** AR `test-kb-20260531-v1`(doc `drive-user-manual-0601-ar-fna-ar-management-v0-03`)via doc-level reindex(`documents.py` real pipeline,[AUDIT-B] 證唔卡 Track A):68→**90 chunks**(force-split +22),223 img uploaded / 30 deduped。
- **G1 PASS**:max per-chunk 圖數 **57 → 8**(diag `_w44diag_imgcount.py` 讀 index)。
- **G2 PASS**:分佈 baseline 多 mega(57/27/25/23/18/16/14/12/12/11)→ 重切後 0 個 >8、22 chunks at cap 8、dist 集中 ≤8;223 unique 全保留(per-chunk 總和 252 ≥ 223,無丟失;278→252 = pile-on cross-chunk dup 亦消除)。
- **下一步 F4**:reindex `drive_user_manuals`(含 AR + 5 模組)→ `/eval/run` 30q no-regression(G3 R@5 / G4 RAGAs)對比 W43 baseline(recall 1.0/faith 0.9956/corr 0.8489/0 attention)。throwaway diag script `_w44diag_imgcount.py` F4 後刪。
