# EKP Git Hooks

commit / push 前自動品質檢查。**唔 touch `.git/`**(用 `core.hooksPath` 指向本資料夾)。

## 啟用(一次性)
```
git config core.hooksPath scripts/hooks
```
停用: `git config --unset core.hooksPath`

## Hooks
| Hook | 觸發 | 做咩 | 緊急跳過 |
|---|---|---|---|
| `pre-commit` | git commit | staged 嘅 `backend/*.py` 跑 `ruff check`(lint) | `git commit --no-verify` |
| `pre-push` | git push | backend 全套 `pytest`(~1-2 分鐘) | `git push --no-verify` |

## 設計註(實測得出)
- **`ruff format --check` 暫未納入 pre-commit**:2026-06-23 實測現有 codebase format 未統一(`models.py` 等會 "Would reformat")。若照搬會令任何改動被攔。**要加 format check,先全庫統一一次**:`cd backend && .venv/Scripts/ruff.exe format`,再喺 pre-commit 加返 `ruff format --check`。
- pre-push 跑全套 test 較慢;急用 `--no-verify`,但唔好習慣性跳(防 stale / 偽驗收溜入,呼應 CLAUDE.md H6)。
- frontend lint(`next lint`)未納入 — 如需可自行喺 pre-commit 加 staged `frontend/*.{ts,tsx}` 分支。