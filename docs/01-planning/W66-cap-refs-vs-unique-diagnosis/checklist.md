# W66 — checklist(cap 計 refs 假說診斷)

## F1 — cap 臨時抬高
- [ ] backend health 200
- [ ] PATCH `max_images_per_answer` 50→150(full replacement)+ readback=150(其餘欄位不變)

## F2 — mega query 直接數三個數
- [ ] `/query` Q001 ×2:每 run 數 raw refs(全部 embedded_images 含重複)/ unique checksum / GT hit(對 docs/eval-set-image-recall-ar.yaml Q001 65 張)
- [ ] `/query` Q043 ×1:同樣三個數(GT 73)
- [ ] timeout 出現 → 記錄 + 180s env 重試一次分離變量(R1)

## F3 — 復原
- [ ] PATCH cap 150→50 + readback 逐欄位 = W64 persisted 值(50/10/40)

## F4 — 判決 + doc-sync
- [ ] 按 plan §2 判決表寫判決
- [ ] 「成功定義 = 全圖召回」決策記入 rollup(AC4)+ memory 更新
- [ ] 若假說證實 → dedup-before-cap 提案(STOP+ask,唔實作)
- [ ] plan closeout + progress retro
