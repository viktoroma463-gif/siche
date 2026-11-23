"""识别「直接代写/代做」诉求，并推进四层引导阶段。"""

from app.rules.textutil import char_count, contains_any

# 只覆盖明确的代写/代做诉求；「帮我分析一下」这类正常支架请求不在此列。
DELEGATION_PATTERNS = [
    "不会做",
    "我不会",
    "还是不会",
    "不会写",
    "不会分析",
    "不会弄",
    "搞不定",
    "写不出来",
    "做不出来",
    "不知道怎么写",
    "帮我决定",
    "你帮我决定",
    "你来决定",
    "替我决定",
    "帮我选",
    "你帮我选",
    "帮我定",
    "直接给我",
    "直接给一段",
    "直接给结论",
    "直接写",
    "直接出稿",
    "直接生成",
    "直接产出",
    "帮我写",
    "替我写",
    "你帮我写",
    "帮我做",
    "替我完成",
    "帮我完成",
    "代写",
    "据此写",
    "写摘要",
    "写一段摘要",
    "帮我概括",
    "帮我总结",
    "概括一下",
    "总结一下",
    "帮我写论点",
    "帮我写观点",
    "帮我写结论",
    "帮我下结论",
    "你来判断",
    "替我判断",
    "完整论文",
    "论文全文",
    "完整分析",
    "一次写完",
    "一次性写完",
    "成品",
    "不用我想",
    "跳过分析",
    "交稿",
    "终稿",
]

MIN_OWN_INPUT = 8


def is_delegation_request(text: str | None) -> bool:
    return contains_any(text or "", DELEGATION_PATTERNS)


def is_substantive_own_input(text: str | None) -> bool:
    raw = (text or "").strip()
    if is_delegation_request(raw):
        return False
    return char_count(raw) >= MIN_OWN_INPUT


def advance_stage(session: dict, text: str) -> int:
    """命中代写诉求则升一级（封顶 4）；用户给出自己的实质输入则归零。"""
    stage = int(session.get("delegation_stage", 0) or 0)
    if is_delegation_request(text):
        stage = min(stage + 1, 4)
    elif is_substantive_own_input(text):
        stage = 0
    session["delegation_stage"] = stage
    return stage
