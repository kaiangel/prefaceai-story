#!/bin/bash
# 安装 pre-commit hook (软链接到 .git/hooks/)
#
# 用法: bash scripts/install_pre_commit_hook.sh
# 文档: docs/CONTRACT_HOOK.md
# 决策: .team-brain/decisions/DECISIONS.md DEC-030

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: 必须在 git 仓库内运行此脚本"
  exit 1
fi

HOOK_SOURCE="$REPO_ROOT/scripts/pre-commit-frontend-impact.sh"
HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"

# 确认 hook source 存在
if [ ! -f "$HOOK_SOURCE" ]; then
  echo "ERROR: hook source 不存在: $HOOK_SOURCE"
  echo "请先确认 scripts/pre-commit-frontend-impact.sh 存在"
  exit 1
fi

# 赋予 hook source 可执行权限
chmod +x "$HOOK_SOURCE"
echo "已赋予可执行权限: $HOOK_SOURCE"

# 安装 hook
if [ -L "$HOOK_DEST" ]; then
  CURRENT_TARGET=$(readlink "$HOOK_DEST")
  echo "已存在 symlink: $HOOK_DEST -> $CURRENT_TARGET"
  if [ "$CURRENT_TARGET" = "$HOOK_SOURCE" ]; then
    echo "symlink 已指向正确目标，无需重新安装"
  else
    echo "WARNING: symlink 指向不同目标，请手动检查后删除再重新运行"
    exit 1
  fi
elif [ -f "$HOOK_DEST" ]; then
  echo "WARNING: $HOOK_DEST 已存在普通文件"
  echo "请手动备份后删除，再重新运行此脚本:"
  echo "  cp $HOOK_DEST ${HOOK_DEST}.bak"
  echo "  rm $HOOK_DEST"
  echo "  bash scripts/install_pre_commit_hook.sh"
  exit 1
else
  ln -s "$HOOK_SOURCE" "$HOOK_DEST"
  echo "pre-commit hook 已安装: $HOOK_DEST"
fi

echo ""
echo "安装完成。验证:"
echo "  ls -la $HOOK_DEST"
echo ""
echo "测试:"
echo "  git add app/api/chapters.py"
echo "  git commit -m 'test: without label'   # 应被 block"
echo "  git commit -m 'test: with label [frontend-impact: no]'  # 应放行"
