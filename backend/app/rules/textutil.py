import re

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WS_RE = re.compile(r"\s+")
MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
MD_BULLET_RE = re.compile(r"^\s{0,3}[-*+]\s+")
MD_QUOTE_RE = re.compile(r"^\s{0,3}>\s?")
MULTI_BLANK_RE = re.compile(r"\n{3,}")


def compact(text: str | None) -> str:
    return WS_RE.sub("", text or "")


def char_count(text: str | None) -> int:
    """Count visible characters (CJK + letters/digits/punct, no whitespace)."""
    return len(compact(text))


def cjk_count(text: str | None) -> int:
    return len(CJK_RE.findall(text or ""))


def contains_any(text: str, keywords: list[str]) -> list[str]:
    return [k for k in keywords if k and k in (text or "")]


def strip_markdown(text: str | None) -> str:
    """强制 AI 输出遵守“无 Markdown”规则。"""
    lines: list[str] = []
    for raw in (text or "").splitlines():
        line = MD_HEADING_RE.sub("", raw)
        line = MD_BULLET_RE.sub("", line)
        line = MD_QUOTE_RE.sub("", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        lines.append(line.rstrip())
    cleaned = "\n".join(lines)
    cleaned = MULTI_BLANK_RE.sub("\n\n", cleaned)
    return cleaned.strip()
