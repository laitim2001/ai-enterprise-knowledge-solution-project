---
bug_id: BUG-026
title: "Chat answer renders the SAME embedded image multiple times (no cross-citation dedup) + per-image labels fall back to citing-chunk section when figure caption absent"
severity: Sev3
status: investigating
reported: 2026-05-30
reporter: "Chris(W42 post-closeout UI demo session 2026-05-29/30 — real chat UI 對 KB `dce-integration-demo-1` 測試,見到同一張圖重覆出現 + 圖片標題唔對應實際圖內容)"
affects_components: [C10, C01]    # C10 Chat Interface UI(primary render bug)+ C01 Ingestion(Finding C per-image caption depth)
spec_refs:
  - architecture.md §4.5     # Citation schema(embedded_images list)
  - architecture.md §3.5     # ChunkRecord embedded_images attribution
  - CLAUDE.md §5.7           # H7 design fidelity(mockup ekp-page-chat.jsx 為 canonical)
related: [BUG-017, BUG-019, BUG-020, BUG-021, BUG-024, BUG-025]
---

# BUG-026 — Chat 重覆圖片(跨 citation 無 dedup)+ per-image label 深度

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged Sev3(presentation-layer,no data loss / security;對齊 PROCESS.md §4.5 「Citation render misaligned」Sev3 範例)— 待 Chris chat-confirm

## 1. Symptom

W42 收尾後 UI demo session,user 喺真實 chat UI(`/chat`)對 KB `dce-integration-demo-1`(`DCE_Integration_Platform_Implementation_Plan.docx`,8 嵌入圖)問「show me all the Integration scenarios」,answer 下方:

1. **同一張圖重覆出現**:某張 §8.x 圖喺 inline image cards + 「Referenced screenshots」gallery 入面出現 2 次以上(user 報「8.5 figure duplicated」)。一份得 8 張圖嘅文件,response 攤出 11 張(含重覆)。
2. **圖片標題唔對應實際圖內容**:圖片 caption / 標題顯示嘅係**引用該圖嘅 chunk 嘅 section**,唔係圖本身嘅內容(user 報「figures mislabeled」+「8.4 figure missing」)。同一個 chunk 帶多張圖時,全部 label 成嗰個 chunk 嘅 section。

## 2. Reproduction Steps

