# W79 checklist — Profile 人手覆寫 write surface(ADR-0058)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — backend override write surface

- [ ] F1.1 `DocProfileInfo`(`api/schemas/doc_profile.py`)加 `manual_override: str | None = None`(向後相容;system auto 保留)
- [ ] F1.2 新 endpoint `PUT /kb/{kb_id}/docs/{doc_id}/profile` + `ProfileOverrideRequest {profile}`:套 `preset_for` 覆蓋 per-doc config + set manual_override + upsert profile + 404 未 ingest
- [ ] F1.3 re-ingest preserve override — `_run_ingest_pipeline` profile persist(813-821)upsert 前 read 舊 merge `manual_override`
- [ ] F1.4 L2 summary resolve effective — `list_documents` join `summary.profile = manual_override ?? profile`
- [ ] F1.5 test `test_doc_profile_override.py`(H6)— 套 preset + persist + 覆蓋現有 config + 404 + re-ingest preserve + summary effective;mypy 0 + ruff 0 + pytest pass + 無 regression

## F2 — frontend L3 override wire + effective 顯示

- [ ] F2.1 `documents.ts` `DocProfileInfo` 加 `manual_override?: string | null` + `documentsApi.overrideProfile`(PUT /docs/{id}/profile)
- [ ] F2.2 L3 `doc-config-tab.tsx` override `select` wire onChange → mutation → invalidate + toast;有 override 標「已人手覆寫(系統原判 X)」+ select 預設 effective
- [ ] F2.3 L2 `kb/[id]/page.tsx` badge 顯示 effective(backend resolve;確認正確)
- [ ] F2.4 type-check 0 + lint 零新 warning + build ✓;H7 視覺不變

## F3 — 驗證 + closeout

- [ ] F3.1 backend pytest + mypy + ruff 全綠;frontend type-check + lint + build 全綠
- [ ] F3.2 browser 驗 override(服務 running:L3 揀 profile → persist → L3/L2 反映 effective + 套 preset)
- [ ] F3.3 closeout:plan closed + progress retro + ADR-0058 README index + memory append
