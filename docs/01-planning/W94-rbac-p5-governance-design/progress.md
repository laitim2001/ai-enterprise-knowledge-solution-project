# W94 P5 設計 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-25(P5 設計 kickoff)

### 開工背景
- P3 完整收束(W92 P3a doc_acl override G6 + W93 P3b group 繼承 G7,已 push)。用戶問「總共幾多 RBAC 要做 + RBAC 以外仲有咩 pending」→ 答畢後用戶指示「先繼續完成 P5」。
- P5「管理權分級 + 存取治理」觸發 H1(加 `auditor` role = role model 演進 + 新治理機制)→ STOP + 跟 P1/P3 既定模式:**先設計 phase + ADR-0068,Accept 後先 implement**(次序鐵律 5)。
- **範圍 AskUserQuestion 拍板 = 「核心 + 存取覆核」**:① 角色分立 + 管理權分級 ② 存取覆核唯讀報告 + re-certify;JIT/break-glass/自動回收延後(Tier 2)。

### 現狀盤點(Explore agent + 自讀 `rbac.py`/`rbac_storage.py`)
- **Role model**:`RoleKey=["admin","editor","user","power"]`,3 active + power(Tier 2 reserved active=False)。**單層 admin,無 super-admin/owner/auditor 分化**。
- **Permission matrix**(`rbac_storage.py:80-131`):5 area × 23 permission × 4 role = 92 cell,硬編 static。`cfg.view_audit_log` + `cfg.manage_users` 皆 admin-only。
- **Guard**(`acl.py:47-126`):`require_role`/`require_kb_acl`/`assert_kb_access`,**admin `:112` 無條件 bypass**。
- **Audit log**:**已有讀端點** `GET /admin/audit-log`(`routes/admin/audit_log.py:34-54`,游標分頁 + action_type/since 過濾)→ access-review 可建喺其上。
- **存取覆核 / re-certify**:**完全 net-new**(grep 0 命中)。
- **Groups**:P3b 已備 member 方法 + 端點。
- **Explore 小結誤判更正**:佢判治理層係「Tier 2 上線先決」**唔啱** —— 上線安全先決已由 P2 達成(DG4);P5 = post-launch Tier 1.5 治理增強(同 P3)。

### kickoff(R1)
- rolling JIT 建 W94 三件套。F1-F3 = 設計 + ADR,**不 implement**。

### F1 + F2 完成(✅ 2026-06-25 Day 1)
- **用戶叫停問「P5 係咩 / 重要嗎 / 會否影響現狀 RAG」** → 答畢(P5 = 後台管理員治理,同 RAG 無關;非上線先決;零索引零檢索影響;additive 唔推倒)→ 用戶 AskUserQuestion 揀「只完成設計 + ADR,暫不 implement」。
- **infra 教訓**:kickoff commit 一度出現假輸出(虛構 hash `9c3f44c`/`0061161` + 虛構 file `threat-model-p5.md` + 敘述雜訊混入 tool result)→ 純 git 命令(`git log --format`/`git status --porcelain`)確認真 HEAD 曾係 `433ab74`(kickoff 未成功)→ 乾淨命令重 commit = `eb72f02`(真,3 file 無污染)。教訓:tool output 異常時用最簡 machine-readable git 命令交叉驗證,勿信夾雜敘述嘅輸出。
- **F1** `threat-model-p5.md`:G8 職責分立(`admin` 單層全權 = 被監察者兼監察者,情景 A 監察盲點 + B 過度授權)+ G9 存取覆核(權限永久有效無 recert,情景 C privilege creep + D 離職遺留)+ 企業 SoD/access-review 對標差距表 + Explore「Tier 2 上線先決」誤判更正(上線安全先決已 P2 達成,P5 = post-launch Tier 1.5)。
- **F2** `target-architecture-p5.md`:① auditor role(DG-P5-A 推薦 A 加 `RoleKey` 第 5 值 + matrix 唯讀 column + 新 `cfg.view_access_review` + guard 復用 `require_role`)+ 分層 push-back(DG-P5-B 推薦 B1 只加 auditor;owner=`kb_acl.manage` 已近似 / super-admin=無真實 driver speculative,留後期)② access-review report(`GET /admin/access-review` 建喺既有 store)+ re-certify(DG-P5-C 推薦 C2 報告 + `access_reviews` 標記 + audit action `access.reviewed`,無 workflow)。影響評估:零索引零檢索、additive、現有 4 role byte-identical。

### 待續(本 phase)
- F3:AskUserQuestion 問 DG-P5-A/B/C/D → 寫 ADR-0068 Proposed(含 DG resolution)→ decision owner Accept → 更新 TRACKER + retro。**Accept = 拍板設計,≠ implement**(implementation = P5-impl,用戶另批)。

### Commits
- (kickoff)`eb72f02` docs(planning): kickoff W94 P5 governance-design phase artifacts
- (本 entry)docs(planning): W94 P5 F1 威脅模型 + F2 目標架構(G8/G9 + auditor + access-review,含分層 push-back)
