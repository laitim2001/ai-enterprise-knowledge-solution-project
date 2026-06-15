# W79 checklist — Profile 人手覆寫 write surface(ADR-0058)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — backend override write surface

- [x] F1.1 `DocProfileInfo`(`api/schemas/doc_profile.py`)加 `manual_override: str | None = None`(向後相容;system auto 保留)
- [x] F1.2 新 endpoint `PUT /kb/{kb_id}/docs/{doc_id}/profile` + `ProfileOverrideRequest {profile}`:套 `preset_for` 覆蓋 per-doc config + set manual_override + upsert profile + 404 未 ingest + 422 無 preset + 503 無 store(用單獨 store helper 唔 require ingestion services)
- [x] F1.3 re-ingest preserve override — `_run_ingest_pipeline` profile persist upsert 前 read 舊 merge `manual_override`
- [x] F1.4 L2 summary resolve effective — `list_documents` `summary.profile = manual_override ?? profile`;override → confidence null(唔黃旗)
- [x] F1.5 test `test_doc_profile_override.py`(H6)8 tests — 套 preset + persist + 覆蓋現有 config + 404 + 422 + 503 + summary effective + backward-compat + re-ingest preserve;**ruff 0 + mypy 新 code clean(剩 line 116 pre-existing baseline)+ pytest 22 passed(override 8 + read-surface 14,zero regression)**

## F2 — frontend L3 override wire + effective 顯示

- [x] F2.1 `documents.ts` `DocProfileInfo` 加 `manual_override?: string | null` + `documentsApi.overrideProfile`(PUT /docs/{id}/profile)
- [x] F2.2 L3 `doc-config-tab.tsx` override `select` wire onChange → mutation → invalidate doc-detail + doc-config + toast;有 override 標「已覆寫 · 系統原判 X」+ select 預設 effective + `DocProfileBadge` 顯示 effective
- [x] F2.3 L2 `kb/[id]/page.tsx` badge 顯示 effective(backend resolve;override → confidence null 唔顯示 % + 唔黃旗)
- [x] F2.4 type-check 0 + lint 零新 warning + build ✓(15/15 pages);H7 視覺不變(select static → functional)

## F3 — 驗證 + closeout

- [x] F3.1 backend pytest 22 + ruff + mypy 全綠;frontend type-check + lint + build 全綠
- [x] F3.2 **browser 驗 override(端到端 PASS)**:L3 揀 P1_sop_imgdense → backend persist(manual_override=P1_sop_imgdense + preset 套落 cap 80 + section_anchored + anchor_cap 5,覆蓋舊 cap 20)+ system auto profile(P1_sop_text)保留 + L3 badge/select effective「P1 圖密SOP · 已覆寫 · 系統原判 P1 文字SOP」+ signals 不變(可解釋)+ L2 effective(profile=P1_sop_imgdense,confidence null)。**坑:backend 改 code 後要重啟先 pick up 新 endpoint**(初次 override 撞 404 — running backend 舊 code;TaskStop + 重起後 PASS)
- [x] F3.3 closeout:plan closed + progress retro + ADR-0058 README index(kickoff done)+ memory append
