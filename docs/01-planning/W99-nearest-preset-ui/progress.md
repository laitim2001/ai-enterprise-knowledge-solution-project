# W99 Progress — nearest 融入自動配對 + 前端 UI

> Daily progress + decisions + commits + 結尾 retro。對應 `plan.md` / `checklist.md`。

## Day 1（2026-06-27）— kickoff（active）

**Context**:W98 收尾後,用戶問「W98 嘅功能有冇配合到之前建立嘅自動分析判斷文件 → 分配配置策略?又是否可以喺頁面自行設定?」。查代碼確認:`section_anchor_nearest`（W98 knob）**未入** `profile_presets.py`（grep 11 檔無一係 profile_presets.py）+ **未上**前端（doc-config-tab 得返舊 section-anchor knob）。用戶 2026-06-27 批准「接埋呢兩步令 W98 同願景完全融合」。

**開工前讀 4 surface 確認既有 pattern**（Karpathy §1.1 think-before-coding,memory 數日舊先對代碼）:
- `profile_presets.py` — P1_sop_imgdense 而家 cap=5,無 nearest;只有 P1_sop_imgdense 開 `enable_section_anchored_aux_images`（nearest 只對佢有意義）。
- `doc-config-tab.tsx` — `DOC_TUNE_KNOB_KEYS` array 加 key 即自動 wire setKnob/dirty/save;W81 image-anchor group（line 487-505）用 `DocTuneGroup` + `DocSwitchKnob` + `DocTuneKnob`,user-approved 方案 A 零新視覺。
- `settings-doc-profiling.tsx` — EditPresetDialog draft 由完整 effective config spread（PUT full replacement → 隱藏 field 唔會洗走）;section-錨定 field 有 toggle+cap input。
- `test_profile_routing.py` — `test_p1_imgdense_preset_aligns_good_config` assert cap==5 等,改 preset 要同步。

**順帶決定（向用戶 surface）**:preset cap 5→8 對齊 drive-images-1（F3 §15 sweet spot）,令新 ingest P1 文件唔比 drive-images-1 差。

**今日產出**:W99 三件套（plan / checklist / progress）。F1-F3 分段:backend preset 自動配對 → frontend 3 surface → verify + doc-sync。

**H1**:屬 W98 ADR-0056 §Amendment 列明嘅「另一決定」preset-level flip（非 global default flip,`Settings.section_anchor_nearest` 仍 False）→ ADR-0056 §Amendment 更新,非新 ADR。

**F1 落地（backend preset 自動配對）**:
- `profile_presets.py` `P1_sop_imgdense` 加 `section_anchor_nearest=True` + `section_anchor_max_per_anchor` 5→8（對齊 drive-images-1 W98 F3 §15）+ module docstring 同步。
- **只改 P1_sop_imgdense** —— 佢係唯一開 `enable_section_anchored_aux_images` 嘅 profile,nearest 只對佢有意義（P1_sop_text/P3_slide_* 冇開 section 錨定 → 不碰,D7+§1.3 surgical）。
- `test_profile_routing.py` `test_p1_imgdense_preset_aligns_good_config` 加 `section_anchor_nearest is True` assert + cap 5→8。其他 test P1 assert 全 `max_images==80`（不變）或 dynamic `preset_for(...)`,grep 確認無漏。
- 驗:**132 passed**（profile_routing + presets_routes + doc_profile_override/backfill/read_surface + profiler + preset_override_store + effective_config + section_anchor_markers）+ ruff All checks passed + mypy `profile_presets.py` 零 error（25 errors 全 pre-existing baseline 喺 kb_management/parsers,mypy follow-imports 觸,非本改動,同 W98 query.py 情況）。

**F2 落地（frontend 3 surface）**:
- `doc-config.ts` DocConfig interface 加 `section_anchor_nearest?: boolean | null`。
- `doc-config-tab.tsx`（L3 per-doc）`DOC_TUNE_KNOB_KEYS` 加 `'section_anchor_nearest'`（自動 wire setKnob/dirty/save）+ W81 image-anchor `DocTuneGroup` 加 nearest `DocSwitchKnob`（enable_section_anchored 同 cap 之間,group 3-col grid 自然 fill）。
- `settings-doc-profiling.tsx`（admin preset 映射）EditPresetDialog section-錨定 field 加 nearest toggle（複用 dialog 既有 `.switch` row pattern）+ `fmtAnchor` table cell 反映（`section · 近錨/章末 · cap N`）。
- **H7 self-check pass**:3 surface 全屬 W78/W81/W82 user-approved design-stage expansion（mockup 無 doc-level/preset-edit design,方案 A）;加 nearest 複用既有 `DocSwitchKnob`/`.switch` row,**無新 component / 無新 mockup deviation**。
- 驗:tsc --noEmit **clean** + vitest `doc-config-tab.test.tsx` **4 passed** + `pnpm lint` clean（僅 1 pre-existing `chat/page.tsx` `<img>` warning,非本改動）。

