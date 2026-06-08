---
change_id: CH-011
spec_ref: ./spec.md
adr_ref: ../../../adr/0048-per-image-doc-order-and-document-span-selection.md
status: in-progress     # in-progress | done
last_updated: 2026-06-08
---

# CH-011 — Checklist

> Atomic items derived from `spec.md §3`。done → `→[x]`;未做標 🚧 + 理由(per CLAUDE.md sacred rule)。
> **Code/re-index GATED on ADR-0048 Accept(H1)。**

## Pre-gate
- [x] P0 — design spec(`per-document-config-platform-design.md` P1)+ CH-011 spec + ADR-0048 Proposed + README index
- [x] P1 — **ADR-0048 Proposed → Accepted(Chris 2026-06-08)**

## C-1 — 位置 primitive(解 Q3)
- [x] C1.1 — `ImageRef.doc_order: int = 0`(**兩個** ImageRef:`backend/api/schemas/query.py` + `backend/indexing/schemas.py`)
- [x] C1.2 — orchestrator 由 `"img@<N>"` key stamp `ImageRef.doc_order`(`backend/ingestion/orchestrator.py`;defensive parse,malformed → 0)
- [x] C1.3 — `embedded_images_json` 序列化帶 `doc_order`:**零改動** — `ChunkRecord.to_search_doc` 嘅 `model_dump(mode="json")` 自動帶新 field(round-trip test 驗證)
- [x] C1.4 — `parse_embedded_images` 讀 `doc_order`(`backend/generation/citation_enrichment.py`;absent → 0)
- [x] C1.5 — frontend `dedupeCitationImages` 排序 `doc_order` 主鍵 + `source_section` fallback(`frontend/lib/chat/citation-images.ts`;mode 一次性決定保 transitive)+ `ImageRef` TS type 加 `doc_order?`(`lib/api/query.ts`)

## C-2 — document-span 揀圖(改善 Q1)
- [x] C2.1 — `_find_section_neighbour_images` cap 選擇 nearest-first → document-order(chunk_index ascending)(`citation_image_neighbors.py`)
- [x] C2.2 — **用戶決定保持 cap=20**(2026-06-08):順序(Q3)修復為本期重點;完整性(Q1 ~35)維持 cap,超額入 Image Library;full per-doc 完整性控制留 P2(layer A)。drive-images-1 config 不變(max_images_per_answer=20 / neighbour max_aux=18)

## Tests
- [x] T1 — `parse_embedded_images` doc_order unit test(有/無 key + storage→query round-trip)(AC2)
- [x] T2 — frontend vitest:doc_order 排序 + 跨 section + doc_order 缺失 fallback(28 passed)(AC3)
- [x] T3 — `_find_section_neighbour_images` document-order pytest(rename caps test + lead 放中間 discriminate)(AC4)
- [x] T4 — backend pytest **1262 passed + 25 skipped + 1 pre-existing fail(非我 — 見 progress)**;frontend vitest 28 + type-check exit 0;ruff 我 code 乾淨(B905 L83 + I001 import 皆 pre-existing 保留);ruff format 全過;mypy --strict 改檔 0 新 error(AC7)

## Verify
- [x] V-restart — backend 殺 dual-process(42616+41360)→ venv python 重啟載新 code(`HYBRID_USE_SEMANTIC_RANKER=false`);/health 全 component OK;frontend :3001 alive
- [x] V1 — re-index drive-images-1 **6/6 reindexed,0 skipped(sources 齊),0 failed,369 chunks**;pre-flight Langfuse 200 + PG 1 row + azurite 10000 ✓
- [ ] V2 — **live chat GL03 query**:§3.1.3 步驟圖照 Word 頁次 render(Q3 解)+ 概覽 lead(AC5)— **用戶驗**(backend /query 已證 doc_order 升序;待 UI 視覺確認)
- [ ] 🚧 V3 — 跨文件 30-query eval(AC6):**deferred(用戶決定 2026-06-08)**。理由:① eval CLI `scripts/run_ragas_eval.py:136` **pre-existing 壞**(`engine.retrieve()` missing `kb_id`,stale 自 ADR-0018 multi-KB wiring,非 CH-011)② text RAGAs(4 metric 全 text-based)**對圖片-only 改動 N/A** —— CLI 唔行圖片 attach/sort 路徑,且 re-index 用相同 embedding 邏輯 → text retrieval bit-identical,metric 必然 flat。real regression 證據已齊(V1 6/6 / V4 production-preserve / V5 doc_order 升序 / 完整 suite 1262 pass)。開 task `task_ecd4f8bd` 修 harness
- [x] V4 — production-preserve:frontend `allHaveDocOrder` mode 一次性決定 → 未 re-index KB(doc_order=0)退回 section sort,既有 vitest(唔 set doc_order)全綠驗證 bit-identical(AC7)
- [x] V5 — doc_order 單調性確認:GL03 /query lead citation 圖 doc_order=259,265,269,275,…,357 **嚴格遞增**(R2)

## Cross-Cutting
- [x] X1 — 每 commit 對應 `progress.md` Day-N(R2)+ component tag(`0283e3e` feat / docs commit / `0b29c1b` housekeeping）
- [x] X2 — ADR-0048 Accepted + README index(R5)
- [ ] 🚧 X3 — components `C01/C03/C05/C10-*.md` design note bump:**deferred** — doc_order propagation 屬既有 ImageRef pipeline 增量,未起獨立 design note；如後續整合落 component 文件再 bump（CC-5,非阻塞）
- [x] X4 — `progress.md` closeout summary + status flip `closed`

---

**Lifecycle reminder**:checklist 隨 spec §3 acceptance criteria 衍生。新 item 先入 spec + changelog 再加。
