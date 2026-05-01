---
component: C10
name: Chat Interface UI
catalog_ref: ../COMPONENT_CATALOG.md#c10--chat-interface-ui
spec_refs: [architecture.md §5 (chat-related views)]
status: v0-draft
last_invalidated: 2026-05-01
---

# C10 — Chat Interface UI Design Note

> **Status**:`v0-draft`(W1 D1 minimal scaffold via F3 `/page.tsx` placeholder;heavy work W3 D2 first touch)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
frontend/
├── app/
│   ├── page.tsx                      ← Chat root (W3 D2 wire)
│   │                                    OR /chat/page.tsx if /admin separate
│   └── chat/                         ← (option B) dedicated /chat path
│       └── [conversation_id]?       ← (Beta+ history)
├── components/
│   ├── chat/
│   │   ├── ChatRoot.tsx              ← Vercel AI SDK useChat() wrapper
│   │   ├── MessageList.tsx           ← scrollable history(virtualized W4 if needed)
│   │   ├── MessageBubble.tsx         ← user / assistant message render
│   │   ├── ChatInput.tsx             ← textarea + submit(send to /query)
│   │   ├── CitationInline.tsx        ← inline footnote marker [^1]
│   │   ├── CitationSidebar.tsx       ← source list + screenshot preview
│   │   ├── StreamingIndicator.tsx    ← typing cursor / progress
│   │   └── EmptyState.tsx            ← initial prompt suggestions
│   └── shared/                       ← AppShell + ThemeProvider(同 C09 share)
└── lib/
    ├── api-client.ts                 ← (shared with C09)POST /query
    └── chat/
        ├── parse-citations.ts        ← extract [^N] markers + map to source
        └── format-streaming.ts       ← incremental SSE chunk handling
```

### Conversation flow

```
User types query
    │
    ▼
ChatInput onSubmit → useChat({ api: '/api/query' }).append()
    │
    ▼
Vercel AI SDK 自動 POST /query stream=true (SSE)
    │
    ▼
C08 API Gateway → C04 Retrieval → C05 Generation (streaming)
    │
    ├─► SSE chunk: {"type":"token", "text":"…"} ← incremental render in MessageBubble
    ├─► SSE chunk: {"type":"citation", "id":"[^1]", "chunk_id":"...", "source_url":"..."} ← CitationInline + sidebar update
    └─► SSE chunk: {"type":"done", "trace_id":"..."} ← stop StreamingIndicator
