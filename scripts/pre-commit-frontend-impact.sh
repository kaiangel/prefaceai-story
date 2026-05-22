#!/bin/bash
# Wave 9 / DEC-030 / Ben 方案 B 落地
# 当 backend 改动以下文件时强制要求 commit message 含 [frontend-impact: yes/no] label
#
# 安装方法: bash scripts/install_pre_commit_hook.sh
# 文档:     docs/CONTRACT_HOOK.md
# 决策:     .team-brain/decisions/DECISIONS.md DEC-030

WATCHED_FILES=(
  "app/api/projects.py"
  "app/api/chapters.py"
  "app/services/pipeline_orchestrator.py"
  "app/services/job_manager.py"
  "app/models/project.py"
  "app/schemas/project.py"
)

# 获取已 staged 的文件列表
STAGED=$(git diff --cached --name-only 2>/dev/null)

# 检查是否有 watched 文件被 staged
HIT=()
for f in "${WATCHED_FILES[@]}"; do
  if echo "$STAGED" | grep -q "^${f}$"; then
    HIT+=("$f")
  fi
done

# 无命中 → 直接放行
if [ ${#HIT[@]} -eq 0 ]; then
  exit 0
fi

# 有命中 → 打印提醒
echo ""
echo "============================================================"
echo "BACKEND 契约相关文件改动检测："
for f in "${HIT[@]}"; do
  echo "   - $f"
done
echo ""
echo "请确认 commit message 含 [frontend-impact: yes] 或 [frontend-impact: no] label"
echo "原因: 上述文件可能影响 frontend API 契约 (DEC-030)"
echo "============================================================"

# 检查 commit message 是否含 label
COMMIT_MSG_FILE=".git/COMMIT_EDITMSG"
if [ -f "$COMMIT_MSG_FILE" ]; then
  if ! grep -qE "\[frontend-impact: (yes|no)\]" "$COMMIT_MSG_FILE"; then
    echo ""
    echo "ERROR: commit message 缺少 [frontend-impact: yes/no] label"
    echo "请在 commit message 末尾加入此 label 后重试"
    echo ""
    echo "示例:"
    echo "  git commit -m 'fix: chapters.py regenerate endpoint [frontend-impact: yes]'"
    echo "  git commit -m 'fix: pipeline_orchestrator.py internal queue [frontend-impact: no]'"
    echo ""
    echo "如需临时跳过 (强烈不建议): git commit --no-verify"
    exit 1
  fi
fi

exit 0
