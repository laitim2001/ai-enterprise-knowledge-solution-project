# W103 — Checklist(i18n en/zh UI chrome 雙語)

> 對應 `plan.md` §2 Deliverables + §3 Acceptance Criteria。逐項 tick;🚧 defer 需 reason + target。

## F1 — Tier 邊界 amendment(首)✅
- [x] F1.1 讀 architecture.md 現狀(§2.2 / §5.0 / §11.1 / line 17 四處定位)
- [x] F1.2 architecture.md §2.2 + §5.0 + §11.1 + line 8 把 Multi-language(en/zh)移出 Tier 2(JP + content/RAG 翻譯留 Tier 2)—— **採 inline-tagged + doc-version-held convention,非 version bump**(R3 deviation,對齊 ADR-0022/0023/0024)
- [x] F1.3 CLAUDE.md §5.4 H4 list 同步移除 en/zh(JP / content 翻譯留低)
- [x] F1.4 ADR-0075 §Implementation Notes 記 amendment 落地
- [x] F1.5 surface diff 畀用戶確認(2026-07-14 用戶確認 diff OK)

## F2 — next-intl 裝機 + R8 驗證
- [ ] F2.1 R8 corp-proxy 裝機探測(ADR-0017;Ricoh MITM)
- [ ] F2.2 next-intl 裝入 frontend(pnpm)
- [ ] F2.3 裝唔到 → STOP + fallback 議(記 progress)
- [ ] F2.4 版本鎖定 + package.json 記錄

## F3 — i18n 機制搭建
- [ ] F3.1 D-2 locale 機制拍板(甲 cookie / 乙 `/[locale]/` routing)— Chris 拍板
- [ ] F3.2 next-intl config + provider
- [ ] F3.3 layout.tsx lang 動態化
- [ ] F3.4 CJK font fallback(latin subset 補 CJK)
- [ ] F3.5 SSR-safe 驗(無 hydration mismatch)

## F4 — en dictionary externalize
- [ ] F4.1 en messages 骨架 + t() wiring pattern 定
- [ ] F4.2 core flow view externalize(分批:nav / dashboard / chat / kb / docs / settings / integrations / users / login)
- [ ] F4.3 CH-023 那 7 檔 externalize(已英文 hardcode → 抽 dict)
- [ ] F4.4 grep 無 en chrome hardcode 殘留(動態拼接走查)

## F5 — zh dictionary
- [ ] F5.1 Claude draft zh 初稿(全 en key 對應)
- [ ] F5.2 technical term glossary(保留英文定譯)
- [ ] F5.3 用戶校對 → 定稿

## F6 — Language toggle 啟用
- [ ] F6.1 定位 mockup disabled Language toggle 現實作位置
- [ ] F6.2 disabled → enabled + 綁 locale 切換
- [ ] F6.3 切換持久化(cookie / localStorage)+ reload 保持

## F7 — H7 design sub-gate + test
- [ ] F7.1 en 態逐 view 對齊 mockup(零回歸)
- [ ] F7.2 zh 態逐 view 走查(文字長度唔撐爆 layout)
- [ ] F7.3 Vitest 切換態 + 關鍵 view
- [ ] F7.4 tsc / eslint / build clean(碰 backend 則 ruff / mypy strict)

## F8 — 文件同步 + closeout
- [ ] F8.1 ADR-0075 impl note
- [ ] F8.2 en/zh dict 維護規則(sync 紀律,類比 DESIGN_SYSTEM.md §7)
- [ ] F8.3 user-guide language 章節(optional)
- [ ] F8.4 BACKLOG B-25 → 完成
- [ ] F8.5 closeout retro(progress.md 結尾)
