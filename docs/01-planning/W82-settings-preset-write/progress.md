# W82 progress — Settings 全域 preset-mapping write surface(缺口 B,ADR-0063)

## Day 1 — 2026-06-16(kickoff)

**Context**:W81 closeout(缺口 A L3 image-anchor knobs)後,session-start gap 分析坐實**缺口 B** —
Settings「文件分類規則」tab 係「admin 指揮中心」調全域 profile→preset 映射,但 backend 冇 write
endpoint、前端 `PRESETS` 硬編碼 +「編輯」/「儲存規則」disabled。逐文件(L3,ADR-0058/0060)可調已通,
全域改唔到 →「指揮中心得一半」。

**狀況確認(code-grounded,grep 坐實非憑記憶)**:
- backend 只有 per-doc `PUT …/profile`(ADR-0058)+ `POST …/profiles/backfill`(ADR-0059),**冇**
  global preset / threshold write endpoint。
- `settings-doc-profiling.tsx` `PRESETS` 硬編碼鏡像 +「編輯」/「儲存規則」`disabled`(註解明標需
  backend write API)。

**用戶決定(2026-06-16,兩輪 AskUserQuestion)**:
1. W82 方向 = **B 收窄版**(preset 映射可寫;**threshold 維持不做** — 同 W79 ADR-0058 拍板,避免矛盾)。
2. 編輯互動 UI = **復用 Settings 既有 form 模式**(視覺零發明,W81 方案 A 同款;mockup 補 edit-form 設計
   走獨立 design sync)。
3. Guard = **還原預設 + 儲存確認**(每 row「還原預設」delete override→回出廠可逆 + 儲存前 confirm)。
4. DD-11 = **記入** `DEFERRED_REGISTER`(已記,免幻影工作項;close 條件 = 本 phase backend write API 落地)。

**Surface 過嘅 stale / 矛盾(揀之前已講清)**:
- 選項 A(D8 PDF/scan robustness)主體已 2026-06-15 探索後 defer(DD-9):robustness OK、真痛點 OCR 慢
  (Tier 2)+ 零 production scan KB → 唔行 A。
- 選項 B 原 prompt「threshold 寫入」同 W79「threshold 不做」矛盾 → 收窄為 preset 映射 only。

**ADR-0063 Accepted**(本 session):新全域 preset-mapping write surface — 持久層 mirror
`doc_profile_store.py`(global key)+ `resolve_preset` overlay(出廠值 `PROFILE_PRESETS` 不動)+
GET/PUT/DELETE API + 三 call site migrate + frontend 復用既有 form + guard。

**落點 ground(R6)**:
- 三 call site = `documents.py` `_route_profile_preset`(923)/ `PUT …/profile`(604 `preset_for`)/
  backfill(經 `_route_profile_preset`)→ 全 migrate `resolve_preset`。
- store mirror `doc_profile_store.py`(Protocol+InMemory+Postgres+factory),table 改 global
  `profile_preset_overrides(profile PRIMARY KEY, config JSONB)`。
- frontend `settings-doc-profiling.tsx`(硬編碼 `PRESETS` 20-36 / disabled 編輯 94-101)+ threshold
  card(139-146)**本 phase 不動**。

**紀律自檢**:H1 ⚠️→✅(ADR-0063 Accepted,follow persist precedent)/ H2 ✅ 零 dep / H4 ✅ 層 A admin /
H6 ✅ store+route 寫 test / H7 ⚠️→✅ edit-form design-stage expansion 用戶揀復用既有 form(視覺零發明)/
Karpathy ✅(store mirror reuse + 出廠值不動 overlay + 兩設計決定畀用戶揀 + production-preserve goal)。

**Plan 落地**:W82 folder + plan.md(active)+ checklist.md(F1-F5)+ progress.md + ADR-0063 + DD-11。

**Next**:F1 backend persist store(`preset_override_store.py`)+ `resolve_preset`。

**Commits**:
- (kickoff)docs(planning): W82 kickoff + ADR-0063 + DD-11 — Settings preset-mapping write surface