1. Ingest 一份多 section、每 section 帶嵌入圖嘅 DOCX(`extract_embedded_images=True`),令 `attach_neighbour_images`(W25 F5 D1 / ADR-0034)會把鄰近 chunk 嘅圖 attach 落 intro/meta chunk
2. Chat 問一條會引用 §X intro chunk + §X.1/§X.2 子 chunk 嘅 query(例「show me all the Integration scenarios」→ 引用 §8 intro + §8.1-§8.5）
3. 觀察 answer 下方 inline image cards + 「Referenced screenshots」gallery
4. **Expected**:每張**獨特**圖(by `checksum_sha256`)只出現一次;每張圖標題反映該圖內容
5. **Actual**:
   - 同一張圖(同 `checksum_sha256`)出現多次 —— 因為佢同時係 §8.1 chunk 嘅 direct image **又** 係 §8 intro chunk 嘅 neighbour-attached image,兩個 citation 都帶住佢
   - 圖標題 = 引用 chunk 嘅 `chunk_title` / `section_path`(無 figure caption 時)

**Reproduction reliability**:Always(deterministic — 只要 neighbour-attach 令同一 checksum 圖落入 ≥2 個 cited citation)

**Environment**:local dev(frontend `:3001` mock auth + backend `:8000`),W42 demo KB `dce-integration-demo-1`(已喺 demo 後清理刪除)

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| Inline image cards | 每張獨特圖一張卡 | `imageCitations.flatMap(c => c.embedded_images.map(...))` 攤平所有 (citation, image) pair,**無跨 citation dedup** → 同 checksum 圖多張卡(`page.tsx:1228-1245`)|
| Image gallery thumbnails | 每張獨特圖一個 thumbnail | `citations.map(c => c.embedded_images[0])` 每 citation 一個 thumbnail,兩個 citation 共用同一 first image → 兩個相同 thumbnail(`page.tsx:1796-1797`)|
| 圖片標題(label)| 反映圖內容 | InlineImageCard `title = image.alt_text \|\| chunk_title`;無 caption 時 fallback 落 citing chunk section,同 chunk 多圖 → 同 label |

## 4. Impact

- **Affected users / scenarios**:每條 chat query 引用到 image-bearing intro/meta chunk + 其鄰近子 chunk 時(Drive corpus 全部 docx 含圖,常見)
- **Workaround available?**:No(presentation 層,user 無法繞過)
- **Data loss / corruption?**:No —— backend citation↔image 資料模型正確(每 citation 合法引用其圖),只係 display 層無 dedup
- **Security implication?**:No
- **Cost implication?**:None directly

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5` —— 對齊範例「Citation render misaligned」。Presentation-layer degradation:重覆圖 + label 不準影響 chat answer 觀感同 stakeholder 對成熟度判斷,但**唔涉資料完整性 / 安全 / 功能阻斷**(citation 資料本身正確,圖可正常開)。低於 BUG-017 Sev2(嗰個係 ingest-time chunk↔section data 損壞)。Postmortem 非強制(Sev3),pattern recurring 先寫。

## 6. Initial Diagnosis(root cause confirmed via code trace 2026-05-30)

3 個 finding,**唔同層 + 唔同處理**:

### Finding A —— 跨 citation 重覆圖(= user 講嘅「dedup」)【真 bug → 修】

`backend/generation/citation_image_neighbors.py::attach_neighbour_images`(W25 F5 D1 / ADR-0034)把鄰近 chunk(`chunk_index ±window`)嘅圖 attach 落每個 citation,**只喺單一 citation 內部** dedup（`_find_neighbour_images` 用 `own_checksums` set 對自己 dedup),**跨 citation 唔 dedup**。結果:

- §8.1 chunk 嘅 figure = §8.1 citation 嘅 direct image **又** 被 attach 做 §8 intro citation 嘅 neighbour image
- 同一 `checksum_sha256` 出現喺 2 個 citation 嘅 `embedded_images`

Frontend 渲染兩處都無跨 citation dedup:
- **Inline cards**(`frontend/app/(app)/chat/page.tsx:1228-1245`):`imageCitations.flatMap((c) => c.embedded_images.map(...))` 攤平所有 pair render
- **Gallery**(`page.tsx:1796`):`citations.map((c) => c.embedded_images[0])` 每 citation 一 thumbnail

**Mockup(`references/design-mockups/ekp-page-chat.jsx:621-664`)從不顯示重覆圖** —— synthetic data 每 citation 一張獨特圖。所以 **dedup = 把 implementation 更貼近 mockup(reverse-direction drift fix),非 H7 deviation**(per CLAUDE.md §5.7「修正 visual drift bug」唔屬 H7 trigger）。

**Fix shape**:frontend 抽一個 pure helper `dedupeCitationImages(citations)` → 回傳 `{ citation, image }[]`,以 `checksum_sha256`(fallback `blob_url`)為 key,每張獨特圖 attribute 落**首次出現**嘅 citation(citation order)。Inline cards + gallery + image count 全部由佢 drive。

### Finding B —— Gallery label 用 `chunk_title`【= mockup-faithful,不動】

Gallery thumbnail label = `c.chunk_title` + `c.doc_title`(`page.tsx:1869, 1880`)。睇落似「label 唔啱」,但 **mockup `ekp-page-chat.jsx:653-656` 本來就係 `c.chunk_title` + `c.doc_title`**（source attribution 設計,thumbnail 標「呢張圖嚟自邊個 chunk / doc」,唔係圖 caption)。

→ **改成 `image.alt_text` 會 violate H7**(偏離 mockup 設計意圖)。預設**保持不動**;若要改成顯示真 caption = mockup deviation,須 H7 STOP+ask + 可能 ADR-route。

### Finding C —— Per-image 真 caption / 無 caption fallback【ingest 層深度 → 待決策】

InlineImageCard `title = image.alt_text || citation.chunk_title`(`page.tsx:1660`)。`alt_text` = ingest 時 Docling caption(`backend/ingestion/parsers/docx_parser.py:117` `item.caption_text(doc)`)。

- 圖**有** DOCX caption(如「Figure 1: High-level integration architecture」,BUG-017 已證此 doc 有)→ `alt_text` 已正確,inline card title 顯示真 caption ✅
- 圖**無** caption → `alt_text=""` → fallback 落 `chunk_title`(citing chunk section)→ 同 chunk 多圖全部同 label（user 見到「3 figures all tagged 8.4 Scenario D」）

另外,neighbour-attached 圖嘅 inline caption 行 = `Citation [N] · {citing chunk section_path}` —— 把 §8.1 圖 attribute 落 §8 intro citation 嘅 section,而非圖本身 section。

**真 fix = ingest-time per-image section / caption 偵測**(每張圖實際屬邊個 §X.x)—— 較大 ingest 層工作,overlap 已 done 嘅 **BUG-017**(嗰個修 chunk↔section 跨邊界 merge mis-attribution),且需 **re-ingest** + **live 驗證 `alt_text` 實際內容**(目前 demo KB 已清理刪除,blobs 已無,無法即時驗)。

→ **需 user 決策**:(a) 先驗證 alt_text 實際內容再決定是否需要 ingest 工作;(b) 接受 mockup-faithful 現狀(gallery chunk_title + inline alt_text-或-fallback),只修 dedup;(c) 排期 ingest per-image caption 為獨立較大 task。

## 7. Acceptance for Fix(checklist preview)

**Finding A(dedup,本 bug 主修)**:
- [ ] Root cause 已 code-trace 確認(`attach_neighbour_images` 跨 citation 無 dedup + frontend 兩處 flat render)
- [ ] **Fix** —— frontend pure helper `dedupeCitationImages(citations)`(key `checksum_sha256` fallback `blob_url`,attribute 落首現 citation)
- [ ] **Fix** —— `chat/page.tsx` inline cards + gallery + image count 改由 deduped 列表 drive
- [ ] **Test** —— Vitest unit test 證 helper 把同 checksum 跨 citation 圖只保留一次(fails before / passes after)
- [ ] Verify gates —— `npm run lint` + Vitest 綠 + `npm run build`
- [ ] Manual UI verify(user reload `/chat` 同一 query → 每張獨特圖一次)—— 需 demo KB 重新 ingest

**Finding B**:no-op(mockup-faithful,documented)

**Finding C**:🚧 待 user 決策(見 §6 Finding C (a)/(b)/(c))—— 唔喺本 bug 主修範圍除非 user pick (c)

## 8. Alternatives Considered(Finding A dedup 位置)

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| 1 | **Frontend display dedup**(本 report)| Presentation 正確(dup 係 display 問題);contained 喺 chat page;保留 backend citation↔image data 完整;handle 任何來源 dup(含兩 chunk 合法共用圖)| Inline / gallery 各自要用同一 deduped 列表 | **Selected** |
| 2 | Backend dedup in `attach_neighbour_images`(attach neighbour 前先 skip 已係其他 cited chunk direct image 嘅圖)| 源頭減 over-attach | 只解 neighbour-attach 一種 dup;改 citation↔image 歸屬;global batch view 較複雜;唔解兩 chunk 合法同圖 | Rejected —— 不完整 + 較複雜 |
| 3 | 兩者都做 | 最徹底 | 違 Karpathy §1.2 simplicity —— frontend dedup 已完全解 user-visible symptom | Rejected —— over-engineered |

## 9. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-30 | Initial triage(Sev3)+ 3-finding root cause code-trace(A dedup 真 bug / B gallery label mockup-faithful / C per-image caption ingest 深度) | W42 post-closeout UI demo session user-report 圖重覆 + 標題不準 | AI self-triage,待 Chris chat-confirm |

---

**Lifecycle reminder**:Sev3 → postmortem 非強制(pattern recurring 先寫)。Finding C 若 user pick ingest 工作 → 屬獨立較大 task,可能 spawn 新 BUG / CH 或入 W43+ phase。
