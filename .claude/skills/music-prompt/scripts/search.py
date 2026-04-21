#!/usr/bin/env python3
"""
music-prompt skill 术语搜索工具

在 music_theory.md 和 cross_sensory.md 中搜索关键词，
返回匹配的流派、乐器、术语、情绪词、场景映射等内容。

用法:
    python3 search.py "钢琴"
    python3 search.py "sad" --domain mood
    python3 search.py "雨夜" --domain scene
    python3 search.py "jazz" --domain genre
    python3 search.py "piano" --domain instrument
"""

import argparse
import os
import sys

# 知识库文件路径（相对于 scripts/ 目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(SCRIPT_DIR, "..", "knowledge")

KNOWLEDGE_FILES = {
    "music_theory": os.path.join(KNOWLEDGE_DIR, "music_theory.md"),
    "cross_sensory": os.path.join(KNOWLEDGE_DIR, "cross_sensory.md"),
}

# domain → 关键标题关键词映射（用于定向搜索）
DOMAIN_SECTION_HINTS = {
    "genre":      ["流派", "genre", "classical", "electronic", "rock", "jazz", "pop", "world", "hip-hop"],
    "instrument": ["乐器", "instrument", "钢琴", "piano", "guitar", "strings", "brass", "woodwind", "percussion"],
    "term":       ["术语", "term", "技法", "bpm", "tempo", "dynamics", "harmony", "timbre", "reverb"],
    "mood":       ["情绪", "mood", "emotion", "感受", "情感"],
    "scene":      ["场景", "scene", "画面", "视觉", "光影", "色调", "构图"],
    "sensory":    ["感官", "sensory", "触觉", "嗅觉", "味觉", "听觉", "视觉", "第六感", "第七感"],
}

# ANSI 颜色（终端输出高亮）
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GREEN = "\033[32m"
DIM = "\033[2m"


def load_file(path: str) -> list[str]:
    """读取文件，返回行列表（保留换行符去除）"""
    if not os.path.exists(path):
        print(f"  [警告] 文件不存在: {path}", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def search_in_lines(
    lines: list[str],
    keyword: str,
    context: int = 1,
) -> list[dict]:
    """
    在行列表中搜索关键词（大小写不敏感）。
    返回匹配结果列表，每项包含：
        line_no   : 匹配行号（1-based）
        matched   : 匹配的原始行文本
        before    : 前 context 行
        after     : 后 context 行
    """
    keyword_lower = keyword.lower()
    results = []
    seen_ranges: set[tuple[int, int]] = set()  # 去重：避免相邻匹配行上下文重叠

    for i, line in enumerate(lines):
        if keyword_lower in line.lower():
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)

            # 跳过与已收录结果重叠的匹配
            range_key = (start, end)
            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            results.append({
                "line_no": i + 1,
                "matched": line.rstrip(),
                "before": [l.rstrip() for l in lines[start:i]],
                "after":  [l.rstrip() for l in lines[i + 1:end]],
            })

    return results


def is_section_relevant(lines: list[str], line_no: int, domain: str) -> bool:
    """
    判断某一匹配行是否属于 domain 对应的章节。
    向上扫描最近的 Markdown 标题（## / ###），
    若标题包含 domain 的关键词则返回 True。
    domain = "all" 时始终返回 True。
    """
    if domain == "all":
        return True

    hints = DOMAIN_SECTION_HINTS.get(domain, [])
    if not hints:
        return True  # 未知 domain 不过滤

    # 向上找最近的章节标题
    for i in range(line_no - 2, -1, -1):  # line_no 是 1-based，所以 -2
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            title_lower = stripped.lower()
            return any(h.lower() in title_lower for h in hints)

    return True  # 没找到标题，不过滤


def format_result(result: dict, file_label: str, keyword: str) -> str:
    """将单个匹配结果格式化为可读字符串"""
    lines_out = []

    # 上下文前行（淡色）
    for line in result["before"]:
        if line:
            lines_out.append(f"  {DIM}{line}{RESET}")

    # 匹配行（高亮关键词）
    matched = result["matched"]
    highlighted = matched.replace(
        keyword, f"{YELLOW}{BOLD}{keyword}{RESET}"
    )
    # 大小写不敏感替换（原文保留，关键词高亮）
    if keyword not in matched:
        # 尝试大小写不敏感替换
        lower_matched = matched.lower()
        idx = lower_matched.find(keyword.lower())
        if idx >= 0:
            highlighted = (
                matched[:idx]
                + f"{YELLOW}{BOLD}{matched[idx:idx+len(keyword)]}{RESET}"
                + matched[idx + len(keyword):]
            )
    lines_out.append(f"  {GREEN}▶{RESET} {highlighted}")

    # 上下文后行（淡色）
    for line in result["after"]:
        if line:
            lines_out.append(f"  {DIM}{line}{RESET}")

    header = f"{CYAN}{file_label}{RESET}  {DIM}行 {result['line_no']}{RESET}"
    return header + "\n" + "\n".join(lines_out)


def run_search(keyword: str, domain: str = "all") -> None:
    """主搜索逻辑：遍历知识库文件，输出匹配结果"""
    total_hits = 0

    print(f"\n{BOLD}搜索关键词:{RESET} {YELLOW}{keyword}{RESET}"
          f"  {BOLD}领域:{RESET} {domain}\n")

    for file_key, file_path in KNOWLEDGE_FILES.items():
        lines = load_file(file_path)
        if not lines:
            continue

        results = search_in_lines(lines, keyword, context=1)

        # 按 domain 过滤
        if domain != "all":
            results = [
                r for r in results
                if is_section_relevant(lines, r["line_no"], domain)
            ]

        if not results:
            continue

        file_label = os.path.basename(file_path)
        print(f"{BOLD}{'─' * 60}{RESET}")
        print(f"{BOLD}文件:{RESET} {file_label}  {DIM}({len(results)} 处匹配){RESET}")
        print(f"{BOLD}{'─' * 60}{RESET}")

        for r in results:
            print(format_result(r, file_label, keyword))
            print()

        total_hits += len(results)

    if total_hits == 0:
        print(f"  未找到匹配「{keyword}」的内容。")
        if domain != "all":
            print(f"  提示: 尝试 --domain all 扩大搜索范围。")
    else:
        print(f"{BOLD}共找到 {total_hits} 处匹配。{RESET}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search.py",
        description=(
            "music-prompt skill 术语搜索工具\n"
            "在 music_theory.md 和 cross_sensory.md 中搜索关键词。\n\n"
            "示例:\n"
            "  python3 search.py \"钢琴\"\n"
            "  python3 search.py \"sad\" --domain mood\n"
            "  python3 search.py \"雨夜\" --domain scene\n"
            "  python3 search.py \"jazz\" --domain genre\n"
            "  python3 search.py \"piano\" --domain instrument"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "keyword",
        help="搜索关键词（支持中英文，大小写不敏感）",
    )
    parser.add_argument(
        "--domain",
        choices=["genre", "instrument", "term", "mood", "scene", "sensory", "all"],
        default="all",
        help=(
            "限定搜索领域（默认 all）:\n"
            "  genre      — 流派\n"
            "  instrument — 乐器\n"
            "  term       — 术语/技法\n"
            "  mood       — 情绪/情感\n"
            "  scene      — 场景/画面\n"
            "  sensory    — 跨感官映射\n"
            "  all        — 全部（默认）"
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_search(args.keyword, args.domain)


if __name__ == "__main__":
    main()
