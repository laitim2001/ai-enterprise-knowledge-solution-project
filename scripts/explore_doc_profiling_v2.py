"""W72-prep 勘查 v2(throwaway,非 production):rule-based profiling v2 規則驗證。

reuse v1(explore_doc_profiling.py)已 parse 嘅 30 份文件 signals(parse 結果固定,
classify 係純函數 → 唔需要重 parse,避免 v1 PDF OCR 35 分鐘成本)。

v2 四項修正(全部基於 v1 實證 finding):
  ① per-format 信號:pptx 一律 P3;PDF 唔靠 img_density(Docling PDF 唔抽 embedded image)
  ② P1 拆 imgdense / text 兩支:純文字步驟型 SOP(procedure / runbook)唔靠圖
  ③ 加 P5_form 類別:無/極少 heading + 無 list + 無圖
  ④ too_small 過濾(<25 paras 噪音,pptx 豁免)

加手標 ground truth(EXPECTED)自動算命中率 + 框出 miss(= LLM tie-break 候選)。
"""

from __future__ import annotations

from collections import Counter

# v1 parse 出嘅固定 signals(直接由 explore_doc_profiling.py 輸出表抄入,reuse 唔重 parse)
# (name, format, paras, headings, depth, lists, images, img_density, head_density, list_ratio)
SIGNALS = [
    ("AI demonstration_20260329 (4).pdf", "pdf", 67, 28, 1, 17, 0, 0.0, 0.418, 0.254),
    ("AI-Governance-Guideline-for-Employees.docx", "docx", 219, 25, 2, 18, 0, 0.0, 0.114, 0.082),
    ("AI-Governance-Procedure.pdf", "pdf", 242, 86, 1, 77, 0, 0.0, 0.355, 0.318),
    ("AI_Automation_Team_Update_EN.pptx", "pptx", 8, 2, 1, 0, 0, 0.0, 0.25, 0.0),
    ("AI_Project_Registration_Form.docx", "docx", 84, 0, 0, 0, 0, 0.0, 0.0, 0.0),
    ("Day1_Master_Deck_v2.pptx", "pptx", 643, 29, 1, 0, 0, 0.0, 0.045, 0.0),
    ("DCE_Integration_Platform_Implementation_Plan.docx", "docx", 630, 120, 3, 0, 8, 0.013, 0.19, 0.0),
    ("DigitalMarketing_DCE.pptx", "pptx", 112, 7, 1, 0, 0, 0.0, 0.062, 0.0),
    ("DRIVE_0601(AR)_AR Management.docx", "docx", 585, 50, 4, 354, 253, 0.432, 0.085, 0.605),
    ("DRIVE_0602(AP)_AP Management.docx", "docx", 408, 42, 4, 217, 248, 0.608, 0.103, 0.532),
    ("DRIVE_0603(FA)_Fixed Asset.docx", "docx", 566, 44, 4, 367, 223, 0.394, 0.078, 0.648),
    ("DRIVE_0604(CB)_Cash and Bank.docx", "docx", 190, 20, 4, 120, 58, 0.305, 0.105, 0.632),
    ("DRIVE_0605(GL)_General Ledger.docx", "docx", 609, 50, 4, 389, 213, 0.35, 0.082, 0.639),
    ("DRIVE_0606(BM)_Budget Management.docx", "docx", 93, 11, 4, 48, 23, 0.247, 0.118, 0.516),
    ("ekp-smoke-test-v2.docx", "docx", 23, 12, 2, 0, 0, 0.0, 0.522, 0.0),
    ("ekp-smoke-test.docx", "docx", 7, 3, 2, 0, 0, 0.0, 0.429, 0.0),
    ("ekp-smoke-test.pdf", "pdf", 6, 1, 1, 0, 0, 0.0, 0.167, 0.0),
    ("ekp-smoke-test.pptx", "pptx", 9, 6, 2, 0, 0, 0.0, 0.667, 0.0),
    ("FY26 BP - DCE - Customer Platform.pptx", "pptx", 237, 18, 2, 0, 39, 0.165, 0.076, 0.0),
    ("FY26 BP Template V1.pptx", "pptx", 83, 14, 2, 0, 7, 0.084, 0.169, 0.0),
    ("FY26_Budget_Proposal_v2.pptx", "pptx", 148, 9, 1, 0, 12, 0.081, 0.061, 0.0),
    ("How_to_Approach_Automation.pptx", "pptx", 60, 1, 1, 0, 0, 0.0, 0.017, 0.0),
    ("IT_Automation_Priority_Matrix.pptx", "pptx", 346, 11, 1, 0, 0, 0.0, 0.032, 0.0),
    ("n8n-PDT-Upgrade-Runbook.docx", "docx", 292, 14, 2, 45, 0, 0.0, 0.048, 0.154),
    ("Nagarro_Alignment_FY26.pptx", "pptx", 132, 4, 1, 0, 25, 0.189, 0.03, 0.0),
    ("Session1_AI_Governance_EN.pptx", "pptx", 431, 19, 1, 0, 17, 0.039, 0.044, 0.0),
    ("Session1_AI_Governance_ZH.pptx", "pptx", 431, 19, 1, 0, 17, 0.039, 0.044, 0.0),
    ("Virtual_Boss_Questionnaire.docx", "docx", 91, 6, 1, 0, 0, 0.0, 0.066, 0.0),
    ("Virtual_Boss_Introduction_and_Brief.docx", "docx", 21, 3, 2, 3, 0, 0.0, 0.143, 0.143),
    ("Workshop_Followup_Slides.pptx", "pptx", 179, 5, 1, 0, 0, 0.0, 0.028, 0.0),
]

