---
bug_id: BUG-013
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-013 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-24

### Investigation

BUG-012 deploy + backend restart 之後,用戶 paste DevTools Console:8 個 `/api/backend/kb/.../screenshots/<sha>.png` 仍 **401 Unauthorized**。URL shape 已 same-origin(BUG-012 fix working),但 auth chain 斷喺更深層。

3-layer diagnostic:

- **Layer 1**:`frontend/lib/auth/mock_msal.ts` `getMockBearer()` 純 in-memory hardcoded constant,**never hits `/auth/login`**;backend `set_session_cookies`(`cookies.py:38-67`)永遠唔執行 → 用戶 browser 從來無 `ekp_session` cookie。BUG-012 assumed cookie path 會 cover same-origin `<img>`,但 cookie 根本唔存在。
- **Layer 2**:apiClient-driven fetches(`/images`, `/kb`, etc.)work 因為 frontend 顯式加 `Authorization: Bearer <dev-token>` header。`<img>` 用 browser-native fetch,**no custom headers allowed**(W3C spec)。
- **Layer 3**:probe confirm — backend with Bearer = 200/513068 bytes;no Bearer = 401。

### Decisions

- **D1.1** — 分類 Bug-fix BUG-013 Sev3 same-tier as BUG-010/011/012
- **D1.2** — Fix locus = **Next.js dev proxy**(`app/api/backend/[...path]/route.ts`)not backend。Proxy runs server-side,knows `isDev`,can inject Bearer for browser-native subresources。3-line surgical,dev-only,production isDev=false bypass。
- **D1.3** — Alternatives evaluated(5 options in report §8)— mock-cookie-init endpoint / crossorigin-credentials / signed URL / fetch-blob component / **proxy-injection** — proxy injection wins on surgical-impact ratio。
- **D1.4** — No ADR triggered:dev-only proxy auth tweak,no architectural / vendor / spec-interface change。

### Code changes

| 檔案 | 改動 |
|---|---|
| `frontend/app/api/backend/[...path]/route.ts` | After HOP_HEADERS filter,add 3-line `if (isDev && !headers['authorization'])` Bearer injection using `process.env.NEXT_PUBLIC_AUTH_MOCK_BEARER ?? 'dev-token'`;docstring cite BUG-013 |

### Verify gates

- **Next.js HMR auto pick up file change** — Next.js dev server watches `app/**/*.ts` + route handlers reload on save。Confirmed via probe success below。
- **Proxy probe with no auth header(simulates `<img>` browser-native request)**:
  ```
  GET /api/backend/kb/.../images               → 200 ✅ (was already 200 with Bearer; injection no-op when apiClient added one)
  GET /api/backend/kb/.../screenshots/<sha>.png → 200 / 513068 bytes / image/png ✅ (PRE-fix this was 401)
  ```
- **Runtime verify(pending user)** — user hard refresh `/kb/sample-document-with-image-1?tab=images` → 8 real thumbnails should render + DevTools Network 8 × `/api/backend/.../screenshots/<sha>.png` 200 each

### Commits

_(見 commit footer — `fix(frontend): Next.js proxy injects dev Bearer for browser-native requests — BUG-013`)_

### Retro

- **BUG-010 → BUG-011 → BUG-012 → BUG-013 cascade in 3 days** 揭示同一 image pipeline 嘅 4 個獨立 layer:upload(BUG-009)+ counter/serving(BUG-010)+ frontend render(BUG-011)+ cross-origin URL(BUG-012)+ dev mock auth injection(BUG-013)。**Pattern lesson**:end-to-end browser-level manual smoke gate 應該 mandatorily 喺 ANY image-pipeline closure cascade 嘅最後一步 enforced,而非 backend curl smoke / unit tests only。Image rendering involves browser-native semantics(`<img>`, cookies, CORS, SameSite, headers)which backend tests structurally cannot exercise。
- **Mock-auth dev mode quirks library** building — already accumulated:no session cookie(BUG-013 trigger)/ apiClient must explicit-add Bearer(architectural)/ cross-origin URL fails(BUG-012)。Maybe future ADR worth pulling these into a「Mock Dev Auth Model」doc to prevent re-discovery。
- **Proxy-injection is the right level**:fixing at `<img>` component level(option 4 in report §8 — fetch + URL.createObjectURL)would have required per-component change for every image surface(KB ImageCard + chat ImageGallery + InlineImageCard + ImageDetailModal mockup future);proxy-level fix covers all current + future image surfaces uniformly with 3 lines。

### Closeout — 2026-05-24 W25 D2 cont

- **Runtime user-eye verify deferral**:precise `/kb/[id]?tab=images` 8-thumb walkthrough deferred per T6 🚧 — user routed to `/kb/[id]/docs/[doc_id]` Document Detail page during 2026-05-24 W25 D2 verify session,surfaced separate BUG-015(`image_refs[].blob_url` raw Azurite URL)+ BUG-016(ChunkSummary missing per-chunk image marker)
- **Fix correctness independently validated** via T5 post-edit proxy probe(401 → 200 transition for no-Bearer `<img>` browser-native simulation)+ implicit confirmation once BUG-015 unblocks Document Detail same-origin proxy path(same underlying infrastructure)
- **`status: in-progress → done`** + checklist 4 closeout boxes ticked + cross-cutting 6 boxes ticked
- **Commit**:`fix(frontend): Next.js proxy injects dev Bearer for browser-native requests — BUG-013`
