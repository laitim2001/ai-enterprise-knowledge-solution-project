---
bug_id: BUG-013
title: "Next.js dev proxy does not inject dev Bearer for browser-native requests (<img>, <video>) → mock-mode session has no cookie → 401 even after BUG-012 same-origin fix"
severity: Sev3
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 — DevTools Network 8 個 `/api/backend/kb/.../screenshots/<sha>.png` GET requests 全部 401 Unauthorized post-BUG-012 same-origin fix)"
affects_components: [C09]    # Admin Console UI / Next.js proxy route handler
spec_refs:
  - architecture.md §5      # Application UI
  - frontend/app/api/backend/[...path]/route.ts (W11 D2 R8 mitigation route)
related: [BUG-010, BUG-011, BUG-012]
---

# BUG-013 — Next.js dev proxy needs Bearer auto-injection for browser-native requests

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged Sev3;**Chris chat-acknowledged 2026-05-24** via 401 paste post-BUG-012 restart。

## 1. Symptom

BUG-012 fix shipped + backend restarted + frontend dev server unchanged。用戶 hard-refresh `/kb/sample-document-with-image-1?tab=images` → 8 個 `<img>` 仍然 placeholder。DevTools Console 全部 8 個 request:

```
GET http://localhost:3001/api/backend/kb/sample-document-with-image-1/screenshots/<sha>.png 401 (Unauthorized)
```

URL shape 而家 same-origin(BUG-012 fix landed),理論上 cookie 應該自動 attach,但**仍 401**。

## 2. Reproduction Steps

1. Backend running with mock-auth(`feature_auth_mock=true`)
2. Frontend running `pnpm dev` on `localhost:3001`
3. User visits any page that uses auth(eg. `/kb/<id>?tab=images`)
4. Page renders OK because `apiClient.kb.listImages()` adds `Authorization: Bearer dev-token` explicitly to fetch — `/images` endpoint 200, `<ImageCard>` receives `url: /api/backend/kb/.../screenshots/<sha>.png`(BUG-012 same-origin shape)
5. `<img src={img.url}>` fires browser-native GET — **NO Authorization header**(browser `<img>` cannot add custom headers)+ **NO `ekp_session` cookie**(per Mock-mode reality — see §6)
6. Next.js proxy forwards to backend with no auth → backend `get_current_user` 401

**Reproduction reliability**:Always(deterministic — mock mode by design has no cookie path)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| `<img>` GET via Next.js proxy(dev mode)| 200 + image bytes | 401 |
| Auth mechanism for browser-native requests | Auto-inject Bearer at proxy layer | No injection → no auth header reaches backend |

## 4. Impact

**Identical user impact as BUG-012** — image visibility broken in KB Images tab + future chat citation `<ImageGallery>`。BUG-012 fix shifted root cause one layer over but did not complete the auth chain for browser-native dev-mode requests。

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:image visibility regression only;text retrieval / Gate 1 / chat 文字 unaffected。No data loss、no security regression(fix 仍 dev-only,production isDev=false → no injection → unchanged behaviour)。同 BUG-010/011/012 tier。

## 6. Initial Diagnosis(root cause confirmed)

W25 D1+ diagnostic chain post-BUG-012 deploy:

- **Layer 1 — frontend code review**:`frontend/lib/auth/mock_msal.ts` `getMockBearer()` hardcodes a `DEV_BEARER` constant in-memory;**never calls `/auth/login`**;therefore the backend `set_session_cookies` flow(`api/auth/cookies.py:38-67`)**never runs in mock mode**。Browser has no `ekp_session` cookie。
- **Layer 2 — frontend apiClient behaviour**:`frontend/lib/api/*` modules go through `api-client.ts` which adds `Authorization: Bearer <DEV_BEARER>` to every fetch in mock mode。This explains why `/images` endpoint(via apiClient)succeeds:Bearer-authenticated。
- **Layer 3 — `<img>` element constraint**:browsers do NOT allow custom headers on `<img>` element;only cookies + a few standard headers go on browser-native subresource requests。In mock mode without cookie:`<img>` has zero auth signal。

