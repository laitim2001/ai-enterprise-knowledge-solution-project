---
change_id: CH-011
title: "Per-image doc_order propagation + document-order 圖片排序/揀圖(platform P1 / Gap C)"
status: done               # draft | proposed | approved | active | done | cancelled
created: 2026-06-08
target_completion: 2026-06-09
affects_components: [C01, C03, C05, C10]
spec_refs:
  - architecture.md §3.6
  - architecture.md §3.7
  - architecture.md §4.5
  - ../../02-architecture/per-document-config-platform-design.md (P1 / Gap C)
adr_ref: ../../../adr/0048-per-image-doc-order-and-document-span-selection.md
---

# CH-011 — Per-image doc_order propagation + document-order 圖片排序/揀圖

> **Spec version**:1.0(initial)
> **Owner**:AI(實作)/ Chris(approve)
> **Approved by**:Chris(2026-06-08,ADR-0048 Accepted)
> **實作 platform roadmap**:`per-document-config-platform-design.md` **P1 / Gap C**(layer C 地基)

## 1. Context (Why)

2026-06-08 live(drive-images-1,GL03「process and confirm journal voucher transactions」)揭 chat 圖片第三問:**步驟圖順序錯亂**(用戶 Q3 — figure 3+ 唔照頁次)+ **完整性不足**(用戶 Q1 — 應 ~35 圖出唔齊)。

根因(已查證,詳見 ADR-0048):`ImageRef` **缺 per-image 文件位置欄位**,前端只按 `source_section` 排 → 同一 section 內(§3.1.3 全部步驟共用 section)排唔到頁次。位置資料(`doc_order`)**ingest 已有但 orchestrator 組 `ImageRef` 時掉咗**。

本變更係 per-document 配置平台 P1 / Gap C,接通 `doc_order` 鏈 + 改揀圖為 document-span。

## 2. Scope (What)

### 2.1 Behavior Change
- **Before**:圖片按 `source_section` lexical stable sort;同 section 內跌返後台 nearest-first 次序(非頁次);揀圖 nearest-first 聚埋 lead。
- **After**:圖片按 per-image **真文件位置 `doc_order`** 排序(section 內外都照頁次);揀圖 document-span 鋪開覆蓋程序頭→尾。

### 2.2 In Scope
**C-1 位置 primitive(解 Q3,需 re-index)**:
- `ImageRef.doc_order: int = 0`(`backend/api/schemas/query.py`)
- orchestrator 由 `"img@<N>"` key stamp `ImageRef.doc_order`(`backend/ingestion/orchestrator.py`)
- `embedded_images_json` 序列化帶 `doc_order`(C03 indexing 寫入側)
- `parse_embedded_images` 讀 `doc_order`(`backend/generation/citation_enrichment.py`)
- frontend `dedupeCitationImages` 排序改 `doc_order` 主鍵 + `source_section` fallback/tiebreak(`frontend/lib/chat/citation-images.ts`)
- re-index drive-images-1

**C-2 document-span 揀圖(改善 Q1)**:
- `_find_section_neighbour_images` cap 選擇由 nearest-first 改 document-order span(`backend/generation/citation_image_neighbors.py`)
- verify 時調大 drive-images-1 per-KB `max_images_per_answer`(config,非 code)

### 2.3 Out of Scope(explicit)
- **per-DOCUMENT config cap 粒度** → P2 / layer A(per-document profile),本期不做
- **query 意圖 gate** → P3 / layer B
- **全域 default flip** / 改 `default_rerank_k` / retrieval 核心
- **image embedding 揀圖**(H4 Tier 2 禁)
- CH-010 pin 重構(pin 仍 attach 概覽;排頭改由 doc_order 接手,但不強制重寫 pin code)

## 3. Acceptance Criteria

- [ ] **AC1**:`ImageRef` 有 `doc_order: int`(default 0);orchestrator 由 `img@<N>` stamp;序列化入 `embedded_images_json`
- [ ] **AC2**:`parse_embedded_images` 讀返 `doc_order`(unit test 覆蓋有/無 key)
- [ ] **AC3**:frontend `dedupeCitationImages` 按 `doc_order` 排(真文件位置主鍵);doc_order 全 0 → 退回 `source_section`(production-preserve;vitest 覆蓋)
- [ ] **AC4**:`_find_section_neighbour_images` 改 document-span 選擇;pytest 覆蓋(原 nearest-first test 改 / 新 document-order test)
- [ ] **AC5**:re-index drive-images-1 後,live chat GL03 query → §3.1.3 步驟圖照 Word 頁次(step1 page21 → import page24 …)render(Q3 解);概覽仍 lead;coverage 改善(Q1)
- [ ] **AC6**:跨文件 30-query eval — recall / faithfulness flat + p95 latency 增幅記錄(regression guard;對照 memory `project_chat_demo_rag_quality_followups`)
- [ ] **AC7**:production-preserve — 未 re-index KB(doc_order 全 0)行為 bit-identical;backend pytest + frontend vitest 全綠;ruff / mypy --strict 改檔 0 新 error
- [ ] **AC8**:H4(無 image embedding)· H7(gallery 仍對齊 mockup,reverse-drift fix)· 驗證指令:`backend\.venv\Scripts\python.exe -m pytest backend/tests/ -k "image or citation or neighbour"` + `pnpm vitest run citation-images`

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | re-index 成本 + Free-tier semantic 402 | High | Med | `HYBRID_USE_SEMANTIC_RANKER=false` 繞;azurite native Plan B |
| R2 | `doc_order` 非全文件單調(parser 假設不成立)| Low | High | verify:抽查 GL03 chunk 的 `img@<N>` N 值單調遞增 |
| R3 | 完整性上限仍受 cap(35 出唔齊)| Med | Med | verify 調大 per-KB cap;full 控制 set 期望 = P2 |
| R4 | re-index 令 chunk_index 變(現有 citation 失效)| Low | Med | re-index 係整 KB 重建,citation 即時重生,無 stale ref |

## 5. Effort Estimate

~1–1.5 day(C-1 半日 + C-2 數小時 + re-index + 30-query eval 半日)。

## 6. Dependencies

- **ADR-0048 Accept(H1 gate)** — code 之前必須
- Runtime:backend `backend\.venv\Scripts\python.exe`(truststore);mock auth `Bearer dev-token`;`HYBRID_USE_SEMANTIC_RANKER=false`;azurite native;pre-flight Langfuse 200 + PG SELECT 1

## 7. Spec Changelog(deviation log)

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-08 | Initial draft(P1 / Gap C kickoff)| 用戶「先執行 P1」 | Chris(pending)|

---

**Lifecycle reminder**:spec locked after status=approved。重大 deviation → §7 changelog。
