# W68 — progress(dedup-before-cap,ADR-0054)

## Day 1(2026-06-12)— kickoff

- W67 證據鏈完整 → H1 STOP+ask 提案 → 用戶 AskUserQuestion 批准「批准,实施(建議)」
  (= ADR + 改 `cap_images_per_answer` 預算計 unique + test + A/B + drive-images-1 cap 50→70)。
- R6:函數單一定義(citation_enrichment.py:111)/ caller query.py:492+645 / 現有 test fixture
  跨 citation 同 checksum → 兩個 test 喺新契約預期 fail,改寫反映新契約。
- 三件套 committed:`docs(planning): W68 dedup-before-cap kickoff`