```

---

## 2. Key Interfaces

### Inputs
- User typed query text(string)
- (Beta+)conversation history scroll back

### Outputs
- Streamed assistant response with inline citations
- Sidebar source list with chunk excerpt + screenshot preview(when available)
- Trace ID link to C09 debug trace viewer(W4)

### Side effects
- POST `/query` SSE stream → C08
- (Beta+)POST `/feedback` thumbs up/down → C06
- Browser localStorage:conversation history(if Beta+ persistence)

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Vercel AI SDK `useChat()` over custom WebSocket / SSE** | Battle-tested SSE handling,auto retry,ergonomic React API。Reduce custom stream parsing code 80% |
| **SSE over WebSocket** | One-way server → client(no need bidirectional);simpler;works through corp proxy / load balancers more reliably than WS |
| **Inline citation `[^N]` + sidebar source list** | Standard pattern(perplexity / chatgpt search style);footnote marker hover/click → highlight sidebar entry |
| **Shared design tokens with C09**(`lib/theming/tokens.ts`)| Cohesive brand;single source for color/spacing/typography |
| **No conversation persistence W1-W6**(stateless per session)| Beta+ scope per spec §5;localStorage history Beta+;server-side persistence Tier 2 multi-user |
| **Citation render = clickable link to chunk inspector**(C09 view 6) | Cross-link verification;user can drill into source |
| **Empty state with suggested prompts**(W4 polish) | Reduce blank-canvas friction;show 3-5 example queries based on KB |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **SSE connection drop mid-stream** | Vercel AI SDK auto-retry;UI shows "重試中..." indicator;若 final fail → error toast + "重新發送" CTA |
| **Citation hallucination**(LLM cites chunk_id 不存在 of retrieved set)| Citation render highlights as "⚠ unverified";link still works but flagged。Backend C05 should validate citations against retrieved chunks before stream |
| **Empty response**(LLM refusal due to low confidence per CRAG)| Render refusal message + suggestion("請嘗試 rephrase 或聯絡 Admin")|
| **Rate limit exceeded(W7+ 429)** | Toast "請稍候 X 秒"(retry-after header);disable input temporarily |
| **Auth expired mid-conversation(W7+)** | Silent token refresh;若 fail → save draft + redirect to login |
| **Long response(> 30s typical)** | Streaming indicator continuous;timeout at 60s safety;若 timeout abort + error toast |
| **Browser tab inactive**(SSE may suspend) | On tab visibility change → check connection state,reconnect if needed |
| **User submits while streaming previous** | Disable input until stream done OR queue / abort current per UX choice(默認 disable) |

---

## 5. Performance Characteristics

| Metric | Target | Notes |
|---|---|---|
| **Time-to-first-token(TTFT)** | **< 2s P95** | Critical UX metric;dominated by C04 + C05 latency |
| **Full response time** | < 30s typical;< 60s timeout | Includes CRAG iterations(W4) |
| **Token streaming rate** | > 10 tokens/sec | If lower,perceived as "slow typing" |
| **Citation render lag** | < 100ms after token receive | Local DOM update |
| **Initial page load** | < 1s P95 | Same SSG/SSR strategy as C09 |
| **Memory for long conversations** | virtualize > 100 messages(W4 if needed) | react-window 或 tanstack-virtual |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Component tests**(MessageBubble, CitationInline, ChatInput)| Vitest + RTL | W3 D2 |
| **Integration test**(useChat mock SSE stream) | Vitest with mock fetch + ReadableStream | W3 D3 |
| **Citation parsing unit test** | parse-citations.ts:input markdown → expected citation array | W3 D2 |
| **E2E streaming smoke**(Playwright + real backend)| Type query → assert tokens stream + citations render | W4 末 |
| **Long conversation perf** | 100+ messages → virtualization smooth scroll | W5 if needed |
| **Network resilience** | Throttle / drop SSE → assert retry behavior | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C10 evolution |
|---|---|
| **Conversation history**(Beta+) | localStorage W7;server-side persistence Tier 2 multi-user |
| **Feedback widget**(thumbs up/down) | `<FeedbackBar />` component;POST /feedback to C06 |
| **Conversation share**(URL with conversation_id) | Server-side persistence required(Tier 2);redacted view of public-shared conversation |
| **Voice input / output**(accessibility + multi-modal) | Web Speech API for input;TTS for output;Tier 2 multi-modal |
| **Multi-language**(JP / ZH per Tier 2) | Locale detection + per-locale prompt engineering;language-aware citation render |
| **Multi-agent visualization**(Tier 2 L4+ orchestration) | Show agent thinking steps(retrieval / reflection / synthesis)as collapsible sub-traces |
| **Adaptive UI based on user role** | Power-user gets advanced settings(top_k tuning, model picker);End-user gets simpler view |

---

## 8. Open Items / TODO

- [ ] **W3 D2 ChatRoot scaffold** + Vercel AI SDK install
- [ ] **W3 D2 SSE wire** to C08 `/query` streaming endpoint
- [ ] **W3 D3 CitationInline + Sidebar** with source link
- [ ] **W3 D5 streaming smoke E2E**(manual + Playwright)
- [ ] **W4 polish empty state** with suggested prompts
- [ ] **W4 citation hallucination flag** rendering
- [ ] **W7+ feedback widget** wire to /feedback
- [ ] **Decision pending**:`/page.tsx` 變 chat root **或** keep landing `/admin` redirect + chat at `/chat`?(W3 D2 decide based on UX research)

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c10--chat-interface-ui`](../COMPONENT_CATALOG.md#c10--chat-interface-ui)
- Spec: `architecture.md §5`(chat-related views)
- Skeleton commit: `7589110`(W1 D1 placeholder)
- Cross-component: consumes C08 streaming endpoint;shares C09 design tokens
