---
artifact: beta-cohort-onboarding-guide
status: pre-onboarding-draft
target_phase: W11-W12 production launch (post IT cred populate per W9 D1 三方 outcome)
audience: Beta cohort first-cohort users (~5-10 RAPO 內部 + 1-2 友好部門 per Q7 Resolved)
prepared_by: AI(Chris reviews + finalises pre-cohort kickoff)
related_artifacts:
  - docs/decision-form.md Q7 (Beta user source) + Q9 (Sensitivity / CMK) + Q11 (Entra ID)
  - infrastructure/entra-id/README.md (login flow + redirect URIs)
  - infrastructure/runbook/README.md (incident response if user reports issue)
---

# EKP Beta — 用戶上手指南(Onboarding Guide)

> **歡迎加入 EKP(Enterprise Knowledge Platform)Beta cohort!**
> 你係首批 Ricoh 內部用戶試用 EKP — 一個專門幫員工搵 user manual 信息嘅 AI 平台。
> **呢份指南畀你由零開始上手,~5 分鐘讀完**。
> **Beta 階段**:W11-W12(預計 real-calendar 6 月初 IT cred 交付後啟動)。

---

## 1. 點樣登入

### 1.1 訪問 URL
打開瀏覽器去 **`https://ekp-beta.ricoh.com`**

(目前未啟用,等 W9 D1 三方 session outcome 確認嘅 IT cred + DNS apply 完成後生效。)

### 1.2 登入流程
1. 點擊頁面右上角 **"Sign in"** 按鈕
2. 自動 redirect 到 Microsoft 公司登入頁面(login.microsoftonline.com)
3. 用你**Ricoh 公司 Microsoft 365 帳號**(eg. `your.name@ricoh.com.hk`)登入
4. 第一次登入會見到 **"Permissions requested"** 同意畫面 — 點擊 **"Accept"**
   - EKP 只 request `User.Read` + `api://<ekp-app>/access` scope(讀你 profile + access EKP API)
5. Redirect 返到 EKP 首頁,右上角會見到你個 username

### 1.3 登入失敗點算?
- **"AADSTS50011" Redirect URI mismatch** → 報告 `#ekp-beta` Slack channel(IT app registration redirect URI 配置問題)
- **點擊 "Accept" 後 redirect 失敗** → 試重新登入;若連續 3 次失敗 → Slack channel + 包括 timestamp + 你 username
- **"User does not exist"** → 你嘅 Ricoh 帳號可能未加入 Beta cohort access list(per Q7 — Chris 控制 access provision)→ Slack `@chris` 或 IT helpdesk

---

## 2. 點樣問問題

### 2.1 基本流程
1. 喺主頁面 chat 框入面 type 你嘅 query(例:`How do I configure the printer for double-sided printing?`)
2. 按 **Enter** 或 **Submit** 按鈕
3. 大約 **2-5 秒**後會見到答案,下面會列出引用嘅 source(citations 標明來源頁碼)

### 2.2 好嘅 query 例子(Good queries)

✅ **具體問題 + 涉及機型/版本**(retrieval 容易搵到)
- `How do I reset the password on Ricoh MP C5503?`
- `What is the toner replacement procedure for IM C400F?`
- `Paper jam recovery steps for Ricoh MP C2503`
- `How to scan to email when SMTP is configured?`

✅ **多語言 OK**(EKP 支援中英文 query;粵語 query 都得)
- `點樣 reset 個 Ricoh MP C5503 嘅密碼?`
- `IM C400F 嘅碳粉點樣換?`

### 2.3 邊際 query(Marginal — 可能 retrieve 唔到精確答案)

⚠️ **太籠統**
- `How does printing work?` → answer 會比較抽象;建議 specify 機型 + 場景

