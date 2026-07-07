---
phase: W87-onedrive-path-migration
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress    # in-progress | closed
---

# Phase W87 — Progress

> Daily progress + 結尾 retro。每 commit 對應一個 Day-N entry(R2)。
> **本 phase 性質**:規劃 + 設計交付為主;實際遷移執行 gated on 用戶 go + F0 IT 政策確認。

---

## Day 0 — 2026-06-23: Kickoff(規劃 + 分析)

**Action**:W87 kickoff — 把 OneDrive 路徑影響分析 + 遷移風險 + 建議文件化。

### Done
- 分類判斷:per PROCESS.md §1.1 決策樹 = **純 infra/tooling**(非 Change:Change 定義為改 product feature behavior,per §3.1;非 product Phase)。借用 Phase 三文件結構純為「小心規劃 → 設計 → 執行」嘅嚴謹度。
- 實測 grounding(見 plan.md §1.1):**最長路徑 263 字元已爆 260 上限**、`LongPathsEnabled=0`、`frontend/node_modules` 35,986 檔、disk 80% 滿、`azurite-data` 388MB、memory 232KB/23 檔。
- 現狀影響分層(Q1,L1-L7)+ 遷移風險分層(Q2,L1-L7)+ 對照總表 → plan.md §1.2/§1.3/§1.4。
- 決策建議 → plan.md §2:F0 IT gate + `LongPathsEnabled` 止血 + 平行複製法(複製不剪下、先驗後退役)。
- 執行 deliverables F0-F6 + rollback → plan.md §3/§6;checklist 衍生。

### Decisions
- **D1 立場上修**:量測揭 263 已爆限後,由上一輪「不急(無硬故障)」上修為「**遷移是正解,宜早不宜遲**」— 失效模式沉默到突然。但尊重用戶「先觀察」→ 採平行複製法 + F0 止血,既觀察又降風險。
- **D2 不觸 H1**:純開發機本地路徑遷移,不改 architecture.md §3/§4 component / vendor / blob path convention / search index schema / 8-view layout / Tier → 無 ADR。
- **D3 Docker volume 不動**:具名 volume(`ekp-postgres-data` / `ekp-langfuse-uploads`)在 Docker 區域,遷移不受影響、全程不碰。
- **D4 本 phase 不執行遷移**:交付規劃 + 設計;執行待用戶 go + F0 gate。Status=draft/in-progress。

### Blockers
- **B1(blocked-on-user)F0.1 企業 IT 政策**:本地路徑是否允許 / 裝置管理會否清 / IT 備份是否只涵蓋 OneDrive — 腳本查不到,待用戶確認。**未確認不可進 F1+**。
- **B2(blocked-on-user)go 決定**:是否進入實際遷移執行,待用戶定。

### Commits
- `<pending>` — `docs(planning): kickoff W87 onedrive-path-migration analysis + plan`(待用戶批准 commit)

---

## Day 1 — 2026-07-07: F0 gate 過 → 止血 → 同日 pivot 執行遷移(路徑 B)

**Action**:用戶 2026-07-06 重提 OneDrive 路徑問題「愈來愈嚴重」,要求重整處理方式。重量現況 → 過 F0 gate → 定當前處理路徑。

### 現況重量(對比 Day 0 全面惡化)
| 指標 | 2026-06-23 | 2026-07-06 | 變化 |
|---|---|---|---|
| 最長路徑 | 263 | **266** | +3(踩線檔移到 `references/dify` 深層 `.spec.tsx`,IDE/git-only 非 runtime) |
| 磁碟可用 | 92.4 GB | **41.2 GB** | **−51 GB** |
| 磁碟滿度 | 80% | **91.3%** | +11.3pp |
| `LongPathsEnabled` | 0 | 0(仍未止血) | — |
| Storage Sense | (Day 0 未量) | **ON(`01=1`)** | dehydration 三觸發條件全齊 |

- **項目自身佔用 ~2.8 GB**:`backend\.venv` 1610MB / `node_modules` 453MB / `azurite-data` 388MB / `.next` 177MB / `references\dify` 126MB / `.git` 19MB → **51GB 消失是系統級,非本項目**,清項目救不了大局。
- **核心惡化**:Storage Sense ON + 磁碟 91% 滿 + OneDrive 逐檔追蹤 `node_modules`/`.venv` → L2「dehydration → build 斷(`errno -4094`)」由隱性風險變**觸發條件全齊**。

### Decisions
- **D5 F0 gate 過**:用戶確認 Ricoh 受管裝置**允許寫入本地非 OneDrive 路徑**(F0.1 = 可以無限制)→ 遷移 B 技術上可行。
- **D6 目標路徑定**:`C:\Users\CLai03\dev\ekp`(前綴 ~22,用戶 profile 內,IT 政策較穩;仍遠短於現前綴 103)(F0.3)。
- **D7 當前處理 = 先止血觀察(路徑 A)**:用戶選 A 而非立即遷移 B。止血清單:A1 `LongPathsEnabled=1`(需 admin,解 L1)/ A2 pin `node_modules`+`backend\.venv` 防 dehydrate(零額外磁碟、可逆,擋 build 斷)/ A3 磁碟系統級認清(項目只 2.8GB)/ A4 升級觸發點。
- **D8 遷移 B ready-on-trigger**:F1-F5 規劃不變、目標路徑已定;觸發條件(build 斷 / 磁碟再掉 / agent 太慢)一到即升 B,~10-20 分鐘可執行、全程雙副本、可逆。

