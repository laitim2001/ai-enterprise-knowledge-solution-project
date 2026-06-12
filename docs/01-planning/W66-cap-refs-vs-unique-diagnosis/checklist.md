# W66 — checklist(cap 計 refs 假說診斷)

## F1 — cap 臨時抬高
- [x] backend health 200
- [x] PATCH `max_images_per_answer` 50→150(full replacement)+ readback=150(其餘欄位不變)

## F2 — mega query 直接數三個數
- [x] `/query` Q001 ×2:raw=150(撞 cap)/ unique=48(釘死)/ GT 48/65 — 兩 run 穩定
- [x] `/query` Q043 ×1:raw=150 / unique=53(+5 vs cap=60)/ GT 53/73
- [x] 無 timeout(120s 內完成,R1 未觸發)

## F3 — 復原
- [x] PATCH cap 150→50 + readback = W64 persisted 值(50/10/40 + parent_doc=False + pin=True)

## F4 — 判決 + doc-sync
- [x] 判決:強形式反證(Q001 unique 釘 48)/ Q043 部分(+5);48–53 = 收割範圍真天花板;漏網圖喺未-cite 區域(window 已證無效)
- [x] dedup-before-cap 提案降級(邊際 +0~+5,唔值得單為 recall 行 H1)— 唔提案實作
- [x] 「成功定義 = 全圖召回」決策記入 rollup + memory
- [x] plan closeout + progress retro
