---
phase: W68
name: dedup-before-cap
status: active       # draft | active | closed
created: 2026-06-12
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "W67 判決:cap 預算被重複 ref 食盡令 cited chunks 圖被清零 = mega-query 0.74 封頂真兇;用戶 2026-06-12 批准實施(AskUserQuestion「批准,实施」)"
adr: "0054"          # supersede ADR-0040「blunt no-dedup」該項決定
spec_refs:
  - docs/adr/0040-per-kb-tunable-retrieval-config-scope.md  # 被 supersede 嘅 blunt 決定
  - docs/01-planning/W67-missing-image-chunk-mapping/       # 證據鏈(預算時間線 + 17/17 cited)
  - docs/01-planning/W66-cap-refs-vs-unique-diagnosis/      # 三軸數據(被 W67 重新詮釋)
---

# W68 — dedup-before-cap(ADR-0054)

> **緣起**:W67 證據鏈 — 漏網 17 張全部屬於 cited chunks,被「cap 預算計 refs + 前置 citation
> 高重複 neighbour aux 食盡」清零(citation 1–4 食盡 150 refs / 68% 重複 / citation 5–26 全 0)。
> 用戶批准:**`cap_images_per_answer` 預算改計 unique(重複 ref 剪走、唔食預算)** + ADR +
> test + A/B 驗證 + drive-images-1 cap 50→70。
>
> **R6 核實**:函數 citation_enrichment.py:111(唯一定義);caller query.py:492 + :645(同語義);
> test 覆蓋 test_effective_config.py:285-343(**fixture 圖 checksum 跨 citation 相同 — 兩個現有
> test 喺新契約下會 fail,屬預期,改寫反映新契約**)+ test_ch010_chapter_overview_pin.py +
> test_config_test_route.py cap test(fixture checksum 唔同 prefix → 預期不受影響)。

## 1. 行為契約(ADR-0054)

- `max_images=None` → **原樣返回,連 dedup 都唔做**(production-preserve,同舊行為 bit-identical)。
- `max_images` 設定時:walk citations in order;每張圖 key = `checksum_sha256 or blob_url`;
  **已見過嘅 key = 重複 ref → 剪走,唔食預算**(即使預算未盡);fresh 圖食 1 預算;預算盡後
  fresh 圖都剪。citations 永不 drop。
- 效果:cap 變成「unique 圖上限」;前置 citation 嘅重複 aux 唔再餓死後面 cited chunks。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | ADR-0054(Accepted,approver Chris 2026-06-12)| 入 docs/adr/ + README index |
| **F2** | `cap_images_per_answer` 改寫 + docstring 更新(指向 ADR-0054)| ruff clean |
| **F3** | test 改寫 + 新增(dup-唔食預算 / dup-喺預算內都剪 / None passthrough 不變 / 跨 citation 預算延續)| `test_effective_config.py` + `test_ch010` + `test_config_test_route.py` 全綠 |
| **F4** | backend 重啟 + **A/B 驗證**:9/9 image-recall run @ persisted 配置(cap 70)vs W64 baseline 0.855;Q001/Q043 預期大升、對照 3 條持平、precision 監察 | mean 顯著 >0.855 + 對照 1.00 + precision 唔崩 |
| **F5** | drive-images-1 cap 50→**70** persist(用戶批准配套)+ readback | readback=70 |
| **F6** | doc-sync(rollup + memory + ADR index)+ closeout | — |

## 3. Acceptance Criteria

- **AC1**:None-cap 路徑 bit-identical(test 證)— 無 per-KB cap 嘅 KB 零影響。
- **AC2**:新契約 test 全綠 + 兩個改寫 test 註明 ADR-0054 行為變更理由。
- **AC3**:A/B — Q001 recall 0.74 → **預期 ~1.00**(W67 證 65/65 in reach);Q043 升幅一齊量
  (W67 未映射 Q043,升幅係新資訊);對照 3 條(Q002/Q004/Q006)持平 1.00;precision ≥0.95。
- **AC4**:per-citation 圖數(config-test breakdown / chat pill)語義變更(共享圖只喺首現
  citation 出現)記入 ADR Consequences — 屬 display 對齊(frontend 本來就 dedup),非 regression。

## 4. 風險

- **R1 🟡 Q043 升幅未知**(W67 只映射 Q001):若 Q043 漏網圖唔全喺 cited chunks → 升幅有限,
  屬有效新資訊,唔阻 closeout。
- **R2 🟢 下游依賴重複 ref**:frontend display / gallery 本來就 dedup(BUG-026)→ 預期零影響;
  vitest 已有 suite 兜底(本 phase 唔改 frontend)。
- **R3 🟢 infra transient**:同前。

## 5. 非目標

- ❌ None-cap 路徑加 dedup(production-preserve)。
- ❌ 改 frontend(display dedup 已存在,行為對齊咗反而更一致)。
- ❌ Q005 b-2 零引用模式(獨立 synthesizer 層問題)。

## 6. H 核對

- **H1**:pipeline 行為改動 + 反轉 ADR-0040 明文決定 → **已走完 STOP+ask 程序**(W67 closeout
  提案 → 用戶 2026-06-12 AskUserQuestion 批准「批准,实施」)→ ADR-0054 記錄。
- **H6**:`backend/generation/` 配套 test 同步改(critical pipeline 範圍)。
- **H2/H3/H4/H5/H7**:不觸。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | Initial plan(active)| W67 證據鏈 + 用戶批准;R6 核實 caller ×2 + test fixture 跨 citation 同 checksum(兩 test 預期 fail → 改寫) |