⚠️ **Out-of-scope query**(EKP 會禮貌拒答,唔會亂作答案)
- `What's the weather today?` → "I cannot answer that with the available documents"
- `Who is the CEO of Ricoh?` → 同上拒答(non-knowledge-base 知識)
- 拒答**唔係 bug**:係 EKP 嘅 "grounded refusal" 設計(per architecture.md §3.5),保證唔會 hallucinate

### 2.4 唔好嘅 query(Bad — 建議避免)

❌ **包含 PII 嘅 query**
- `Send the report to john.doe@ricoh.com`
- `Call user emp123456 about printer`
- 系統會**自動 redact PII**(email / phone / employee ID 變`<REDACTED_*>`)before 儲存,但建議直接唔好包 PII

❌ **超 2000 字符長 query**
- API hard limit;會 reject with 422 Validation Error(per architecture.md §4.5)

---

## 3. 點樣 feedback 答案質素

### 3.1 Thumbs up / down 按鈕
每個答案下面有 **👍 / 👎** 按鈕:
- **👍 thumbs_up**:答案有用 + 引用準確
- **👎 thumbs_down**:答案唔啱 / 引用錯 / 完全唔關事

### 3.2 加 comment(optional)
點完 thumbs 之後可以加文字 comment 解釋:
- 為何 thumbs_down(eg. "wrong machine model" / "answer doesn't match the manual page" / "missed the actual issue")
- 為何 thumbs_up(eg. "found exact section I needed" / "saved 10 min searching")

### 3.3 Feedback 去咗邊?
- Direct send 去 Beta team review queue(Langfuse cloud,encrypted at rest)
- Daily review by Chris + EKP team
- **唔會公開**你個 username + comment(只 aggregate analytics)
- 用作改善 EKP 答案質素 + W11-W12 production launch readiness 信號

---

## 4. Beta 階段 known limitations

### 4.1 Knowledge base scope
- **目前覆蓋**:Drive 系列 user manuals(MP / IM / SP 系列;~2000 chunks per W4 D1 baseline)
- **未覆蓋**:其他 Ricoh KB(Production print / Sales / HR 等)
- **W12+ scope**:per Q7 + Q12,Tier 2 multi-KB expansion 屬 production launch 後嘅 governance trigger

### 4.2 Performance
- **正常 latency**:2-5 秒(per architecture.md §7.1 G1 SLO < 30 秒)
- **CRAG-triggered query**(borderline 答案需要 reformulation):4-6 秒
- **高峰時段**(typically 10am-12pm):latency 可能升 5-8 秒;Beta 階段唔會 page on-call,純 monitor

### 4.3 知識更新
- **目前**:manuals 由 W2 ingest(2026-05-04 baseline);新版本 manual W11+ phase 由 Chris coordinate re-ingest cycle
- **Q15**(manual update frequency)pending Beta cohort signal — feedback 入 Slack channel 報告"answer 唔反映新版本 manual"會直接 feed Q15 resolution

---

## 5. 報告 bug / 提供 feedback