**Probe evidence**(this session):

```
GET /api/backend/kb/.../screenshots/<sha>.png(no auth header)→ 401
GET /api/backend/kb/.../screenshots/<sha>.png(with Bearer dev-token)→ 200 + 513068 bytes
```

**Cookie auth path mock-mode-completion** would also be sufficient(see Alternatives Considered),but proxy-injection is more surgical for the immediate Tier 1 dev-only need。

**Fix shape**:Add 3-line conditional Bearer injection in `frontend/app/api/backend/[...path]/route.ts`:

```typescript
// W25 BUG-013 — mock dev mode: <img> / <video> / browser-native requests
// can't add Authorization header themselves, and mock mode never sets the
// ekp_session cookie (mock_msal.ts hardcodes a Bearer in-memory, no login
// endpoint round-trip). Auto-inject the dev Bearer on the way through the
// server-side proxy so browser-native subresources still authenticate.
// Production (isDev=false): no injection — real MSAL Bearer / cookie flow
// through unchanged.
if (isDev && !headers['authorization']) {
  headers['authorization'] = `Bearer ${process.env.NEXT_PUBLIC_AUTH_MOCK_BEARER ?? 'dev-token'}`;
}
```

Placement:after the existing `req.headers.forEach(...)` HOP_HEADERS filter,before the upstream request build。

非架構 / vendor / storage-layout 改動(純 dev-only proxy auth-flow tweak)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix(checklist preview)

- [ ] Root cause confirmed:mock mode never sets `ekp_session` cookie → `<img>` browser-native request has neither Bearer nor cookie → 401
- [ ] **Fix** — `frontend/app/api/backend/[...path]/route.ts`:add `if (isDev && !headers['authorization']) headers['authorization'] = Bearer ${dev token}` after HOP_HEADERS filter
- [ ] Tests — N/A(Next.js route handler tested via integration through `pnpm dev` server,no unit test infra existing for catch-all proxy route file)
- [ ] Verify gates — Next.js HMR pick up file change auto;backend unchanged
- [ ] Runtime verify — user hard refresh `/kb/<kb_id>?tab=images` → 8 real thumbnails + DevTools Network 8 × 200(non-401)

## 8. Alternatives Considered

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| 1 | Mock-mode also sets `ekp_session` cookie via dedicated `/auth/dev/init-session` endpoint | Architecturally cleanest(cookie path uniformity)| Backend + frontend changes(new endpoint, init wiring, users_repo session seed)~30 LOC | Rejected — more invasive than proxy injection |
| 2 | `<img crossorigin="use-credentials">` + backend CORS Allow-Credentials | Standard browser opt-in | Still requires cookie to be set(mock mode doesn't);+ CORS config | Rejected — doesn't solve mock-no-cookie reality |
| 3 | Query-param signed URL token(SAS-like)| Bypasses cookie/Bearer altogether | Tokens in URL → server logs + browser history;requires expiry logic | Rejected — non-trivial security plumbing for dev-only need |
| 4 | Frontend Image component fetches via apiClient + URL.createObjectURL | Works for ALL auth modes(mock + self-register + MSAL)without backend change | Significant frontend complexity;state management per image | Rejected — way over-engineered for this Tier 1 scope |
| 5 | **Next.js proxy auto-inject dev Bearer**(this ADR)| 3-line surgical;dev-only;unblock all `<img>` paths at once;no backend change | Slight philosophical concern about proxy adding auth user didn't explicitly send | **Selected** — best surgical / impact ratio |

## 9. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-24 | Initial triage(Sev3)— BUG-012 fix shifted root cause one layer over;`<img>` still 401 because mock mode has no cookie + browser cannot add Bearer | DevTools Network 8/8 401 post-BUG-012 deploy + restart | Chris(chat-confirm 2026-05-24)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
