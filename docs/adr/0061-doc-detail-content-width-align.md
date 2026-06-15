# ADR-0061: Doc-detail 頁面寬度對齊全站 — `content content-wide`(1600px 置中)→ `content`(貼邊)

**Date**: 2026-06-15
**Status**: Accepted(方向 amended by ADR-0062)
**Approver**: 用戶(2026-06-15 AskUserQuestion 揀「改貼邊 + 同步 mockup」)

> **Amended by ADR-0062**(同日):本 ADR 把 doc-detail 從 `content-wide`(1600px 上限)改成無上限
> 貼邊,方向理解錯誤 —— 用戶隨後發現全站「貼邊撐滿」才是真問題。ADR-0062 給**全 app** `.content`
> 加 responsive 最大寬度(1600px 居中)。doc-detail 仍用 `.content`(本 ADR 的 className 統一成立),
> 改經全站上限自動居中 → 視覺回到 ~1600px 但全站一致。本 ADR 的「貼邊」意圖被 ADR-0062 取代。

## Context

用戶報告 `/kb/[id]/docs/[docId]`(Document Detail,含 Chunk inspector + Per-doc 配置兩個 tab)
頁面「明顯縮到中間了,正常是貼近邊界的」。

根因鏈:
- `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx:118` 頁面 wrapper 用
  `<div className="content content-wide" style={{ paddingTop: 16, paddingBottom: 16 }}>`。
- `styles-mockup.css:314` `.content-wide { max-width: 1600px; margin: 0 auto; }` —— 1600px 置中。
- 全站**所有**其他 authenticated 頁面(dashboard / kb / kb/[id] / eval / traces / settings /
  users / upload / kb/new)用純 `<div className="content">`,而 `.content` **無 max-width**
  (`flex: 1` 撐滿)→ 貼邊。
- 兩個 tab 在同一個 `content content-wide` 容器內,寬度必然相同;config tab 因單欄卡片留白更明顯,
  inspector tab 的 3-pane 撐滿 1600px 看起來「滿」所以較不易察覺。

關鍵:doc-detail 的 implementation **100% 對齊 mockup** `ekp-page-doc-detail.jsx:27`
(逐字 `content content-wide` + 同一 `paddingTop/paddingBottom: 16` inline style)。其餘 mockup
頁面一律純 `.content`。換言之這個「縮中間」是 mockup 的 **deliberate design**(設計者意圖:
doc-detail 是 3-pane 密集佈局,1600px 上限限制超寬螢幕行長),**不是 bug、不是 W81 引入**。

因此「改成貼邊」= 讓 implementation **偏離 mockup**(layout philosophy 改動)→ 觸 H7(§5.7)+
H1-adjacent(§5.1「8-view layout philosophy」)→ STOP and ask。用戶在知情下揀「改貼邊 + 同步 mockup」。

## Decision

1. **doc-detail 頁面 wrapper** `content content-wide` → `content`(移除 `content-wide`,
   **保留** `paddingTop/paddingBottom: 16` inline —— 那是 doc-detail 密集佈局的特意垂直設定,
   與「貼邊」水平訴求無關,surgical 不動)。
2. **同步更新 mockup** `references/design-mockups/ekp-page-doc-detail.jsx:27` 一致移除
   `content-wide`,維持 mockup = single source of truth(避免 implementation-mockup drift)。
3. 全站 layout 自此一致:所有 authenticated 頁面 = 貼邊撐滿。

純 frontend;backend 零改動;可逆。

## Alternatives Considered

- **保持現狀(忠於 mockup 1600px 置中)** — rejected:用戶明確不滿 + doc-detail 是全站唯一例外,
  layout 不一致本身是 visual drift。
- **放寬 max-width(如 1920px)** — rejected:仍與全站「無上限貼邊」不一致,治標;且要為 doc-detail
  維持一條獨有規則。
- **只改 implementation,不同步 mockup** — rejected:會造成 mockup-implementation drift,違反
  §3.2.1 / H7 single-source-of-truth(下次有人對 mockup 做 fidelity check 會把它「修」回 content-wide)。

## Consequences

- **Positive**:全站 layout 一致(對齊 ADR-0024 unified shell 的一致性精神);對齊用戶期望;
  超寬螢幕善用橫向空間;mockup 同步更新後零 drift。
- **Negative**:doc-detail 正式偏離原 mockup 的 deliberate 1600px 設計(已透過同步更新 mockup
  消解);3-pane inspector 在超寬螢幕行長變長 —— 用戶接受此 trade-off。
- **Neutral**:single-line class 改動 + mockup 同步;backend / API / schema 零影響;完全可逆。

## References

- mockup `references/design-mockups/ekp-page-doc-detail.jsx:27`(同步更新)
- `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx:118`
- `frontend/app/styles-mockup.css:307-314`(`.content` / `.content-wide` 定義)
- ADR-0029(doc-detail 3-pane layout — 本頁佈局來源)
- ADR-0024(unified application shell IA — layout philosophy 一致性精神)
- CLAUDE.md §5.7 H7(design fidelity)/ §5.1 H1(layout philosophy)/ §3.2.1(mockup single source of truth)
