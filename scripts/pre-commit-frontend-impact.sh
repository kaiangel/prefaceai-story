#!/bin/bash
# Wave 9 / DEC-030 / Ben 方案 B 落地
# 当 backend 改动以下文件时强制要求 commit message 含 [frontend-impact: yes/no] label
#
# Wave 10 P0 安全 (KEY_LEARNINGS #58 + DEC-050): Layer 0 SECRET SCANNER (拦截 commit 前 secret 泄漏)
#
# 安装方法: bash scripts/install_pre_commit_hook.sh
# 文档:     docs/CONTRACT_HOOK.md
# 决策:     .team-brain/decisions/DECISIONS.md DEC-030 + DEC-050

# ====================================================================
# Layer 0 SECRET SCANNER (Wave 10 加, P0 防 GitGuardian 重演)
# ====================================================================
# 扫描 staged 文件内容 (不只 file name) 是否含 secret 模式
# 模式覆盖: Google API (AIzaSy 39 char) + Anthropic (sk-ant-) + OpenAI (sk-) + 火山引擎 (AKLT)

SECRET_PATTERNS=(
  "AIzaSy[A-Za-z0-9_-]{33}"            # Google API (含 Gemini)
  "sk-ant-[a-zA-Z0-9_-]{40,}"           # Anthropic API
  "sk-[a-zA-Z0-9]{40,}"                  # OpenAI API (会误伤 sk-ant-, but 检测 OK)
  "AKLT[A-Za-z0-9+/=]{40,}"             # 火山引擎
)

# 白名单 (脱敏占位符不算泄漏)
SECRET_ALLOWLIST=(
  "AIzaSyCX\*\*\*"                       # 已脱敏占位符 (旧 Apr29 key)
  "AIzaSyBm\*\*\*"                       # 已脱敏占位符 (旧 Apr29 new key)
  "AIzaSyxxx"                            # 文档示例占位符
  "sk-ant-xxx"                           # 文档示例
  "sk-xxx"                               # 文档示例
  "AKLTxxx"                              # 文档示例
  "redacted-key"                         # 脱敏标记
)

# 获取 staged 文件 (跳过删除文件)
SECRET_STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)

if [ -n "$SECRET_STAGED" ]; then
  for f in $SECRET_STAGED; do
    # 跳过二进制 / 不存在文件
    [ -f "$f" ] || continue
    file --mime "$f" 2>/dev/null | grep -q "charset=binary" && continue

    for pattern in "${SECRET_PATTERNS[@]}"; do
      MATCHES=$(grep -nE "$pattern" "$f" 2>/dev/null)
      if [ -n "$MATCHES" ]; then
        # 检查是否在 allowlist
        IS_ALLOWED=false
        for allow in "${SECRET_ALLOWLIST[@]}"; do
          if echo "$MATCHES" | grep -qE "$allow"; then
            IS_ALLOWED=true
            break
          fi
        done

        if [ "$IS_ALLOWED" = "false" ]; then
          echo ""
          echo "🚨🚨🚨 ============================================================"
          echo "🚨 SECRET SCANNER 拦截: 文件 $f 含 secret 模式 ($pattern)"
          echo "🚨 ============================================================"
          echo ""
          echo "Match (前 200 char):"
          echo "$MATCHES" | head -3 | cut -c1-200
          echo ""
          echo "📋 处理建议:"
          echo "  1. 脱敏: AIzaSy*** / sk-*** / AKLT*** (前 8 char + 星号 + [redacted-key-...])"
          echo "  2. 移到 .env (gitignored)"
          echo "  3. 如确认是占位符/历史脱敏, 加 'redacted-key' 注释跳过"
          echo ""
          echo "⚠️  如强制跳过 (强烈不建议): git commit --no-verify"
          echo "⚠️  历史教训: 5/22 GitGuardian 警报 + Google 主动 revoke (DEC-050 / KEY_LEARNINGS #58)"
          echo ""
          exit 1
        fi
      fi
    done
  done
fi

# ====================================================================
# Layer 1 FRONTEND-IMPACT CHECK (DEC-030 / Ben 方案 B, 原 hook 逻辑)
# ====================================================================

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
