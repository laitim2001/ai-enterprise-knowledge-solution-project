# W103 — Progress(i18n en/zh UI chrome 雙語)

> Daily progress + decisions + commits + 結尾 retro。對應 `plan.md` + `checklist.md`。

## Day 1(2026-07-14)— Kickoff

**Context**:ADR-0075 Accepted(2026-07-14 雙 approve)後開 W103 phase。承 CH-023 externalize 地基(7 檔中文洩漏止血 → 全站 source language 英文 hardcode)。翻譯來源 = Claude draft 初稿 + 用戶校對(拍板 (a))。

**已做**:
- plan.md draft → 用戶 approve → 狀態 `proposed` → `active`。
- 建 checklist.md(8 F 展開)+ progress.md kickoff。
- **F1 Tier 邊界 amendment 完成**(F1.1-F1.5 tick):architecture.md §2.2 + §5.0 + §11.1 + line 8 + CLAUDE.md §5.4 H4 —— en/zh UI chrome i18n 由 Tier 2 移出 → Tier 1;JP UI + content/RAG 翻譯留 Tier 2。ADR-0075 加 §Implementation Notes。用戶 2026-07-14 確認 diff OK。
- **F2 next-intl 裝機完成**(F2.1-F2.4 tick):R8 corp-proxy 探測通過(registry 可達,Ricoh MITM 未阻 npmjs — `pnpm view` / `add` 皆成功);next-intl **4.13.2** 裝入 frontend(peerDeps `next ^14` + `react ^18` 完全相容,無需降 v3);package.json `^4.13.2` + pnpm-lock 更新;**tsc baseline clean**(裝包無破壞 build)。

**Decision / deviation(R3)**:
- **F1.2 採 inline-tagged + doc-version-held convention,非 plan 原寫「version bump」** —— 對齊 architecture.md 既有 amendment 慣例(§3.4 ADR-0023 / §3.7 ADR-0022 / §5 ADR-0024),更接近既有 pattern(§13);doc version held v6,唔 bump v7。architecture.md line 17 歷史 note 保留(審計軌跡)。
- Language toggle 實際 disabled→enabled = F6,非 F1(F1 只確立文件層 Tier 邊界,頁面暫未有雙語切換功能)。

**Open decision(待拍板)**:
- **D-2 locale 機制** — 甲 cookie / header negotiation(URL 不變,傾向)vs 乙 `/[locale]/` routing(全 route 重構)。**留 F3 前 Chris 拍板**;F1 amendment 不受影響,已先行。

**下一步**:F3 i18n 機制搭建 —— **先拍板 D-2 locale 機制**(甲 cookie / 乙 `/[locale]/` routing)+ next-intl config/provider + `layout.tsx` lang 動態化 + CJK font fallback。

**Commits**:
- `29a0bdd` — W103 kickoff(plan approved + checklist + progress + BACKLOG B-25 進行中)。
- `2096811` — W103 F1 Tier 邊界 amendment(architecture.md §2.2/§5.0/§11.1/line 8 + CLAUDE.md §5.4 H4 + ADR-0075 impl note)。
- (見下一 commit)W103 F2 — next-intl 4.13.2 裝機(package.json + pnpm-lock)。
