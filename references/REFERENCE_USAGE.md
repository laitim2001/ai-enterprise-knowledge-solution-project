# Reference Repository Usage Policy

> **Purpose**:本文件係 EKP project 對待第三方開源 reference repository 嘅**正式 policy**。當前主要 reference 係 [Dify](https://github.com/langgenius/dify),但同樣原則適用於將來引入嘅其他 reference repo。
>
> **Audience**:所有 contributor(包括 Claude Code)
>
> **Effective**:from W1 Day 1
>
> **Owner**:Chris(Tech Lead)

---

## 1. 核心原則

`references/` folder 嘅內容係 **read-only design reference**,**唔係** EKP codebase 一部分,**唔係** dependency。

呢個 folder 嘅 git tracking 行為:

```bash
# .gitignore 入面必須 include
references/dify/
references/DIFY_PINNED_COMMIT.txt
```

每個 dev 喺自己 local 環境 clone reference repo,**唔 commit** 入主 repo。原因:
- License 隔離(reference 嘅 license 唔污染我哋 codebase)
- Repo size 控制(Dify 自己有 ~50 萬行)
- Update 由 team explicit decision(see §6),唔自動 sync

---

## 2. Setup

### 2.1 Initial Clone(W1 Day 1)

```bash
# 喺 EKP repo root 執行
mkdir -p references && cd references

# Shallow clone(慳空間)
git clone --depth 1 https://github.com/langgenius/dify.git

# Pin commit SHA + 日期(保證 team 同 reference 同一版本)
git -C dify log -1 --format="%H %ci" > DIFY_PINNED_COMMIT.txt

cd ..

# 確認 .gitignore include 咗
grep -q "references/dify" .gitignore || cat << 'EOF' >> .gitignore

# Reference repos (read-only,not part of EKP codebase)
references/dify/
references/DIFY_PINNED_COMMIT.txt
EOF
```

### 2.2 Verify Setup

```bash
# 應該見到 Dify 嘅 file
ls references/dify/web/app/        # Next.js frontend code

# 應該見到 pinned commit
cat references/DIFY_PINNED_COMMIT.txt
```

---

## 3. Allowed Actions ✅

呢啲行為**完全合法**,鼓勵做:

### 3.1 Read for Design Inspiration

- 開 `references/dify/web/...` 入面任何 file 學佢 layout、interaction、component composition
- 截 Dify UI 嘅 screenshot 做 design discussion reference
- 讀 Dify 嘅 backend API endpoint 設計學 RESTful pattern

### 3.2 Document Pattern Adoption

當你 implement EKP component 時參考 Dify 嘅某個 pattern:

```typescript
// frontend/components/kb/document-list-table.tsx

/**
 * KB Documents table component.
 * 
 * Reference: dify/web/app/components/datasets/documents/list.tsx
 * Adopted: column structure (name / chunking mode / words / retrieval count / status)
 *          + per-row action menu pattern
 * Diverged: column ordering, custom EKP design tokens, no chat plugin column
 */
export function DocumentListTable({ ... }) { ... }
```

### 3.3 PR Comment Convention

寫 PR 時若引用 Dify pattern,**必須**喺 PR description 標明:

```markdown
## Changes
Implements `DocumentListTable` for KB detail page.

## Reference
- `dify/web/app/components/datasets/documents/list.tsx`(layout pattern only)

## Diverged from reference
- EKP design tokens(see frontend/lib/theming/tokens.ts),no Dify color palette
- Added `format` icon column(EKP-specific:.docx / .pdf / .pptx)
- Removed `chat plugin` integration column(out of scope)
```

呢個 convention 有 3 個目的:
1. **Audit trail**:future reviewer / Claude Code 知道 design lineage
2. **License clarity**:明確分清楚邊啲係 inspired vs 原創
3. **Knowledge sharing**:Team member 互相學 「點抄 reference」

### 3.4 Reference Dify API Design as Inspiration

EKP 嘅 endpoint design(`docs/api-contract.md`,W2 ready)可以參考 Dify 嘅 endpoint pattern,但 schema、naming、URL 結構都應該係 EKP 自己嘅 decision。

---

## 4. Forbidden Actions ❌

呢啲行為**絕對禁止**,違者 PR 不予 merge:

### 4.1 Code Copy

- ❌ **任何形式嘅 copy-paste**(整段、半段、function、class、type definition)
- ❌ **「modified copy」**(我抄完改名、改 variable、改 typo,本質仍係 copy)
- ❌ **AST-level 抄寫**(structure 一致 + 改變量名,亦屬 derivative work)

### 4.2 Dependency Reuse

- ❌ Import / require 任何 `@dify/*` package
- ❌ Add Dify 嘅內部 lib 入 `package.json` / `pyproject.toml`
- ❌ 將 Dify 嘅 utility function copy 過嚟做「我哋自己嘅 helper」

### 4.3 Brand / Identity Reuse

- ❌ Dify logo / brand name(EKP 唔係 Dify 嘅 fork / 衍生品)
- ❌ Dify 嘅 primary color / accent color(use EKP design tokens)
- ❌ Dify 嘅 marketing copy / tagline / button text

### 4.4 Fork-style Operations

- ❌ Fork Dify repo 自己嘢 maintenance
- ❌ Submodule Dify 入主 repo
- ❌ Vendor 一個 Dify instance 然後修改

---

## 5. Why These Restrictions

### 5.1 License Reality

Dify 用 **modified Apache 2.0**,**附加 commercial restrictions**:

1. 唔可做 multi-tenant SaaS 服務 rebrand
2. 唔可移除 Dify branding(若 host Dify instance)
3. 主 license: <https://github.com/langgenius/dify/blob/main/LICENSE>

對 EKP 嘅 implication:

| 行為 | License clean? |
|---|---|
| Read-only reference + 學 idea + 自己重寫 | ✅ Clean(idea ≠ derivative work) |
| Copy 一段 Dify code 入 EKP | ❌ EKP codebase 變 derivative,inherit 限制 |
| Fork Dify + rebrand 為 EKP | ❌ 違反附加條款 |
| 將 EKP 用作 multi-tenant SaaS(future)| ⚠️ 若涉 Dify code 必違反 |

### 5.2 Scope Reality

Dify 50 萬行代碼,我哋實際需要嘅可能只有 15–20%(KB management UI、retrieval testing、document parsing UI)。Fork 全部 = inherit 200K+ 行 maintenance burden,**對 12 週 Tier 1 timeline 災難級影響**。

### 5.3 Differentiation Reality

EKP 嘅 moat 係 Drive Project domain + Azure-native stack + Ricoh integration(architecture.md §13.0)。如果 EKP 視覺 / interaction 同 Dify 一模一樣,stakeholder 自然問:「點解唔直接 self-host Dify?」呢個問題 EKP team 答唔到。

**Layout 抄、視覺自訂** 嘅 hybrid 路線,確保 EKP 視覺 distinct 之外,亦保留「我哋同 Dify 唔同」嘅 storytelling angle。

---

## 6. Update Cadence

Dify reference repo 唔自動 sync,要 explicit decision:

### 6.1 Quarterly Review

每 quarter team meeting 入面 review:
- Dify 過去 3 個月有冇重大 design change?
- 有冇新 feature 值得 study?
- 有冇 license 改動?

如決定 update:

```bash
cd references/dify
git pull origin main

cd ..
git -C dify log -1 --format="%H %ci" > DIFY_PINNED_COMMIT.txt

# Commit 嘅只係 DIFY_PINNED_COMMIT.txt 嘅 update record
# 但實際 file 仍 gitignored
```

### 6.2 Ad-hoc Update Triggers

- Dify release major version(e.g. v2.0)
- 我哋遇到設計問題 + 想睇 Dify 點解
- Security issue / license change

---

## 7. Hierarchy of Reference Sources

當實作 UI / pattern 時,**reference 優先順序**:

| Priority | Source | When to use |
|---|---|---|
| 1 | EKP `docs/architecture.md` | First check spec — 必有 authoritative answer |
| 2 | EKP existing components | Maintain 內部 consistency |
| 3 | shadcn/ui official examples | shadcn 官方 patterns,licence MIT |
| 4 | **Dify reference** | 揀 RAG / KB-specific UI pattern |
| 5 | Vercel AI SDK examples | Streaming / chat patterns |
| 6 | Other open-source RAG UI(e.g. AnythingLLM、Verba) | 補充 reference |
| 7 | 自己創新 | 前 6 條都唔啱先自己諗 |

唔係 priority 越低 = quality 越差,而係**搵到 trusted answer 嘅機率遞減**。Dify 排第 4 因為**Dify 唔係 chat tool,佢嘅 chat UI 唔係 EKP end user UI 嘅好 reference**(end user UI 應該抄 ChatGPT / Claude.ai 嘅 conversational UI pattern)。

---

## 8. Dispute Resolution

當 dev 之間 disagree 「呢個 PR 算唔算 copy」:

1. **作者**喺 PR comment 解釋自己 reasoning
2. **Reviewer** 列具體 concern(line-by-line 比對 Dify source)
3. 仍 unresolved → escalate to Tech Lead(Chris)
4. Chris 唔 sure → **default to safer side(rewrite from scratch)**

呢個 escalation path 故意嚴 —— license dispute 嘅 cost 永遠遠高於 rewrite 嘅 cost。

---

## 9. Future Reference Repos

如果 EKP 將來 add 其他 reference repo(e.g. AnythingLLM、Verba、Onyx):

1. 新 reference 加入 `references/<repo-name>/`
2. 同樣 gitignore + pin commit
3. 本文件 add 一個 sub-section 講該 repo 嘅:
   - License
   - Allowed / Forbidden 嘅 specific 範圍
   - PR comment convention example
4. 走 ADR 流程(see [`../CLAUDE.md` §5](../CLAUDE.md))

---

## 10. Quick Reference Card

```
┌────────────────────────────────────────────────────────┐
│ EKP Reference Repository Usage — Quick Reference       │
├────────────────────────────────────────────────────────┤
│ ✅ Read     ✅ Study     ✅ Adopt patterns             │
│ ✅ Document references in PR comments                   │
│ ✅ Use EKP design tokens (not Dify colors)             │
│                                                          │
│ ❌ Copy code (any size, any form)                      │
│ ❌ Import Dify packages                                 │
│ ❌ Replicate brand identity                             │
│ ❌ Fork or vendor Dify                                  │
│                                                          │
│ When in doubt → rewrite from scratch                    │
│ Disputes → escalate to Tech Lead                        │
└────────────────────────────────────────────────────────┘
```

---

## 11. Reference

- Architecture spec(reference policy):[`../docs/architecture.md` §12](../docs/architecture.md)
- CLAUDE.md hard constraint H3:[`../CLAUDE.md` §4.3](../CLAUDE.md)
- Setup guide(initial clone):[`../docs/setup.md` §4.1](../docs/setup.md)
- Dify license:<https://github.com/langgenius/dify/blob/main/LICENSE>

---

**Policy version**:1.0
**Created**:2026-04-27
**Owner**:Chris(Tech Lead)
**Effective**:from W1 Day 1
