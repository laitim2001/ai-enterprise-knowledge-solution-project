# W72 — 文件畫像引擎 checklist

> Atomic items per `plan.md` §2 交付物。每日 tick;`[ ]`→`[x]`,唔可刪未勾項(改 scope 標 🚧 + reason)。

## F1 — profiler 核心(schema + 信號抽取 + classify v3 + 信心度)

- [x] `ProfileResult` dataclass — `profile` Literal(P1_sop_imgdense / P1_sop_text / P2_prose / P3_slide_imgdense / P3_slide_text / P4_scan_imgdense / P5_form / too_small / unknown)+ `confidence: float` + `signals: ProfileSignals` + `fallback_applied: bool`
- [x] `DocumentProfiler.profile(parser_result, source_path) → ProfileResult` 骨架
- [x] 信號抽取:ParserResult 衍生(paras / headings 數 / max depth / list_item 數 / images 數 / tables 數 + img_density / head_density / list_ratio)
- [x] tick-box / Q-marker 密度 scan(`raw_text` → `□` `★` `Qn` `Your answer:`)
- [x] classify v3:per-format(pptx→P3 細分 / PDF 唔靠 img_density)+ too_small 20 + P1 拆兩支 + P5_form + P2_prose
- [x] 信心度計算(強信號零矛盾→高 / 邊界→低)
- [x] D7 低信心 fallback(unknown / 極低信心 → `P2_prose` + `fallback_applied=True`)
- [x] mypy --strict 0 + ruff 0 (mypy `--explicit-package-bases --follow-imports=silent` exit 0;pypdfium2 無 stub → `# type: ignore[import-untyped]`)

## F2 — PDF pre-OCR 信號(pypdfium2)

- [x] `pypdfium2` per-page pass:text-layer 空比例 + 每頁字數密度(pre-OCR,秒級)
- [x] 接入 profiler PDF 分支:text-layer 空比例高 → `P4_scan_imgdense` short-circuit(**唔觸發 Docling OCR**)
- [x] born-digital PDF 分流:每頁字數低 → P3_slide / 高 + heading → P1_sop_text
- [x] 驗 scan short-circuit 唔行 Docling OCR(unit test `test_pdf_probe_real_scan_is_p4` 真 scan → P4,空 ParserResult 路徑)

## F3 — accuracy harness + H6 test

- [x] accuracy harness:真 parse 30 sample(docx/pptx Docling + PDF do_ocr=False)抽真信號(非 hardcoded);scan 用空 ParserResult + pypdfium2(`scripts/profiler_accuracy_harness.py`)
- [x] 7 份 scan 發票跑 profiler → 全判 `P4_scan_imgdense`(7/7)
- [x] accuracy ≥90% gate(扣 SMALL 噪音 content)= **34/34 = 100%**(n8n-runbook tickbox 誤判修正後)
- [x] miss 變化 vs v2 勘查記錄(R2):n8n-runbook 真 parse tickbox_d=0.188 誤搶 form;reorder tickbox→P1_sop_text 之後修正;2 剩 miss = SMALL artifact(門檻 20 副作用)
- [x] profiler unit test:classify 各分支 / 信心度 / D7 fallback / PDF pre-OCR / deterministic(`tests/test_profiler.py` 19 test;synthetic ParserResult CI-safe + 真 scan probe skipif)
- [x] pytest 綠(19 passed)+ ruff clean

## F4 — 收爐

- [ ] memory 更新(`project_per_kb_tunable_config_vision` append profiler 落地)
- [ ] closeout retro(progress.md 結尾)
- [ ] ADR-0056 段 ② render-side 交棒記錄(profiler output 契約 → routing 段消費點)
- [ ] plan.md status → closed