# 手標 ground truth(人類判斷嘅正確 family)
EXPECTED = {
    "AI demonstration_20260329 (4).pdf": "P3",          # PDF demo deck — 預期 rule 會撞 SOP
    "AI-Governance-Guideline-for-Employees.docx": "P2",
    "AI-Governance-Procedure.pdf": "P1",                # 純文字 procedure 步驟
    "AI_Automation_Team_Update_EN.pptx": "P3",
    "AI_Project_Registration_Form.docx": "FORM",
    "Day1_Master_Deck_v2.pptx": "P3",
    "DCE_Integration_Platform_Implementation_Plan.docx": "P2",
    "DigitalMarketing_DCE.pptx": "P3",
    "DRIVE_0601(AR)_AR Management.docx": "P1",
    "DRIVE_0602(AP)_AP Management.docx": "P1",
    "DRIVE_0603(FA)_Fixed Asset.docx": "P1",
    "DRIVE_0604(CB)_Cash and Bank.docx": "P1",
    "DRIVE_0605(GL)_General Ledger.docx": "P1",
    "DRIVE_0606(BM)_Budget Management.docx": "P1",
    "ekp-smoke-test-v2.docx": "SMALL",
    "ekp-smoke-test.docx": "SMALL",
    "ekp-smoke-test.pdf": "SMALL",
    "ekp-smoke-test.pptx": "P3",
    "FY26 BP - DCE - Customer Platform.pptx": "P3",
    "FY26 BP Template V1.pptx": "P3",
    "FY26_Budget_Proposal_v2.pptx": "P3",
    "How_to_Approach_Automation.pptx": "P3",
    "IT_Automation_Priority_Matrix.pptx": "P3",
    "n8n-PDT-Upgrade-Runbook.docx": "P1",               # 純文字 runbook 步驟
    "Nagarro_Alignment_FY26.pptx": "P3",
    "Session1_AI_Governance_EN.pptx": "P3",
    "Session1_AI_Governance_ZH.pptx": "P3",
    "Virtual_Boss_Questionnaire.docx": "FORM",          # 問卷 — 預期 rule 會撞 prose
    "Virtual_Boss_Introduction_and_Brief.docx": "P2",   # 短 intro — 預期 rule 會撞 too_small
    "Workshop_Followup_Slides.pptx": "P3",
}


def classify_v2(fmt, P, H, depth, L, I, img_d, head_d, list_r):
    # pptx 一律 P3(豁免 too_small);再按圖密度細分子型(影響後續 image 流程)
    if fmt == "pptx":
        return f"P3_slide_{'imgdense' if img_d >= 0.12 else 'text'}"
    # 噪音過濾(非 pptx)
    if P < 25:
        return "too_small"
    # 表單/問卷:無 / 極少 heading + 無 list + 無圖
    if H <= 1 and L == 0 and I == 0:
        return "P5_form"
    # P1 圖密 SOP:深結構 + 圖密 + 步驟列表(per-format:docx 主)
    if depth >= 3 and img_d >= 0.15 and list_r >= 0.3:
        return "P1_sop_imgdense"
    # P1 純文字 SOP:步驟列表密 + heading 多(唔靠圖 → PDF / 純文字 docx 都接到)
    if list_r >= 0.12 and H >= 10:
        return "P1_sop_text"
    # P2 散文:有結構 heading 但 list 少、圖少
    if head_d >= 0.05 and list_r < 0.12:
        return "P2_prose"
    return "unknown"


def fam(label):
    if label.startswith("P1"):
        return "P1"
    if label.startswith("P2"):
        return "P2"
    if label.startswith("P3"):
        return "P3"
    if label.startswith("P5_form"):
        return "FORM"
    if label == "too_small":
        return "SMALL"
    return "UNKNOWN"


def main():
    print("| 文件 | v2 label | family | expected | 結果 |")
    print("|---|---|---|---|---|")
    hit = miss = 0
    misses = []
    for row in SIGNALS:
        name, fmt, P, H, depth, L, I, img_d, head_d, list_r = row
        label = classify_v2(fmt, P, H, depth, L, I, img_d, head_d, list_r)
        f = fam(label)
        exp = EXPECTED.get(name, "?")
        ok = f == exp
        if ok:
            hit += 1
            verdict = "✅"
        else:
            miss += 1
            verdict = "❌ MISS"
            misses.append((name, label, f, exp))
        short = name if len(name) <= 44 else name[:41] + "..."
        print(f"| {short} | {label} | {f} | {exp} | {verdict} |")

    total = hit + miss
    print(f"\n=== 命中率 ===")
    print(f"全部:{hit}/{total} = {hit / total * 100:.1f}%")
    # 扣 SMALL 噪音後(真實內容文件)
    content = [r for r in SIGNALS if EXPECTED.get(r[0]) != "SMALL"]
    c_hit = sum(
        1 for r in content
        if fam(classify_v2(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])) == EXPECTED[r[0]]
    )
    print(f"扣 too_small 噪音(真實內容文件):{c_hit}/{len(content)} = {c_hit / len(content) * 100:.1f}%")
    print(f"v1 baseline 約 70% → v2")

    print(f"\n=== MISS(= LLM tie-break 候選)===")
    for name, label, f, exp in misses:
        print(f"  {name}: rule 判 {f}({label})vs 人判 {exp}")

    print(f"\n=== v2 profile 分佈 ===")
    dist = Counter(classify_v2(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]) for r in SIGNALS)
    for p, c in dist.most_common():
        print(f"  {p}: {c}")


if __name__ == "__main__":
    main()