### 5.1 Slack channel
**`#ekp-beta`**(joined automatically when you're added to cohort access list)
- 一般 question / minor bug → 直接 post
- Critical bug(complete outage / cannot login)→ `@chris` mention

### 5.2 Bug report template
```
**Symptom**:你見到嘅 issue(eg. "答案完全唔關事" / "登入失敗 AADSTS50011")
**Steps to reproduce**:
  1. 訪問 ekp-beta.ricoh.com
  2. Type query "..."
  3. ...
**Expected**:你預期見到嘅 answer / behaviour
**Actual**:實際見到嘅 answer / error message
**Timestamp**:大約嘅時間(2026-06-XX HH:MM)— 用作 trace correlation
**Screenshot**(optional):if visual issue;Slack 直接 attach
**Browser + OS**:eg. Edge 134 on Win 11 / Safari 18 on macOS 15
```

### 5.3 What NOT to include
- ❌ **PII**(email / phone / employee ID — 系統會 auto-redact 但 best practice 唔好包)
- ❌ Confidential business data(非 manual 內容)
- ❌ Production credentials(API key / password / token)

---

## 6. 隱私須知(Privacy Notice)

### 6.1 你嘅 query 點樣處理
- **儲存**:Ricoh internal Langfuse cloud(encrypted at rest per Q9 Resolved — Internal classification + Azure-managed key)
- **保留期**:90 days rolling(W11+ retention policy per beta-plan-v1.md §4)
- **PII auto-redaction**:email / phone / employee ID / Ricoh ID 自動 strip 變 `<REDACTED_*>` placeholder before 儲存(per CLAUDE.md §5.5 H5)
- **Aggregate analytics only**:Beta team review aggregate patterns(top frequent queries / refusal rate / CRAG trigger rate),**唔睇個別 user 嘅 query history**

### 6.2 你嘅 identity
- Login 會儲你嘅 Entra ID `oid`(Object ID)+ `tid`(Tenant ID)+ `preferred_username`
- Audit log 用 4-character slug(eg. `u_a3b2`)記錄 cohort session correlation,**唔記**你個 full username 喺 query corpus
- **Q9 Internal classification**:no PII at rest in query corpus(`docs/03-implementation/beta-real-queries-W9-W10.yaml`)

### 6.3 你嘅 권리
- 想 export 你嘅 query history → Slack `@chris` request(7-day SLA per beta-plan-v1.md §5)
- 想 opt-out / delete data → Slack `@chris`(立即 mark cohort access disable;query corpus 90-day rolling 自然 expire)

---

## 7. 鳴謝 + W11-W12 staged rollout

Beta cohort feedback 會直接 shape EKP 嘅 W11-W12 production launch 體驗:
- **W11**:25% staged rollout — Beta cohort + 第一批 production user(extended RAPO + 友好部門)
- **W12**:100% rollout — full Ricoh internal access(post Stakeholder go/no-go review per beta-plan-v1.md §3 W12 gate)

你嘅 thumbs feedback + bug report + 直接 Slack channel discussion 全部係 W11-W12 milestone signal。**多謝你協助呢個 internal MVP 從 prototype 到 production-ready**。

---

## 8. Quick reference card(列印 / bookmark)

```
EKP Beta — Quick Reference

Login:    https://ekp-beta.ricoh.com → Microsoft Sign In
Query:    Type in chat → Enter
Feedback: 👍 / 👎 + optional comment
Bug:      Slack #ekp-beta + (template above)
Privacy:  Internal classification | PII auto-redact | 90d rolling

Latency:  2-5 sec (CRAG: 4-6 sec; peak hour: up to 8 sec)
SLO:      < 30 sec answer time (architecture.md §7.1 G1)
Refusal:  "I cannot answer..." = OOS query (NOT a bug — by design)

When stuck: @chris on Slack #ekp-beta
```

---

## 9. Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-29(W9 D4)| Initial draft | F4.2 acceptance per W9 plan §2;Karpathy §1.2 simplicity-first 1-page coverage;final cohort kickoff version W11 D1 post IT cred + DNS apply per W9 D1 三方 outcome |
| 2026-06-06(W10 D5)| F5.3 final review pass — content coverage verified across §1-§9;**carry-over to W11 D1**:Chris IT helpdesk contact info populate + Slack `#ekp-beta` channel auto-join confirmation;**no structural change W10 D5**(Karpathy §1.3 surgical — defer in-place edits until Chris contact data lands per Track A IT engagement cascade)| F5.3 W10 plan §2 acceptance partial(Track A still blocked on IT cred populate event;tabletop substitute pattern same as F5.1)|

**Lifecycle reminder**:呢份 onboarding doc 喺 W11 D1 cohort kickoff 之前由 Chris 最後 review + 加實際 contact info(IT helpdesk number + Slack channel auto-join confirmation per W10 D5 carry-over)。Real-cohort feedback W11+ 收返 lessons → W11 D5 retro update history with usage signals。
