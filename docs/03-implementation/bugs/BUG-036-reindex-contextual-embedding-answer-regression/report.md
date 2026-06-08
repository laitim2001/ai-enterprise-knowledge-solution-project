---
bug_id: BUG-036
title: "Chat 文字答案格式 regression — re-index 引入 contextual embedding 後步驟列亂編號 + 重複行"
severity: Sev2          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: verifying   # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-06-08
reporter: "End-user (Chris)"
affects_components: [C04, C05]
spec_refs:
  - architecture.md §3.2   # contextual retrieval / embedding (ADR-0045)
  - architecture.md §3.7   # citation expansion (ADR-0034)
  - architecture.md §3.5   # synthesis / answer composition
---

# BUG-036 — Chat 文字答案格式 regression（re-index 後步驟列亂編號 + 重複行）

> **Report version**:1.0(initial)
> **Triage approver**:Chris(2026-06-08，揀「開 Bug-fix 正式診斷+修」）

## 1. Symptom

drive-images-1 chat 問「How do I process and confirm journal voucher transactions?」，**文字答案由清晰格式變亂**：
- **OLD（清晰）**：用 source 自身編號（`GL03-1. Create General Journal` → `1.1`、`1.2`…），分段乾淨，無重複。
- **NEW（亂）**：synthesizer 自行重新編號成 `1.1–1.24 / 2.1–2.14 / 3.1–3.8 / 4.1–4.11 / 5.1–5.6` 階層，**出現重複行**（「Confirm Approval Request」×2-3、「Approve General Journal」×2、「Post the Journal/Post Journal」），仲有 artifact「2.13. 2.Click Download」「2.14. 3.Input…」。用戶評「內容看起來都混亂了」「很嚴重」。

⚠️ **CH-011（圖片 doc_order / 順序修復）intact + 獨立** —— 圖片順序仍正確；本 bug 純粹係**文字側** regression。

## 2. Reproduction Steps

1. Chat UI（`localhost:3001`）選 KB `drive-images-1`
2. 問「How do I process and confirm journal voucher transactions?」
3. **觀察**：答案 13 citations，步驟列 synthetic 重編號 + 重複行（CAR×2、AGJ×1，偶爾 ×3）

**Reproduction reliability**:Always（API 連續 2 run 重現 13 cites + CAR×2；synthesis 有輕微 variance 影響確切重複數，但亂格式穩定）

**Environment**:local dev（backend venv :8000，HYBRID_USE_SEMANTIC_RANKER=false；frontend :3001）

## 3. Expected vs Actual

- **Expected**：清晰、跟 source 結構、無重複行的步驟列（OLD 格式）。
- **Actual**：synthetic 重編號 + 重複 heading 列 + artifact 前綴。

## 4. Impact

- **Affected users / scenarios**：drive-images-1（及任何 re-index 後 = contextual embedding + `answer_detail=detailed` + 完整性 expansion 開）的列舉/程序型 query。
- **Workaround available?**:Yes（內容仍齊全，只係格式亂；config 可緩解 — 見 §6）
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev2**：core user-facing chat 答案 surface 的品質 regression，用戶明確 flag「很嚴重」；重複行 + artifact 係明確 defect（非純風格）。非 Sev1（無 outage / data loss，內容仍完整可用）。Sev2 → **mandatory postmortem**（per PROCESS.md §4.5）—— 重點教訓 = re-index 操作的副作用未被預警。

## 6. Initial Diagnosis（updated as investigation progresses）

- **Initial hypothesis（triage 2026-06-08）**：re-index（為 CH-011 doc_order 而做）**首次把 CH-008 contextual embedding（ADR-0045，今日 merge）套落 drive-images-1**。OLD/NEW **同 config、同 chunk 文字**，唯一變數 = contextual embedding（`build_contextual_document(section_path, chunk_text)`，orchestrator L169，**always-on 無 toggle**）。embedding 改 → 檢索 ranking shift。
- **支持證據（2026-06-08 API）**：
  - `/query` 回 **13 citations**：4 個 reranked（chunk 24/29/31/34，有 score）+ **9 個 score-0 = citation_expansion materialized**（chunk 25/26/27/28/30/32/33/35/36 = 整段 §3.1.1–§3.1.5）。
  - drive-images-1 config：`answer_detail=detailed`、`enable_citation_post_hoc_expansion=true depth=1 max_aux=10`、`parent_doc=false`、`rerank_k=5`。
  - **機制**：`detailed` synthesizer 收到整段 §3.1（含重複 heading 的相鄰 chunk）→ 把每行逐一列 → synthetic 重編號 + 重複行。
  - 2 run 重現穩定（CAR×2），確認非純 synthesis variance（但 variance 影響確切重複數）。
- **待確認（investigation）**：
  - (i) contextual embedding 係唯一變數？（vs OLD 是否其實另一 config）
  - (ii) 重複行的確切來源 — 哪幾個相鄰 chunk 含重複 heading 文字？synthesizer 點解唔 dedup？
  - (iii) 哪個 lever 最有效還原清晰格式（contextual toggle re-index / expansion 收細 / answer_detail / synthesis prompt dedup），且唔犧牲完整性？

## 7. Acceptance for Fix（checklist preview）

- [ ] Reproduction confirmed locally（已：API 2 run）
- [ ] Root cause identified（contextual embedding 引入 vs expansion 餵料 vs synthesis dedup — 區分清楚）
- [ ] Fix implemented（方向待 §6(iii) 投票後定）
- [ ] Regression test added（如涉 synthesis/retrieval code）
- [ ] Verified（重跑 §2 repro：清晰格式還原 + 完整性不退 + CH-011 圖片順序不受影響）

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-08 | Initial triage（Sev2）+ 診斷捕捉 | CH-011 re-index 副作用，用戶 flag | Chris |

---

**Lifecycle reminder**:Sev1/Sev2 → `postmortem.md` mandatory（per PROCESS.md §4.5）。
