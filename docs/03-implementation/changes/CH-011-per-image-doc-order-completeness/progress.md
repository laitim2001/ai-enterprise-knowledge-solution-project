---
change_id: CH-011
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
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

## Closeout(填於 status=closed)

### Acceptance verification
_(待)_

### Effort summary
_(待)_

### Lessons
_(待)_

---

**End of CH-011 progress**