**F3 落地（verify + doc-sync）**:
- **running-backend `GET /profile-presets` verify 改用 pytest 取代並明標 deviation（R3）**:F1 改 module-level constant `PROFILE_PRESETS`,`test_profile_routing` 直接 assert 含 nearest+cap8 + `test_profile_presets_routes`（TestClient = in-process route logic）驗 serialize 機制,兩者都喺 132 passed。running backend 係 W98 啟動 `reload=False`,重啟純為 GET = import 新 code 返新值嘅 tautology（零額外資訊,Karpathy §1.2 minimum work）→ 重啟留畀 browser demo 一齊做（offer 用戶）。
- ADR-0056 加 §Amendment(W99) — 自動配對 F1 + 前端 UI F2 + 範圍邊界（preset-level + UI,global default 仍 OFF）+ 驗證;line 311「out-of-scope」措辭更新為「preset-level 已落地 / global default 仍 out-of-scope」。
- memory [[project_per_kb_tunable_config_vision]] + [[project_inline_image_markers_w70]] append W99 段。
- DEFERRED N/A（無新 defer;DD-10/12/13/14 不受影響）。

**Commits（Day 1）**:
| Hash | Subject | 對應 |
|---|---|---|
| `97bb927` | docs(planning): W99 kickoff | F0 kickoff |
| `69bc2bb` | feat(ingestion): P1_sop_imgdense preset 加 nearest + cap8 | F1 |
| `c1aa7a7` | feat(frontend): nearest toggle 上 per-doc + preset-mapping UI | F2 |
| (本 commit) | docs(adr): ADR-0056 §Amendment W99 + W99 close | F3 |

---

## Phase Gate — G-W99 = **PASS**（2026-06-27）

- ✅ F1 preset 含 nearest+cap8 + test 綠（production-preserve:只 P1_sop_imgdense,其他 profile + global default 不變）。
- ✅ F2 三 surface 可顯示可調 + tsc/vitest/lint 綠 + H7 self-check（零新視覺,跟既有 design-stage expansion 方案 A）。
- ✅ F3 端到端 verify（pytest constant + route serialize 取代 running GET,明標 deviation R3）+ ADR-0056 §Amendment 更新（非新 ADR,per H1 W98 pre-scoped「另一決定」preset-level flip）。
- **無新 ADR**（ADR-0056 §Amendment）/ **無新 vendor**（H2）/ **無 fine-tune**（H4）/ **global default OFF = 非 P1/其他 KB production-preserve**（H1）。

## Retro（教訓）

1. **「願景融合」唔係加功能,係接駁 surface**:W98 落地咗 knob 但停喺單一 KB 人手 set;融合 = 接入(a)自動配對 preset + (b)前端 UI 兩個既有 surface。改動細（1 backend preset + 3 frontend surface）但令 vision「自動配對 + 自助調試」對 nearest 完整成立。
2. **改前先讀 surface pattern**:讀 4 file（profile_presets / doc-config-tab / settings-doc-profiling / test）先動手,確認(i)只 P1 開 section 錨定故只改一個 preset;(ii)`DOC_TUNE_KNOB_KEYS` list 驅動全 plumbing 加 key 即 wire;(iii)EditPresetDialog draft spread 完整 config 故 PUT 唔洗走隱藏 field;(iv)test 只一處寫死 cap=5。零返工。
3. **constant change 嘅 verify 唔需 running backend**:pytest 直接 assert module constant + TestClient route test 已 full cover;running backend reload=False 重啟純 tautology。明標 deviation 取代 silent skip（同 W98 deferred pattern）。
4. **甲類兩腿相連仍成立**:nearest 入 preset 令新文件自動有錨定,但上限仍 = 乙類答案完整度（generation-ceiling 已收口）—— 自動配對唔改變呢個結構邊界。
