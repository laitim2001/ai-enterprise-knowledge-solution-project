---
bug_id: BUG-006
report_ref: ./report.md
progress_ref: ./progress.md
written: 2026-05-22
author: "AI"
sign_off: pending     # pending | signed
---

# BUG-006 — Postmortem

> **Mandatory for Sev1 / Sev2**(per `PROCESS.md §4.5`)。Sev2:chat-against-a-KB(EKP core flow)broken out-of-the-box,no usable workaround。

## 1. Incident Timeline

> Single session 2026-05-22(real-calendar collapsed — discovery → fix same sitting)。Wall-clock 未逐步記錄,以下為事件順序。

| Step | Event |
|---|---|
| 1 | User(Chris)在 `/chat` 對住啱建立嘅 KB 發問 → 502 `pipeline.retrieval_failed`,reported |
| 2 | First investigation — 留意到報錯 URL index = `ekp-kb-drive-v1`,並非 KB 對應 index |
| 3 | `GET /kb` + `GET /kb/{id}/documents` 查實際狀態 → KB = `drive-user-manual-1`(非 `ekp-kb-drive-v1`)|
| 4 | Trace frontend → backend:`chat/page.tsx` `kbId` / `streamQuery` / `kb_naming.kb_id_to_index_name` |
| 5 | Root cause identified — `kbId` state stale `DEFAULT_KB_ID='drive_user_manuals'` legacy alias,無 sync effect |
| 6 | Chris confirmed Bug-fix BUG-006 + Sev2 + 4-doc workflow |
| 7 | Fix implemented(`chat/page.tsx` sync `useEffect`)+ regression test added + verified |
| **Total** | discovery → fix:single session |

## 2. Root Cause(detailed)

`frontend/app/(app)/chat/page.tsx` 維持兩個關於「當前 KB」嘅值:

- **`kbId`**(`useState`,`:163`)— raw state,初始化做 `DEFAULT_KB_ID = 'drive_user_manuals'`(`:117`,註解標明「W3 single-KB POC」)。**送去 backend 嘅就係佢**(`streamQuery` `:332` + `conversationsApi.create` `:233`/`:510`)。
- **`activeKb`**(derived,`:172`)— `kbs.find((k) => k.kb_id === kbId) ?? kbs[0]`。**畫面顯示嘅就係佢**(KB `<select value={activeKb?.kb_id}>` `:862`)。

當載入嘅 KB(`drive-user-manual-1`)同 `kbId`(`'drive_user_manuals'`)唔等時,`activeKb` 正確 fallback `kbs[0]` → **下拉選單顯示正確** → 用戶冇任何視覺線索話佢知有問題。但 `kbId` state **永遠冇被 sync** —— 冇 `useEffect` 將佢拉返去有效 KB。於是每條 query 送嘅 `kb_id` 都係 stale 嘅 `'drive_user_manuals'`。

`'drive_user_manuals'` 喺 `backend/storage/kb_naming.py` 係 `_LEGACY_KB_ID` —— `kb_id_to_index_name` 將佢映射到 legacy index `ekp-kb-drive-v1`(ADR-0018 文件化嘅 Tier 1 legacy alias)。但 `ekp-kb-drive-v1` 喺 `azureaisearchtesting` resource 從未建立 → Azure 404 → `pipeline.retrieval_failed` 502。Backend 無 bug — 完全照 ADR-0018 設計運作。

**Why didn't this surface earlier?**

1. **W3 POC 假設遺留** — W3 single-KB POC 年代,seed KB 就係 `drive_user_manuals`(legacy index `ekp-kb-drive-v1` 當時存在)→ 嗰陣 `DEFAULT_KB_ID` default「啱用」。Multi-KB(W15/W18/W20)landed 後、加上換咗 Azure resource(無 legacy index)、加上用戶建真實 KB —— 個 default 先變錯。W20/W22 chat rebuild 沿用咗 `DEFAULT_KB_ID`(preserve-existing / plan-text contamination — `feedback_design_fidelity.md` D7/D9 anti-pattern class)。
2. **Display 掩蓋 stale state** — `activeKb` 衍生值令下拉選單**永遠顯示正確**,bug 完全冇 UI 線索。
3. **`/chat` 零自動化測試覆蓋** — `frontend/tests/unit/` 21 個 test file 入面**冇 chat page test**。亦無一個 chat-query 自動化 E2E 真正對住真實 KB 發 query —— interactive chat flow E2E 由 W12 起一直 **smoke-user-deferred**(per session-start.md §11)。呢個 bug 正正係長期 defer interactive E2E 嘅代價。

