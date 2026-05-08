# ADR-0014: Hybrid Auth Model — Microsoft Entra ID SSO + Self-Service Email Register

**Date**: 2026-06-10
**Status**: Accepted
**Approver**: Chris(acting as Stakeholder per past sessions authorization pattern;explicit ack 2026-06-10 evening session W11 D2 cont)

## Context

原本 Tier 1 spec(architecture.md v5.1)假設 Drive Project 用戶**只有** Ricoh internal staff,所以 Q11(decision-form.md)decided「Microsoft Entra ID enterprise SSO」作為唯一 auth 路徑。Q11 status 已 Resolved per W7-W8 implementation。

**Trigger**:W11 D2 cont(2026-06-10)evening session,User 評估 frontend UI completion 狀態時 surface 兩個獨立但相關 gap:
1. Frontend completion ~15-20% vs §5 spec(barebones page.tsx,no shadcn/ui,no tokens consume — see ADR-0015 詳細)
2. **缺乏 public-facing entry point**:`/` 路徑直接係 chat(假設用戶已 logged-in),冇 public landing page、冇 self-service register flow、冇 forgot password flow

User explicit ack:scope expansion 必要,**Tier 1 v6 amendment 必須 cover hybrid auth model**(SSO + self-register),不可 defer 到 Tier 2 — 原因:
- Drive Project 真實 user pool **可能包含** external partner / vendor / contractor 唔在 Ricoh Entra ID tenant 入面
- Public landing page + register flow 屬 standard SaaS user journey 必需
- W12-W15 UI sprint 已 plan,順便 land hybrid auth 比 Tier 2 額外 sprint 節省

## Decision

Tier 1 v6 amendment **新增 self-service email register flow**,與既有 Microsoft Entra ID enterprise SSO **並行存在**。

### 兩條 auth 路徑

**路徑 A — Internal SSO**(per Q11,unchanged):
- 用戶來源:Ricoh staff(已喺 Entra ID tenant 入面)
- Login flow:`/login` → click「Sign in with Microsoft」→ MSAL redirect → Microsoft → callback → `/chat`
- User identity:`oid` claim from Entra ID JWT;backend `Settings.feature_auth_mock=False` post-IT cred delivery
- Authorization:Entra ID app role(per Pattern A 8-step infrastructure setup)
- Backend component:C12 Auth Provider(`backend/api/auth/msal_provider.py`,Day 1 + W7-W8 actuals)

**路徑 B — Self-service register**(v6 amendment NEW):
- 用戶來源:External partner / vendor / contractor / public(non-Entra-ID user)
- Register flow:`/register` 3-step wizard(account info → email verify → welcome)
- Login flow:`/login` enter email + password → POST `/auth/login` → backend verify email + Argon2id password → session token → `/chat`
- User identity:internal `users` table(separate from Entra ID claims),unique email key
- Authorization:simplified role flag(`role: "user" | "admin"`),admin manually granted via Admin Console
- Backend new components:
  - C12 Auth Provider extended:`/auth/register`、`/auth/verify-email`、`/auth/login`、`/auth/forgot-password`(Tier 2 deferred)endpoints
  - C13 **Email Verification Service** NEW(per architecture.md §3 v6 amendment) — vendor decision pending OQ-Q22
  - User table schema(`users`):id、email(unique)、password_hash(Argon2id)、display_name、verified、verification_token、role、created_at、last_login_at
  - Session token storage(initial:server-side session + httpOnly cookie;defer JWT to Tier 2 if needed)

### Email Verification Service vendor decision(OQ-Q22 NEW)

候選:
- **Azure Communication Services** — Azure-native,billing 整合,SDK Python 支援
- **SendGrid** — 業界標準,免費 tier 100/day 足夠 Tier 1 cohort
- **AWS SES** — 唔考慮(off Azure stack per spec §13)

Decision deferred to W12 D1-D2 W12 phase plan kickoff。Default-if-unanswered:Azure Communication Services(同 Azure stack 一致 per CLAUDE.md §5.2 H2)。

## Alternatives Considered

### Alt A:Pure SSO Tier 1(rejected)

**Tradeoff**:
- ✅ Pro:original spec 一致,無新 backend 工作,無新 vendor decision
- ❌ Con:Drive Project external partner 用戶完全冇 access path → adoption ceiling 低
- ❌ Con:Public landing page 冇 register CTA 會造成 UX cliff(user discover platform → 但 register 路徑唔見 → bounce)

**Reject reason**:User explicit decision to expand scope per W11 D2 cont session;adoption + UX impact 不可接受 trade。

### Alt B:Pure self-register Tier 1(SSO defer Tier 2)(rejected)

**Tradeoff**:
- ✅ Pro:simpler backend(只一條 path)
- ❌ Con:Q11 already Resolved with Entra ID;W7-W8 substantial implementation work would be discarded
- ❌ Con:Internal Ricoh staff lose seamless SSO(每次 login 要 re-enter password)
- ❌ Con:Track A IT cred event 已係 W11 plan critical path,reverting 等於 abandon W11 投入

**Reject reason**:既存 Entra ID infra investment + Q11 decision lock-in。

### Alt C:Hybrid(this ADR)— ACCEPTED

兩條 path 並行,各自服務唔同 user segment。Backend 額外 ~1 sprint 工作量,但 UX completeness + adoption ceiling 大幅提升。

## Consequences

### Positive

- **Adoption ceiling 大幅提升**:internal Ricoh staff(SSO seamless)+ external partner(self-register self-service)
- **Standard SaaS UX**:public landing page + register CTA + login form + forgot password 都係 user expectation
- **Tier 2 friendly**:hybrid 已 establish auth abstraction,Tier 2 加 Google / GitHub OAuth 嘅成本低
- **Already-budgeted impl window**:W12-W15 UI sprint cycle 順便 land,無新 sprint required

### Negative

- **Backend sprint scope expand**:~1-1.5 weeks 額外 backend work(C13 email service + user table + auth endpoints + verify flow)— absorb in W13(per W12-W15 roadmap)
- **新 OQ-Q22**(email vendor decision)— must land W12 D1-D2 to unblock W13 implementation
- **新 user data store**:internal `users` table 增加 PII 處理範圍(email + password hash + display_name)— Settings spec § 影響 + R5 risk register 補一條 R-A1 user data PII handling
- **Production launch defer impact**:hybrid auth 屬 W12-W15 sprint 嘅一部分,production launch W16+ delay 已 acknowledged

### Neutral

- **OQ-Q22 vendor**:Azure Comm Service vs SendGrid 都係成熟 production-ready,主要 trade billing convenience vs feature-richness
- **Forgot password flow**:暫時 defer Tier 2(per §5.10 spec note)— self-register 用戶 W12-W15 phase 唔會有 password reset path;Tier 2 補
- **2FA / OAuth providers**:defer Tier 2(per §11)— 唔影響 Tier 1 hybrid model 框架

## References

- architecture.md v6 §5.10 + §5.11(Login / Register view spec)
- architecture.md v6 §13.12(v5.1→v6 amendment trigger)
- ADR-0015(UI Tier 1 expansion)— sister ADR for同 W12 amendment cycle
- decision-form.md Q11(Entra ID SSO,Resolved)
- decision-form.md Q22(NEW pending — email verification vendor)— W12 D1-D2 land
- W11 D2 progress.md cont entry(2026-06-10 stakeholder ack)
- W12-W15 UI sprint roadmap — `docs/01-planning/W12-ui-foundation-discovery/plan.md`(W12 phase folder)
- CLAUDE.md §5.1 H1 architectural change constraint(this ADR satisfies)
