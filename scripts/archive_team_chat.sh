#!/bin/bash
set -euo pipefail

# =============================================================================
# TEAM_CHAT.md 归档脚本
# 两种模式:
#
# 1. 日期模式 (默认): 将 7 天前的消息归档到 .team-brain/chat-archive/YYYY-MM.md
#    用法: ./scripts/archive_team_chat.sh
#
# 2. 行数模式: 超过指定行数时保留最新 N 行，其余按月归档
#    用法: ./scripts/archive_team_chat.sh --max-lines 5000 --keep 2000
#
# 幂等: 多次运行结果一致
# =============================================================================

# --- 解析参数 ---
MODE="date"       # "date" 或 "lines"
MAX_LINES=""
KEEP_LINES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-lines)
            MODE="lines"
            MAX_LINES="$2"
            shift 2
            ;;
        --keep)
            KEEP_LINES="$2"
            shift 2
            ;;
        *)
            echo "❌ 未知参数: $1"
            echo "用法: $0 [--max-lines N --keep M]"
            exit 1
            ;;
    esac
done

# 行数模式必须同时提供 --max-lines 和 --keep
if [[ "$MODE" == "lines" ]]; then
    if [[ -z "$MAX_LINES" || -z "$KEEP_LINES" ]]; then
        echo "❌ 行数模式需要同时提供 --max-lines 和 --keep 参数"
        echo "用法: $0 --max-lines 5000 --keep 2000"
        exit 1
    fi
fi

# --- 配置 ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEAM_CHAT="$PROJECT_ROOT/.team-brain/TEAM_CHAT.md"
ARCHIVE_DIR="$PROJECT_ROOT/.team-brain/chat-archive"
RETENTION_DAYS=7

# --- 前置检查 ---
if [[ ! -f "$TEAM_CHAT" ]]; then
    echo "❌ 错误: $TEAM_CHAT 不存在"
    exit 1
fi

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# =============================================================================
# 行数模式
# =============================================================================
if [[ "$MODE" == "lines" ]]; then
    echo "📏 行数模式: 超过 $MAX_LINES 行时归档，保留最新 $KEEP_LINES 行"
    echo "📂 归档目录: $ARCHIVE_DIR"

    export TEAM_CHAT ARCHIVE_DIR MAX_LINES KEEP_LINES

    python3 << 'PYTHON_LINES_SCRIPT'
import os
import re
import sys
from datetime import datetime

team_chat = os.environ.get('TEAM_CHAT')
archive_dir = os.environ.get('ARCHIVE_DIR')
max_lines = int(os.environ.get('MAX_LINES'))
keep_lines = int(os.environ.get('KEEP_LINES'))