### Blockers
- **B1 CLOSED**:F0.1 IT 政策已確認(允許本地路徑)。
- **B2 部分 resolve**:go 決定 = 先 A 止血(非立即遷移),B ready-on-trigger。
- **B3(NEW,blocked-on-user)A1 需 admin**:當前 session 非 elevated(`GOADOMAIN\CLai03`),`LongPathsEnabled=1` 要用戶在 admin PowerShell 跑;domain GPO 可能覆蓋,跑完必須驗證是否生效。

### 執行:同日 pivot 到實際遷移(路徑 B,F1–F4 大致完成)
用戶當日自行(1)跑 `LongPathsEnabled=1`(admin,已驗 return 1)(2)pin `node_modules`/`.venv`(3)**全量複製項目到 `C:\Users\CLai03\ai-enterprise-knowledge-solution-project`**(非 `dev\ekp`;前綴 56,最長路徑 266→~219;profile 根非 Known Folder → 已逃出 OneDrive 同步,attributes 無 reparse)。決定切換用新資料夾開發 → pivot A→B。

**已完成(AI 從本 OneDrive session 以絕對路徑操作新資料夾)**:
- **F2 doc 同步**:本 session 的 4 個 W87 doc 編輯已在新資料夾(robocopy rc=0 = 已最新)。
- **F3 memory 重綁**:33 個 memory 檔複製到新 key 目錄 `C--Users-CLai03-ai-enterprise-knowledge-solution-project\memory\`,`MEMORY.md` 就位。
- **F4a frontend 重建**:先刪 `node_modules`/`.next` → `pnpm install` 2m58s,node_modules 35,894 檔、`next` 就位(僅無害警告 `Ignored build scripts: unrs-resolver`,F6 可選收尾)。
- **F4a backend venv 重建**:先刪 `.venv` → `python -m venv` OK,但 `pip install -e ".[dev,eval]"` **卡 MITM 代理**:`numpy-2.5.1`(12.4MB)`IncompleteRead`(310KB 後斷線)= pyproject 註解早警告的 R8 corp-proxy 擋大 binary。
  - **繞法(不切網絡、不重下載)**:舊 OneDrive `.venv`(1.6GB)完整無缺 → robocopy 其 `site-packages`(61,802 檔,numpy 2.4.4 已滿足 pyproject 無 pin 約束)到新 `.venv` → `pip install -e . --no-deps --no-build-isolation` 只重綁 editable 指向新路徑,零網絡。
- **F4b 輕量驗證(從本 session)**:`api.server` → **新路徑** ✅;核心套件全 import OK(fastapi/uvicorn/docling/numpy 2.4.4/ragas/langchain_openai/psycopg/openai/langfuse/azure);**pytest 收集 1736 tests,零 import error**。

**教訓(可複用)**:venv 重建撞 Ricoh MITM 代理擋大 wheel 時,若舊 venv 完整,**複製 `site-packages` + `pip install -e . --no-deps` 重綁**比切 mobile hotspot 重下 1.6GB 更快、零網絡;代價 = 依賴的 console script `.exe`(uvicorn/pytest/ruff)不生成,一律用 `python -m <tool>` 呼叫即可。

### 待新資料夾 session 完成(F4 全棧 gate + F5)
- 在 `C:\Users\CLai03\ai-enterprise-knowledge-solution-project` 開新 Claude session(memory 已綁好)→ 重啟服務(**infra docker 具名 volume 不動 + basename 同 → Postgres/Langfuse 資料無縫**)+ azurite + backend(`python -m api.server`)+ frontend → 驗 `/health`、chat query 引用+圖、`/conversations` 舊 session、blob 圖顯示。
- F4 全綠 + 觀察 ≥3 天 → 退役 OneDrive 副本(先封存)。**未綠前絕不刪 OneDrive。**

### Decisions(續)
- **D9 pivot A→B**:用戶同日直接執行遷移(已複製 + 決定切換),止血 A 只作過渡;當前 = 遷移執行中,backend/frontend 已重建 + 輕驗過,待新 session F4 全棧 gate。
- **D10 保留現名不 rename**:新 basename `ai-enterprise-knowledge-solution-project` 與舊相同 → `docker compose` project 名一致 → 具名 volume 無縫沿用(rename 成 `dev\ekp` 反而斷 volume 連續性)。

### Blockers
- **B3 CLOSED**:`LongPathsEnabled=1` 用戶已在 admin PowerShell 跑,已驗 return 1。

### Commits
- `<pending>` — `docs(planning): W87 Day 1 — F0 gate + pivot 執行遷移(路徑 B)F2–F4 + 代理繞法`(待用戶批准 commit)

---

## Retro(填於 phase 結束 / 執行完成後)

(待執行)

---

**End of W87 progress(Day 1;遷移執行中,backend/frontend 已重建+輕驗,待新 session F4 全棧 gate)**
