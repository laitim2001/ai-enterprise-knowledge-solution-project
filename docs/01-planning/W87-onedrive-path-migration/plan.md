# W87 plan — OneDrive → 本地路徑遷移(分析 + 規劃)

**Status**: draft(規劃 + 設計完成,**未執行** — 待用戶 go 決定 + F0 企業 IT gate)
**Kickoff**: 2026-06-23
**任務類型**: **infra / tooling migration**(per PROCESS.md §1.1 決策樹 = 純 infra,**非** product Change / Phase;借用 Phase 三文件結構純為執行嚴謹度)
**ADR**: 無(預期)。遷移**不改** architecture.md §3/§4 component / vendor / blob path convention / search index schema / 8-view layout / Tier 邊界 → 不觸 H1。純開發機本地路徑變更。
**前置 gate**: F0 企業 IT 政策確認(blocked-on-user)。**未過 gate 不可執行 F1+**。

---

## §1 Context / 緣起 + 分析

### 1.0 緣起
用戶 2026-06-23 重提:本項目放喺 OneDrive 路徑
(`C:\Users\CLai03\OneDrive - Ricoh Asia Pacific\Documents\GitHub\ai-enterprise-knowledge-solution-project`)
長期影響檔案查找 + Claude Code 工具執行效率,要求**分層分析現狀影響 + 遷移風險**,再規劃。本 phase = 把該分析 + 建議 + 執行計劃文件化留底,**規劃階段,未動手遷移**。

### 1.1 量測數據(2026-06-23 實測,grounding)
| 指標 | 量測值 | 意義 |
|---|---|---|
| **最長絕對路徑** | **263 字元** | **已超 Windows 260 上限 3 字元**(`@azure/msal-browser` 深層 `.d.ts.map`) |
| `LongPathsEnabled`(registry) | **0(關閉)** | 260 限制生效中,無長路徑豁免 |
| 根目錄前綴長度 | 103 字元 | 每個檔起跳就吃 103;可攜相對路徑部分 = 160 |
| `frontend/node_modules` 檔數 | 35,986 | OneDrive 逐檔追蹤同步的量級(未算 root / backend) |
| `.git` 檔數 | 1,614 | |
| node_modules 抽樣 Offline 比例 | 0 / 200 | 目前 hydrated 在本地(讀取暫 OK,但隨時可被 dehydrate) |
| Disk C | 381.4 GB used / 92.4 GB free(~80% 滿) | OneDrive「釋放空間」自動化的觸發壓力面 |
| OneDrive 進程 | 1(running) | 同步活躍中 |
| `infrastructure/azurite-data` | 388 MB | 活的本地 blob(上傳文件/圖片),gitignored |
| Claude memory | 232 KB / 23 檔 | 跨 session EKP 知識;綁路徑編碼 key |
| Claude session 全量 | 475 MB | 歷史對話(可選搬) |

