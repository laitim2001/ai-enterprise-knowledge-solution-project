# ADR-0062: 全 app `.content` responsive 最大寬度 — 超寬螢幕內容居中限 1600px(padding-clamp)

**Date**: 2026-06-15
**Status**: Accepted
**Approver**: 用戶(2026-06-15 AskUserQuestion 揀「全 app 加最大寬度 + 居中」)

## Context

ADR-0061 修 doc-detail「縮到中間」時,我**誤解方向** —— 把 doc-detail 從全站唯一有寬度上限的頁
(`content-wide` = max-width 1600px 置中)改成無上限貼邊。用戶隨後在 `/kb` 發現:「貼邊撐滿」本身
才是問題 —— 超寬螢幕(ultrawide)上內容拉到最右、KB 卡片 grid 排到 5+ 列、「整個頁面沒有了
responsive 效果」。

實測根因(2560px viewport):
- 全站**所有**頁面用純 `.content`(`flex: 1`,**無 max-width**)→ 內容無限撐滿可用寬度(2312px)。
- doc-detail 原本的 `content-wide`(1600px 上限)反而是全站唯一對超寬螢幕做了寬度約束的頁;ADR-0061
  把它也移除,等於全站都失去上限。

用戶真正訴求:整個 app 內容要有 **responsive 最大寬度**,超寬螢幕優雅居中,而非無腦撐滿。這是全 app
layout philosophy 改動(影響所有用 `.content` 的頁面 + 偏離所有 mockup 的純 `.content`)→ 觸 H1 + H7。
用戶 STOP+ask 後揀「全 app 加最大寬度 + 居中」(preview 顯示 1600px)。

## Decision

`.content` 左右 padding 改用 clamp 技巧(top 24 / bottom 40 不變):

```css
.content { padding: 24px max(28px, (100% - 1600px) / 2) 40px; }
```

- 可用寬 > 1600px → 左右 padding = `(100% - 1600px) / 2` → 內容區 **1600px 居中**。
- 可用寬 ≤ 1600px → 左右 padding = `28px`(原最小值)→ 內容區**撐滿**(窄螢幕零影響)。

**為何用 padding-clamp 而非 `max-width` + `margin: auto`**:`.content` 是 flex item(`.main` flex
container 內,`flex: 1 1 0%`)。實測 `max-width: 1600px; margin: 0 auto` → auto margin 吸收剩餘空間令
flex-grow 失效,寬度縮到**內容自然寬度 1008px**(非 1600)。padding-clamp **不破壞 flex/scroll**
(scrollbar 仍在容器最右),實測內容區精準 **1600px 居中**。

- `1600px` = 沿用既有 `content-wide` 值;單一位置可調(兩個 CSS 檔同一行),用戶若嫌窄/寬一行改。
- **影響範圍**:所有用 `.content` 的頁面(dashboard / kb / kb/[id] / docs/[docId] / eval / traces /
  settings / users / upload / kb/new)統一居中。**chat 用獨立 3-pane grid**(`height: calc(100vh -
  topbar)`,不用 `.content`)→ 保持全寬沉浸式對話,不受影響。
- **doc-detail** 維持 `.content`(ADR-0061 已改),現經全站上限自動居中 = 視覺回到 ~1600px 但全站一致;
  ADR-0061 的 className 統一仍成立(**不 revert**)。
- 同步改 **canonical** `references/design-mockups/styles.css:332` + **verbatim copy**
  `frontend/app/styles-mockup.css`(per DESIGN_SYSTEM.md §7.2 class change)。

## Alternatives Considered

- **`max-width` + `margin: auto` on `.content`** — rejected:flex item + auto margin 破壞 flex-grow,
  寬度縮到內容自然寬度(實測 1008px 非 1600)。
- **逐頁加 `content-wide` class** — rejected:要改 10+ 頁面 + 10+ mockup,易漏 + drift;改 `.content`
  一處全站一致。
- **每頁加 inner max-width wrapper** — rejected:要改所有頁面 DOM 結構,大量改動。
- **維持貼邊撐滿(不改)** — rejected:用戶明確要 responsive 上限。
- **用 CSS 變數 `--content-max`** — considered:既有 `content-wide`/`content-narrow` 都 hardcode
  1600/1280,為一致 + simplicity 維持 hardcode;可調性 = 改一行。

## Consequences

- **Positive**:全站 layout 一致 + responsive 上限;超寬螢幕內容居中不拉到邊;窄螢幕自動撐滿;
  chat 全寬不受影響;單一 CSS 位置可調;不破壞 flex/scroll。
- **Negative**:正式偏離所有頁面 mockup 的純 `.content`(已同步更新 canonical + copy 消解 drift);
  1600px 是 judgment 值,用戶若嫌窄/寬可一行調整。
- **Neutral**:純 CSS;零 backend / schema 影響;完全可逆。

## References

- ADR-0061(doc-detail content-width-align — 本 ADR amends 其「貼邊」方向;doc-detail 仍用 `.content`,
  改經全站上限居中)
- ADR-0024(unified application shell IA — 全站一致性精神)
- `frontend/app/styles-mockup.css` `.content`(307-) + `references/design-mockups/styles.css:332`
- DESIGN_SYSTEM.md §7.2(class change 5-step)/ §7.3(drift incident log)
- CLAUDE.md §5.1 H1 / §5.7 H7 / §3.2.1(mockup single source of truth)
