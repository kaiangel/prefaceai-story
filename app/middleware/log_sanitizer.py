"""日志脱敏 — 拦截 print/logging 输出，替换敏感信息为 ***REDACTED***"""

import builtins
import io
import re

# 敏感关键字模式：匹配 KEY=value 或 "key": "value" 等常见格式
_SENSITIVE_PATTERNS = [
    # 环境变量 / 配置键值对: KEY=sk-ant-xxx 或 KEY = "xxx"
    re.compile(
        r"(ANTHROPIC_API_KEY|GEMINI_API_KEY|OPENAI_API_KEY"
        r"|VOLCENGINE_ACCESS_KEY|VOLCENGINE_SECRET_KEY"
        r"|api_key|secret_key|access_key|auth_token"
        r"|password|token|secret)"
        r"""(\s*[=:]\s*['"]?)([^\s'",:}{)\]]{8,})""",
        re.IGNORECASE,
    ),
    # sk-ant-xxx / sk-xxx / AIzaSy 等 API Key 格式
    re.compile(r"(sk-ant-[a-zA-Z0-9_-]{10,})"),
    re.compile(r"(sk-[a-zA-Z0-9_-]{20,})"),
    re.compile(r"(AIzaSy[a-zA-Z0-9_-]{30,})"),
    re.compile(r"(AKLT[a-zA-Z0-9_-]{10,})"),
]

_REDACTED = "***REDACTED***"


def _sanitize(text: str) -> str:
    """对文本中的敏感信息进行脱敏"""
    result = text
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.groups == 3:
            # 键值对模式：保留键名，替换值
            result = pattern.sub(rf"\1\2{_REDACTED}", result)
        else:
            # 直接匹配模式：整体替换
            result = pattern.sub(_REDACTED, result)
    return result


_original_print = builtins.print


def _sanitized_print(*args, **kwargs):
    """替换内置 print，对输出做脱敏"""
    sanitized_args = []
    for arg in args:
        sanitized_args.append(_sanitize(str(arg)) if not isinstance(arg, str) else _sanitize(arg))
    _original_print(*sanitized_args, **kwargs)


def install():
    """安装日志脱敏（patch builtins.print）"""
    builtins.print = _sanitized_print