> **核心發現**:最長路徑 263 字元**此刻已爆 260 限制**,能跑只因踩線檔是 IDE-only 的 `.d.ts.map`(runtime 不碰)+ 部分工具走 `\\?\` 擴展路徑僥倖繞過。**這是借運氣,不是穩定** — 失效模式為「沉默到突然」(裝個深層依賴 / 一次 `pnpm install` / OneDrive 一次釋放空間就可能無預警斷)。搬到 `C:\dev\ekp`(前綴 10)後最長路徑 263 → 170,headroom −3 → **+90**。

### 1.2 現狀影響分層(Q1)
| 層 | 嚴重度 | 摘要 |
|---|---|---|
| **L1 路徑長度(MAX_PATH 260)** | **高** | 263 已爆;`pnpm install` / `git checkout` / 檔案複製 / OneDrive 同步該檔皆可能 `path too long`;遷移後 +90 headroom |
| **L2 檔案 I/O + OneDrive 同步** | **高** | 3.6 萬+檔逐一同步;現 hydrated(讀 OK)但 disk 80% 滿 → 一旦 dehydrate → `errno -4094 UNKNOWN`(`.npmrc` 註解記錄的故障);每次 build/install 觸發大量上傳爭用 |
| **L3 工具可靠性** | 中(技術債累積) | 已燒 3 個永久 workaround:`.npmrc` hoisted(~10x 磁碟換掉 symlink-穿-reparse 失敗)、`playwright` 30s timeout、`vitest` threads pool。遷出後可全還原 |
| **L4 Claude Code / agent 工作流** | 中–高 | 用戶原始痛點。每次 Glob/Grep/Read/遞迴掃描穿 OneDrive reparse + 同步層;本次對話 `du` / 全樹遞迴慢到要放背景 = 直接證據;overhead 攤在整 session 每個工具呼叫 |
| **L5 資料完整性 / 同步衝突** | 中(隱性) | `azurite-data`(活 blob 寫入)+ `.env` 放雲端同步資料夾 → OneDrive 在寫入當下同步可生 `-CLai03` 衝突副本甚至寫壞 |
| **L6 安全 / 合規** | 中(雙面) | `.env` 含 Azure/Cohere secret(H5),git 有保護但**正上傳到 Ricoh 企業 OneDrive 雲**;ingest 客戶文件亦在同步。雙面:多一個暴露面 vs 企業租戶或正是認可位置 |
| **L7 成本 / 資源** | 低–中 | hoisted ~10x 磁碟 + OneDrive 持續掃描 CPU + 反覆上傳 node_modules build 產物消耗頻寬與雲配額(純浪費) |

### 1.3 遷移風險分層(Q2)
| 層 | 嚴重度 | 摘要 + 緩解 |
|---|---|---|
| **L1 一次性資料遺失** | 低(可控) | 只 3 樣 gitignored 要帶:`.env` / `azurite-data`(388MB) / memory。緩解:先複製驗證、後刪舊 |
| **L2 Claude 記憶 / session 重綁** | 低 | memory(232KB/23檔)要搬到新路徑 key 目錄,否則「失憶」;舊目錄不消失,漏了可補。可逆 |
| **L3 Docker / 服務** | 極低 | 具名 volume(`ekp-postgres-data` / `ekp-langfuse-uploads`)不在項目路徑,不受影響;連線字串全 `localhost`/相對;掃描無硬編碼絕對路徑(`.claude` hook 用 `$CLAUDE_PROJECT_DIR`)|
| **L4 失去 OneDrive 雲備份** | 中(最真實代價) | gitignored 工具(`.claude/commands`/`skills`/hooks/`scripts/`/memory)現靠 OneDrive 雲備份;遷出後只剩本地。緩解:穩定工具 commit 入 git / 另設備份 |
| **L5 企業 IT 政策** | **未知(真正 gate)** | 受管裝置:`C:\dev` 類路徑是否允許寫入 / 會否被裝置管理清掉 / IT 自動備份是否只涵蓋 OneDrive。**腳本查不到,要用戶確認** |
| **L6 環境重建成本** | 低 | 新路徑 `pnpm install` + 重建 venv ~10–20 分鐘 + 全棧重驗。一次性 |
| **L7 可逆性** | 極低 | 完全可逆,搬回即可,無 lock-in |

### 1.4 對照總表
| 維度 | 現狀(OneDrive) | 遷移後(本地) |
|---|---|---|
| 最長路徑 / MAX_PATH | **263(已爆,−3)** | 170(+90) |
| node_modules 讀取穩定性 | hydrated 才 OK,可被 dehydrate | 永遠本地、穩定 |
| 同步爭用 / 衝突副本 | 3.6 萬+檔同步,blob 即時寫入有風險 | 無 |
| agent 檔案查找 / 工具延遲 | 每次付 OneDrive overhead | 原生本地速度 |
| 已背 workaround | 3 個(永久技術債) | 可全還原 |
| secret / 客戶文件上雲 | 持續上傳企業租戶 | 不上雲 |
| 雲端備份 | ✅ 有 | ❌ 需自行安排 |
| 一次性遷移風險 | — | 低、可逆 |
| 企業 IT 合規 | 認可位置(假設) | **需確認** |

---

## §2 決策與建議

**判斷**:看到 263 已爆限後,立場由「不急」上修為「**遷移是正解,宜早不宜遲**」(失效模式沉默到突然,長期開發於此環境 = 借運氣)。但尊重用戶「先觀察」節奏,採**兼顧路徑**:

1. **F0 過 gate(必做、零成本)** — 確認 Ricoh 裝置政策:本地路徑是否允許、IT 備份是否只保 OneDrive。此題答案決定遷移代價是否重算。
2. **F0 止血(不搬也值得)** — 嘗試 `LongPathsEnabled = 1`(`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem`,需 admin),立刻解除 260 最尖銳風險,爭取觀察餘裕。(注意:需 admin、非所有舊工具吃,但對 Node/現代工具有效,淨正面。)
3. **真要遷時用「平行驗證」法(最穩)** — **複製**(非剪下)一份到新路徑,新位置跑通全棧/build/chat/memory,實用幾天確認 OK,**才**退役 OneDrive 那份。既滿足「先觀察」,又把風險降到最低、全程可回頭。

**一句話**:現狀能用但穩定性係借嚟嘅;遷移風險低、可逆,主要不確定性係企業 IT 政策(F0)。建議先過 F0 + 開 `LongPathsEnabled` 止血,觀察期內要真遷就用平行複製法。

---

## §3 Scope / Deliverables

> 執行採**階段 gate**:F0 未過不可進 F1;F4 驗證未綠不可進 F5(退役舊路徑)。

### F0 — 前置 gate + 止血(blocked-on-user / 零風險)
- **F0.1**(用戶確認)企業 IT 政策:本地路徑允許寫入?裝置管理會否清?IT 備份是否只涵蓋 OneDrive?→ 結果記 progress。
- **F0.2**(可選、即時)`LongPathsEnabled = 1`(需 admin)止血 — 解除 260 風險,獨立於遷移與否皆有益。
- **F0.3**(用戶決定)目標路徑:建議 `C:\dev\ekp`(最短);備選 `C:\Users\CLai03\dev\ekp` / `…\Projects\ekp`。下稱 `<NEW_ROOT>`。

### F1 — 遷移前置準備 / 盤點
- 停 backend / frontend / native azurite 進程(避免複製時鎖檔)。Docker **不停**(volume 不動)。
- 盤點要帶的 gitignored:`.env`、`infrastructure/azurite-data`(388MB)、Claude memory(232KB/23檔)(+ 可選 session 475MB)。
- 確認 working tree:未追蹤 `.agents/`、`AGENTS.md` 要一併帶(或先 commit)。

### F2 — 平行複製到新路徑(非剪下)
- `robocopy` 整個項目 → `<NEW_ROOT>`,**排除** `node_modules` / `.venv` / `.next`(build 產物重建)。
- **保留** `.git`(歷史)+ `.env` + `infrastructure/azurite-data` + 未追蹤檔。
- git remote(GitHub HTTPS)與本地路徑無關,複製後 `push`/`pull` 照常。

### F3 — Claude Code 記憶 / session 重綁
- `<NEW_ROOT>` 首次開 Claude Code 會自動生成新 key 目錄(`C:\dev\ekp` → key `C--dev-ekp`,即 `~/.claude/projects/C--dev-ekp/`)。
- 把舊 `~/.claude/projects/C--Users-CLai03-OneDrive---…-project/memory/` 複製入新 key 目錄(+ 可選 session 歷史)。
- 驗證:新路徑開新 session,確認 `MEMORY.md` + 23 memory 檔載入。

### F4 — 新環境重建 + 全棧驗證(gate:全綠才可進 F5)
- `<NEW_ROOT>` 跑 `pnpm install` + 重建 backend venv。
- 全棧重啟(infra docker + native azurite + backend + frontend),逐個驗 ready。
- 驗證點:`/health` 200 / chat 跑一條 query 有引用 + 圖 / `/conversations` 有舊 session data / azurite blob 圖可顯示。
- **此步全綠 = 新環境可信**,未綠不可退役舊路徑。

### F5 — 觀察期 + 舊路徑退役
- 新路徑實用 N 天(用戶定,建議 ≥ 3 天)。期間舊 OneDrive 副本保留(雙保險)。
- 確認穩定無回頭需求 → 退役 OneDrive 副本(或先壓縮封存再刪,釋放雲配額)。

### F6(可選、post-migration)— 還原 OneDrive workaround
- `.npmrc` 還原 pnpm 預設 symlink store(省 ~10x 磁碟);`playwright` / `vitest` timeout/pool 調回。
- **建議分開做**(遷移先求穩,優化後補),每項改完跑對應 test 驗證。

---

## §4 設計原則
1. **複製不剪下、先驗後退役** — F2 複製、F4 驗證、F5 才退役,全程舊副本在,可隨時回頭。
2. **階段 gate** — F0 IT gate / F4 驗證 gate,未過不前進,杜絕半遷狀態。
3. **零產品行為改動** — 遷移後系統行為必須 identical(非 Change),驗證以「行為不變」為準。
4. **Docker volume 不動** — 具名 volume 在 Docker 區域,遷移全程不碰,避免誤刪 KB metadata / traces。
5. **誠實標 blocked** — F0.1 IT 政策腳本查不到,明標 blocked-on-user,不假設。

---

## §5 Non-goals(明確唔做)
- **唔改任何產品 code / behavior** — 純路徑遷移,非 feature change。
- **唔碰 Docker 具名 volume / 不重建 Postgres / Langfuse 資料**。
- **唔改 architecture.md / vendor / blob path convention / search index schema**(不觸 H1/H2)。
- **唔喺本 phase 強制執行遷移** — 本 phase 交付規劃 + 設計;執行待用戶 go + F0 gate。
- **唔順手做 F6 還原**(優化與遷移解耦,各自驗證)。

---

## §6 Risks(執行風險 + rollback)
- **R1 複製途中 azurite-data 被鎖** → blob 複製失敗 / 不完整。緩解:F1 先停 native azurite 進程再複製;複製後比對檔數 / 抽樣大小。
- **R2 漏帶 gitignored**(`.env` / azurite-data / memory)→ 新環境缺 secret / 丟 blob / 失憶。緩解:F1 盤點清單逐項 tick,F4 驗證點覆蓋。
- **R3 企業 IT 政策禁本地路徑 / 不備份** → 遷移代價重算。緩解:F0.1 gate 先確認,未確認不動。
- **R4 OneDrive 複製期繼續同步製造衝突副本** → 緩解:複製前可暫停 OneDrive 同步(右下角 → 暫停),複製完再恢復。
- **R5 新環境驗證未過卻已退役舊路徑** → 緩解:F4/F5 硬 gate,觀察期保留雙副本,N 天後才退役。
- **Rollback**:任何階段失敗 → 直接回用 OneDrive 原副本(從未刪),新路徑副本刪除即可。完全可逆。

---

## §7 紀律自檢(kickoff)
- **H1** ✅ 純開發機本地路徑遷移,不改 §3/§4 component / vendor / blob path convention / search index schema / 8-view layout / Tier → 不觸 H1。無 ADR。
- **H2** ✅ 零新 dependency(`robocopy` 系統內建;`pnpm`/`uv` 既有)。
- **H4** ✅ 無 Tier 2 feature。
- **H5** ⚠️ 注意:遷移會把 `.env` secret 由企業雲移到本地(L6 雙面);F2 過程不可 log / commit secret 內容。
- **H6** ✅ 無 production module code 改動(F6 還原 config 才跑對應 test)。
- **H7** ✅ 無前端 mockup 對應改動(F4 驗證 chat 視覺只為確認行為不變,非改 UI)。
- **Karpathy** ✅ think(263 已爆限 + IT gate 未知 upfront surface)、simple(robocopy + 平行複製,不發明新 taxonomy / 不寫複雜遷移工具)、surgical(只動路徑,Docker volume / 產品 code 不碰)、goal(success = 新路徑全棧驗證全綠 + 行為 identical + memory 載入 + 舊副本安全退役)。

---

## §8 Changelog
- 2026-07-07 Day 1(續)— **同日 pivot A→B 並執行遷移**:用戶已(1)`LongPathsEnabled=1`(驗 return 1)(2)pin node_modules/.venv(3)全量複製到 `C:\Users\CLai03\ai-enterprise-knowledge-solution-project`(前綴 56,已逃出 OneDrive)。AI 從本 session 完成 F2 doc 同步 + F3 memory 重綁(33 檔)+ F4 重建(frontend `pnpm install` / backend venv 撞 MITM 代理擋 numpy 12MB → **複製舊 venv site-packages + `pip install -e . --no-deps` 重綁繞過**)+ 輕驗(`api.server` 新路徑 / 1736 tests 收集零 error)。目標路徑改用現名(非 `dev\ekp`,basename 同 → docker volume 無縫,D10)。**待新資料夾 session 做 F4 全棧 gate + F5 觀察退役**。詳見 progress Day 1。
- 2026-07-07 Day 1 — 用戶重提「愈來愈嚴重」,重量現況全面惡化(最長路徑 263→**266**、磁碟可用 92.4→**41.2 GB**、滿度 80%→**91.3%**、Storage Sense 確認 **ON** = L2 dehydration 三觸發條件全齊、項目自身僅 ~2.8GB 證 51GB 消失屬系統級)。**F0 gate 過**:IT 允許本地路徑(F0.1)+ 目標路徑定 `C:\Users\CLai03\dev\ekp`(F0.3)。**當前決策 = 先止血觀察(路徑 A)**:A1 `LongPathsEnabled=1`(需 admin,待用戶跑)/ A2 pin `node_modules`+`backend\.venv` 防 dehydrate / A3 磁碟系統級認清 / A4 升級觸發點(build 斷 / 磁碟再掉 / agent 太慢 → 升 B)。遷移 B(F1-F5)ready-on-trigger,規劃不變。詳見 progress Day 1。
- 2026-06-23 kickoff — 用戶要求把 OneDrive 路徑影響分析 + 遷移風險 + 建議打包成規劃文件。分類判斷:per PROCESS.md §1.1 = 純 infra(非 Change/Phase),借 Phase 三文件結構為執行嚴謹度。實測揭最長路徑 263 已爆 260(立場由「不急」上修「宜早不宜遲」)。設計 F0(IT gate + LongPathsEnabled 止血)→ F1-F5 平行複製法(複製不剪下、先驗後退役)→ F6 可選還原。**Status=draft,未執行,待用戶 go + F0 gate**。
