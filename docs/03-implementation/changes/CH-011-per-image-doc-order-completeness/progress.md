---
change_id: CH-011
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed     # in-progress | closed
---

# CH-011 — Progress

> Day-N entries + closeout。每 commit 對應一個 Day-N mention(R2)。
> 實作 platform roadmap **P1 / Gap C**(per-document config platform 地基層)。

---

## Day 1 — 2026-06-08

### Done
- 寫 per-document 配置平台完整 design spec(`docs/02-architecture/per-document-config-platform-design.md`)— as-built map(平台 W43-W51 已建一大半)+ 3 gap 分析(A per-doc 粒度 / B 意圖 gate / C per-image 位置)+ phasing roadmap(C→A→B)
- 用戶選「先執行 P1(Gap C)」→ kickoff CH-011 pre-doc + ADR-0048 → **Chris Accept**
- 查證根因:`ImageRef` 缺 doc_order;`doc_order` ingest 已有(`EmbeddedImage.doc_order` + orchestrator `"img@<N>"` key)但組 `ImageRef` 時掉咗;`parse_embedded_images` + frontend 排序都唔用位置 → section 內排唔到
- **C-1 落實**:`doc_order` 加兩個 ImageRef(query + indexing schema)+ orchestrator stamp + parse 讀 + frontend `(doc_order 主鍵, section fallback)` 排序 + TS type;`to_search_doc` 序列化零改動(model_dump 自動帶,round-trip test 驗)
- **C-2 落實**:`_find_section_neighbour_images` nearest-first → document-order(chunk_index ascending)
- **測試**:backend 53(targeted)+ 完整 suite **1262 passed / 25 skipped / 1 pre-existing fail**;frontend vitest 28 + type-check exit 0;ruff format 全過;mypy --strict 改檔 0 新 error

### Decisions
- 分類 **Change CH-011**(同 CH-009/CH-010 chat 圖片質素線一致;schema + re-index 同 CH-009 dims precedent)
- **ADR-0048 Accepted**(Chris 2026-06-08):per-image doc_order primitive(C-1,需 re-index)+ document-order 揀圖(C-2);ingest-time stamp + re-index(rej query-time stamp:較 invasive);H4 只用 doc_order/section/文字信號;H7 屬 reverse-drift fix 例外
- frontend 排序 mode **一次性決定**(`allHaveDocOrder = out.every(...)`)而非 per-pair → 保 comparator transitive + production-preserve(全 0 legacy → section sort bit-identical)
- per-DOC config cap 粒度明確留 P2(layer A);本期守 Karpathy §1.2 唔提前做
- 仍喺 `feat/chat-image-relevance-ch009`(CH-010 未 merge,同 feature 線)

### Findings(透明記錄,per R3 + §1.3)
- 🔴 **`citation-images.ts` null-byte corruption 修復**:Grep 偵測到 2 個 null byte(offset 5686/5750)喺 `imageSectionPath(...).join('\0')` —— `join(' ')` 嘅空格(0x20)被損壞成 null(0x00),committed 入 CH-009。因分隔符只用於內部 lexical 比較(從不顯示)故行為無差、vitest 照過 = silent corruption。byte-level 還原 2 bytes 為 space(我正要改嗰 block,in-scope)。**建議**:其他 source file 值得掃 null byte(可能同源)。
- ⚠️ **pre-existing 失敗 test(非我)**:`test_synthesizer.py::test_synthesize_invokes_engine_fetch_expansion_when_engine_and_kb_id_provided` —— `citation_expansion.py` section-aware 擴展用 section_path-less mock chunks,depth=1 配唔到 → 0 neighbours。`git stash` 我全部改動後喺 HEAD code 同樣 FAIL → 證實 pre-existing,非 CH-011 引起(我冇 touch citation_expansion.py)。屬另一修(out of CH-011 scope)。
- ⚠️ **pre-existing ruff 保留**:`citation_image_neighbors.py:83` B905 zip(CH-010 已記錄)+ `test_citation_image_neighbors.py:18` I001 import block(git diff 確認非我改動)→ surgical 保留。
- ℹ️ `ruff format` normalize 咗 `test_citation_image_neighbors.py` 3 處 pre-existing trailing-comma 格式(L233/260/336,我冇 touch 嘅 test)— canonical formatter side-effect,formatting-only。