## 3. Impact Assessment

- **Users affected**:任何對住真實 KB(kb_id ≠ legacy alias)用 `/chat` 嘅 user — dev / 任何 future Beta cohort。100% chat query 失敗。
- **Duration of impact**:由 multi-KB + 換 Azure resource 之後一直存在(latent);實際被觸發 = 用戶今次測試。
- **Data loss / corruption**:No。
- **Workarounds used during incident**:None — 無 usable workaround(single-option `<select>`)。
- **Cost impact**:None(dev 環境;Beta 未 launch)。

## 4. What Worked

- **錯誤訊息夠具體** — 502 envelope 直接帶住 Azure index URL(`ekp-kb-drive-v1`),一眼睇出 index name 唔對,大幅縮短診斷。
- **Backend 健康 + API 可直接 query** — `GET /kb` / `GET /kb/{id}/documents` 即刻俾到實際 KB / 文件狀態,confirm 咗 frontend↔backend 嘅 mismatch。
- **`kb_naming.py` 文件清晰** — module docstring + `_LEGACY_KB_ID` 命名令「點解 `drive_user_manuals` → `ekp-kb-drive-v1`」一讀即明,確認 backend 無 bug。

## 5. What Didn't Work / Was Slow

- **零 chat page 測試** — 無 Vitest、無真正 chat-query E2E → 一個 golden-path bug 一路 ship 都冇 gate 攔到。
- **smoke-user-deferred backlog 積壓** — interactive chat E2E 由 W12 defer 到而家;呢個 bug 係嗰個 deferral 嘅直接後果。

## 6. Surprises

- **Display 正確 ≠ 行為正確** — 下拉選單顯示正確嘅 KB,令人(包括 review)以為 KB 選擇 OK。Raw-state vs derived-display-value 分叉係一個隱蔽 bug class。
- **單一 option `<select>` 令「重選」唔可能** — 通常「揀返同一個」可作 workaround,但 HTML `<select>` `onChange` 只喺值改變時 fire → 1 個 option 時永遠 fire 唔到 → 完全無 workaround。

## 7. Action Items

| # | Action | Owner | Due | Component(s) | Status |
|---|---|---|---|---|---|
| 1 | BUG-006 regression test(`chat-kb-sync.test.tsx`)— chat 送出真實 kb_id | AI | 2026-05-22 | C10 | Done(本 bug-fix) |
| 2 | 擴充 `/chat` page Vitest 覆蓋(send flow / KB selector / conversation CRUD)— 目前 chat page 零 unit test | AI | W24d+ | C10 | Open |
| 3 | Audit 其他 W3/W-early-POC 遺留 hardcoded default constant(`DEFAULT_*` grep)— `DEFAULT_KB_ID` 唔一定係唯一一個 | AI | W24d+ | C09/C10 | Open |
| 4 | Seeded-dev-KB script + 對住 seeded KB 嘅 chat-query 自動化 E2E — 解 long-standing smoke-user-deferred gap | AI / Chris | post Track A IT cred | C10/C12 | Open |
| 5 | Dev note:raw-state vs derived-display-value 分叉 anti-pattern(送出去嘅應該係 displayed 嘅值)— 考慮入 `feedback_design_fidelity.md` memory | AI | W24d+ | — | Open |

## 8. Risk Register Update

- 唔新增 R-number(交 Chris 評估)。但本 incident **實證咗**長期 smoke-user-deferred interactive E2E 嘅風險 —— 一個 core golden-path bug 喺所有自動化 gate(`tsc` / `lint` / `[oklch`=0 / Vitest)全綠之下一路 ship。建議 `RISK_REGISTER.md` 反映「interactive E2E coverage gap」嘅 probability 已由 potential → realized(Action Item #4 對應 mitigation)。

## 9. Component Design Note Updates

- `components/C10-*.md`(若存在):edge-case section 補「KB selection state(`kbId`)必須 sync 去已載入嘅 `kbs`;送 backend 用 resolved value 而非 raw state」。C10 design note 若仍 pending 則喺起草時納入。

---

**Sign-off**:AI | Date:2026-05-22
**Reviewed by**:_pending_ — Chris | Date:_pending_
