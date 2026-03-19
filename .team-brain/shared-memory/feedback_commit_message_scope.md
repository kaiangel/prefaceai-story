---
name: Commit message 必须覆盖完整代码范围
description: Git commit message 必须标注所有包含的变更批次，不能遗漏。PM 复核发现 4926a9a 包含 T29-T37 + T-A~T-K 两批代码但 message 仅标注 T-A~T-K。
type: feedback
---

DevOps 做 git commit 时，commit message 必须覆盖该 commit 中**所有**代码变更的范围。

**事件 (2026-03-14)**: Commit `4926a9a` 实际包含 T29-T37（R6 修复）+ T-A~T-K（R7 修复）两批代码变更，但 commit message 仅标注了 "T-A~T-K platform fixes"，遗漏了 T29-T37。PM 部署复核时发现此问题。

**教训**:
- 提交前必须 `git diff --cached` 确认所有变更内容
- Commit message 必须反映完整的变更范围，不能只标注最近一批
- 如果多批未提交代码混在一起，要么拆分 commit，要么在 message 中全部列出