with open(team_chat, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
total_lines = len(lines)

print(f"📊 当前行数: {total_lines}，阈值: {max_lines}，保留: {keep_lines}")

if total_lines <= max_lines:
    print(f"✅ 无需归档（{total_lines} ≤ {max_lines}）")
    sys.exit(0)

# --- 识别文件头部（第一个 --- 前，含第一个 ---）---
header_end = 0
separator_count = 0
for i, line in enumerate(lines):
    if line.strip() == '---':
        separator_count += 1
        if separator_count == 2:
            header_end = i + 1
            break

if separator_count < 2:
    for i, line in enumerate(lines):
        date_h3 = re.match(r'^### \d{4}-\d{2}-\d{2}', line)
        date_h4 = re.match(r'^#### @\w+.*[\(\[](\d{4}-\d{2}-\d{2})', line)
        if date_h3 or date_h4:
            header_end = i
            break

header_lines = lines[:header_end]
message_lines = lines[header_end:]

print(f"📊 头部行数: {len(header_lines)}，消息行数: {len(message_lines)}")

# --- 取最后 keep_lines 行作为保留内容 ---
# 从 message_lines 里取最后 keep_lines 行
if len(message_lines) <= keep_lines:
    print(f"✅ 消息行数 ({len(message_lines)}) ≤ keep_lines ({keep_lines})，无需归档")
    sys.exit(0)

archive_message_lines = message_lines[:-keep_lines]  # 要归档的中间部分
keep_message_lines = message_lines[-keep_lines:]      # 保留的最新部分

print(f"📊 归档消息行数: {len(archive_message_lines)}，保留消息行数: {len(keep_message_lines)}")

# --- 日期提取工具 ---
date_pattern_h3 = re.compile(r'^### (\d{4}-\d{2}-\d{2})')
date_pattern_h4 = re.compile(r'^#### @\w+.*[\(\[](\d{4}-\d{2}-\d{2})')

def extract_date(line):
    m = date_pattern_h3.match(line)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    m = date_pattern_h4.match(line)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

# --- 按月份分组归档内容 ---
monthly_archives = {}  # "YYYY-MM" -> [lines]
current_month = None

for line in archive_message_lines:
    d = extract_date(line)
    if d is not None:
        current_month = d.strftime('%Y-%m')
    if current_month is not None:
        if current_month not in monthly_archives:
            monthly_archives[current_month] = []
        monthly_archives[current_month].append(line)
    # 没有日期的前置行（如空行）暂归入第一个月份或丢弃（无月份时丢弃）

if not monthly_archives:
    print("⚠️  归档部分没有找到日期标记，跳过归档（保留原文件不变）")
    sys.exit(0)

# --- 写入归档文件（幂等）---
for month_key in sorted(monthly_archives.keys()):
    archive_file = os.path.join(archive_dir, f"{month_key}.md")
    archive_lines = monthly_archives[month_key]
    new_content = '\n'.join(archive_lines)

    existing_content = ""
    if os.path.exists(archive_file):
        with open(archive_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    # 幂等检查：用第一条日期行判断
    first_date_line = None
    for line in archive_lines:
        if extract_date(line) is not None:
            first_date_line = line
            break

    if first_date_line and first_date_line in existing_content:
        print(f"  ⏭️  {month_key}.md 已包含此内容（幂等跳过）")
        continue

    if existing_content:
        with open(archive_file, 'a', encoding='utf-8') as f:
            f.write('\n' + new_content)
        print(f"  📝 追加到 {month_key}.md ({len(archive_lines)} 行)")
    else:
        file_header = f"# 序话Story 团队群聊归档 — {month_key}\n\n"
        file_header += f"> 归档自 `.team-brain/TEAM_CHAT.md`\n"
        file_header += f"> 归档时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        file_header += "---\n\n"
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(file_header + new_content)
        print(f"  📝 创建 {month_key}.md ({len(archive_lines)} 行)")

# --- 重写主文件 = 头部 + 最新 keep_lines 行 ---
final_lines = header_lines + ['\n'] + keep_message_lines

while final_lines and final_lines[-1].strip() == '':
    final_lines.pop()
final_lines.append('')

final_content = '\n'.join(final_lines)

with open(team_chat, 'w', encoding='utf-8') as f:
    f.write(final_content)

new_line_count = len(final_content.split('\n'))
archived_count = sum(len(v) for v in monthly_archives.values())

print(f"\n✅ 行数归档完成!")
print(f"  归档前行数: {total_lines}")
print(f"  归档后行数: {new_line_count}")
print(f"  归档消息行数: {archived_count}")
print(f"  归档月份数: {len(monthly_archives)}")
print(f"  归档文件: {', '.join(sorted(monthly_archives.keys()))}")

PYTHON_LINES_SCRIPT

    echo ""
    echo "🎉 行数归档脚本执行完毕"
    exit 0
fi

# =============================================================================
# 日期模式（原有逻辑，不动）
# =============================================================================

# --- 计算截止日期 ---
# macOS 和 Linux 的 date 命令不同
if date -v -1d > /dev/null 2>&1; then
    # macOS (BSD date)
    CUTOFF_DATE=$(date -v -${RETENTION_DAYS}d +%Y-%m-%d)
else
    # Linux (GNU date)
    CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d)
fi

echo "📅 归档截止日期: $CUTOFF_DATE (保留 $CUTOFF_DATE 之后的消息)"
echo "📂 归档目录: $ARCHIVE_DIR"

# 导出变量供 Python heredoc 使用
export TEAM_CHAT ARCHIVE_DIR CUTOFF_DATE

# --- 使用 Python 进行精确的日期解析和归档 ---
# Bash 对复杂文本处理能力有限，使用 Python 确保正确性
python3 << 'PYTHON_SCRIPT'
import os
import re
import sys
from datetime import datetime

# 从环境获取参数
team_chat = os.environ.get('TEAM_CHAT')
archive_dir = os.environ.get('ARCHIVE_DIR')
cutoff_date_str = os.environ.get('CUTOFF_DATE')

cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d').date()

# 读取整个文件
with open(team_chat, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
total_lines = len(lines)

# --- Step 1: 分离头部和消息体 ---
# 头部 = 第一个 "---" 之前的内容 + "---" 本身
# 然后是 "## 聊天记录" + "---"
# 消息从第一个日期行开始

# 找到头部结束位置
# 头部格式:
#   # 标题
#   > 说明
#   ---
#   ## 聊天记录
#   ---
header_end = 0
separator_count = 0
for i, line in enumerate(lines):
    if line.strip() == '---':
        separator_count += 1
        if separator_count == 2:
            header_end = i + 1  # 包含第二个 ---
            break

# 如果找不到两个 ---，使用保守策略
if separator_count < 2:
    # 找第一个日期行
    for i, line in enumerate(lines):
        if re.match(r'^### \d{4}-\d{2}-\d{2}', line) or re.match(r'^#### @\w+.*\(\d{4}-\d{2}-\d{2}\)', line):
            header_end = i
            break

header_lines = lines[:header_end]
message_lines = lines[header_end:]

print(f"📊 文件总行数: {total_lines}")
print(f"📊 头部行数: {len(header_lines)}")
print(f"📊 消息行数: {len(message_lines)}")

# --- Step 2: 将消息分割成带日期的块 ---
# 日期模式:
#   ### 2026-04-14 HH:MM
#   ### 2026-04-14 (任意文字)
#   #### @agent (2026-04-14)
#   #### @agent → @agent (2026-04-14)
#   #### @agent → @agent (2026-04-14 HH:MM)

date_pattern_h3 = re.compile(r'^### (\d{4}-\d{2}-\d{2})')
date_pattern_h4 = re.compile(r'^#### @\w+.*\((\d{4}-\d{2}-\d{2})')
# Also match: #### @agent [2026-04-14 HH:MM]
date_pattern_h4_bracket = re.compile(r'^#### @\w+.*\[(\d{4}-\d{2}-\d{2})')

def extract_date(line):
    """从行中提取日期，返回 date 对象或 None"""
    m = date_pattern_h3.match(line)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    m = date_pattern_h4.match(line)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    m = date_pattern_h4_bracket.match(line)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

# 将消息行分成块，每个块有一个日期
# 块 = (date, [lines])
blocks = []
current_date = None
current_block_lines = []

for line in message_lines:
    line_date = extract_date(line)
    if line_date is not None:
        # 保存之前的块
        if current_block_lines:
            blocks.append((current_date, current_block_lines))
        current_date = line_date
        current_block_lines = [line]
    else:
        current_block_lines.append(line)

# 保存最后一个块
if current_block_lines:
    blocks.append((current_date, current_block_lines))

print(f"📊 消息块数: {len(blocks)}")

# --- Step 3: 分类块为 archive（旧）和 keep（新）---
archive_blocks = []  # (date, lines)
keep_blocks = []     # (date, lines)

for block_date, block_lines in blocks:
    if block_date is not None and block_date < cutoff_date:
        archive_blocks.append((block_date, block_lines))
    else:
        # 没有日期的块（如开头的空行）或日期 >= cutoff 的块保留
        keep_blocks.append((block_date, block_lines))

print(f"📊 归档块数: {len(archive_blocks)}")
print(f"📊 保留块数: {len(keep_blocks)}")

if not archive_blocks:
    print("✅ 没有需要归档的消息（所有消息都在 7 天内）")
    sys.exit(0)

# --- Step 4: 按月份分组归档块 ---
monthly_archives = {}  # "YYYY-MM" -> [lines]

for block_date, block_lines in archive_blocks:
    if block_date is None:
        continue
    month_key = block_date.strftime('%Y-%m')
    if month_key not in monthly_archives:
        monthly_archives[month_key] = []
    monthly_archives[month_key].extend(block_lines)

# --- Step 5: 写入归档文件 ---
for month_key in sorted(monthly_archives.keys()):
    archive_file = os.path.join(archive_dir, f"{month_key}.md")
    archive_lines = monthly_archives[month_key]

    # 如果归档文件已存在，读取现有内容并合并（幂等）
    existing_content = ""
    if os.path.exists(archive_file):
        with open(archive_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    new_content = '\n'.join(archive_lines)

    # 幂等检查：如果新内容已经在归档文件中，跳过
    # 使用第一个日期行作为标记检查
    first_date_line = None
    for line in archive_lines:
        if extract_date(line) is not None:
            first_date_line = line
            break

    if first_date_line and first_date_line in existing_content:
        print(f"  ⏭️  {month_key}.md 已包含此内容（幂等跳过）")
        continue

    # 写入归档文件
    if existing_content:
        # 追加到现有文件
        with open(archive_file, 'a', encoding='utf-8') as f:
            f.write('\n' + new_content)
        print(f"  📝 追加到 {month_key}.md ({len(archive_lines)} 行)")
    else:
        # 创建新归档文件
        file_header = f"# 序话Story 团队群聊归档 — {month_key}\n\n"
        file_header += f"> 归档自 `.team-brain/TEAM_CHAT.md`\n"
        file_header += f"> 归档时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        file_header += "---\n\n"

        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(file_header + new_content)
        print(f"  📝 创建 {month_key}.md ({len(archive_lines)} 行)")

# --- Step 6: 重写主文件（头部 + 保留的消息）---
# 确保头部包含归档说明
header_text = '\n'.join(header_lines)

# 检查是否已有归档说明（幂等）
archive_notice = '> 历史消息已归档到'
if archive_notice not in header_text:
    # 在群成员说明之后、第一个 --- 之前插入归档说明
    # 找到 "**群成员**" 行的位置
    insert_idx = None
    for i, line in enumerate(header_lines):
        if '群成员' in line or '**群成员**' in line:
            # 找到这一行之后的空行
            j = i + 1
            while j < len(header_lines) and header_lines[j].strip() == '':
                j += 1
            # 如果下一个非空行是 >（仍在 blockquote 中），继续
            while j < len(header_lines) and header_lines[j].startswith('>'):
                j += 1
            insert_idx = j
            break

    if insert_idx is None:
        # 找第一个 --- 之前插入
        for i, line in enumerate(header_lines):
            if line.strip() == '---':
                insert_idx = i
                break

    if insert_idx is not None:
        notice_lines = [
            '>',
            '> 历史消息已归档到 `.team-brain/chat-archive/YYYY-MM.md`',
            '> 归档脚本: `scripts/archive_team_chat.sh`',
        ]
        header_lines = header_lines[:insert_idx] + notice_lines + header_lines[insert_idx:]

# 组装保留的消息
keep_content_lines = []
for _, block_lines in keep_blocks:
    keep_content_lines.extend(block_lines)

# 组装最终文件
final_lines = header_lines + ['\n'] + keep_content_lines

# 去掉末尾多余空行
while final_lines and final_lines[-1].strip() == '':
    final_lines.pop()
final_lines.append('')  # 文件末尾保留一个换行

final_content = '\n'.join(final_lines)

# 写入主文件
with open(team_chat, 'w', encoding='utf-8') as f:
    f.write(final_content)

# 统计
keep_line_count = len(final_content.split('\n'))
archived_line_count = sum(len(lines) for _, lines in archive_blocks)
print(f"\n✅ 归档完成!")
print(f"  归档前行数: {total_lines}")
print(f"  归档后行数: {keep_line_count}")
print(f"  归档消息行数: {archived_line_count}")
print(f"  归档月份数: {len(monthly_archives)}")
print(f"  归档文件: {', '.join(sorted(monthly_archives.keys()))}")

PYTHON_SCRIPT

echo ""
echo "🎉 归档脚本执行完毕"