### Execution(live,2026-06-08)
- Commit `0283e3e`(feat code+tests)+ docs commit;working tree 淨剩 session-start.md(永不 commit)+ live-*.png(scratch)
- Backend 殺 dual-process(venv parent 42616 + system child 41360)→ venv python 重啟(`HYBRID_USE_SEMANTIC_RANKER=false`);/health 全 component OK
- **Re-index drive-images-1:6/6 reindexed,0 skipped(sources 齊),0 failed,369 chunks** → `doc_order` 入 index
- Backend /query GL03 驗:lead citation 20 圖 doc_order **259→265→269→…→357 嚴格遞增**;概覽(259/265)行頭,§3.1.3 步驟照頁次 → **Q3 backend 層證實解決**(視覺待用戶 UI 驗 V2)
- **Q1 完整性 cap 決定**:用戶選**保持 cap=20**(C2.2);順序為本期重點,完整性 ~35 留 P2

### Blockers
- 無(V1 re-index 已完成,sources 齊)

### Effort
- Planned:1–1.5 day;Actual(Day1 文檔 + code + test):~3h;Variance:—

### Commits
| Hash | Subject |
|---|---|
| `0283e3e` | feat(generation): CH-011 per-image doc_order + document-order image sort/select |
| _(this docs commit)_ | docs(adr): per-document config platform design + ADR-0048 + CH-011 kickoff |

---

## Closeout（2026-06-08，status=closed）

### Acceptance verification
- **AC1** ✅ `ImageRef.doc_order` 兩個 schema + orchestrator stamp（`img@<N>`）+ `to_search_doc` 自動序列化（round-trip test）
- **AC2** ✅ `parse_embedded_images` 讀 doc_order（有/無 key + storage→query round-trip test）
- **AC3** ✅ frontend `dedupeCitationImages` doc_order 主鍵排序 + 缺失 fallback（vitest 28）
- **AC4** ✅ `_find_section_neighbour_images` document-order（chunk_index ascending）+ pytest
- **AC5** ✅（backend 層）GL03 /query lead citation doc_order 259→357 嚴格升序、概覽 lead；🚧 **UI 視覺確認待用戶（V2）**
- **AC6** 🚧 **deferred** — eval CLI pre-existing 壞（kb_id）+ text RAGAs 對圖片-only N/A（見 checklist V3 + task `task_ecd4f8bd`）
- **AC7** ✅ production-preserve（vitest fallback）+ backend suite 1262 pass（1 pre-existing 非我）+ ruff/format/mypy 改檔 0 新 error
- **AC8** ✅ H4（無 image embedding）+ H7（reverse-drift fix）

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| 1（design spec + ADR + code + test + restart + re-index + closeout）| 8–12 | ~5 | −3 |

### Lessons
- **doc_order 一直喺手**：解 Q3 嘅 primitive（`EmbeddedImage.doc_order`）ingest 早就有,只係 orchestrator 砌 `ImageRef` 時用完即棄 → 接通一段就解,零新 extraction。先查清 as-built 避免重造（Karpathy §1.1）。
- **平台 as-built > memory**：per-doc config 平台 vision memory（2 日前）已過時 —— 全 pipeline 試跑 loop W43-W51 已建。design spec 階段查證救返避免重做整個平台。
- **null-byte silent corruption**：`citation-images.ts` `join(' ')` 空格被損壞成 `\0`（committed 入 CH-009）—— 只用於內部比較故 vitest 一直照過。Grep binary-match 揭發。教訓:exact-match Edit 失敗 + Grep 報 binary → 查 raw bytes,勿盲 rewrite。
- **text RAGAs ≠ 圖片 regression 工具**:image-ordering 改動唔應該用 text eval 把關;real guard = backend doc_order 升序驗 + vitest production-preserve + re-index 0-failed。
- **Carry-overs**:V2（用戶 UI 驗）/ V3+AC6（eval harness 修 + 跑,task `task_ecd4f8bd`）/ pre-existing synthesizer test（task `task_b05602ed`）。

### Component design note status updates
- 🚧 deferred（X3）— doc_order 屬既有 ImageRef pipeline 增量,未起獨立 design note bump（非阻塞）

---

**End of CH-011 progress**
