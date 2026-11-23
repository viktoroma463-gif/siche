"""草稿生成四项条件判定与润色迭代计数。"""

from app.rules.delegation import is_delegation_request
from app.rules.textutil import char_count, contains_any

ACK_PATTERNS = ["好的", "明白了", "知道了", "收到", "嗯", "可以", "行吧", "ok", "OK"]

DRAFT_REQUEST_PATTERNS = [
    "参考草稿",
    "草稿片段",
    "参考片段",
    "帮我整理",
    "据此整理",
    "帮我改写",
    "改写成",
    "润色成",
    "生成一段",
    "写一段参考",
    "基于我的",
    "根据我的",
    "按照我的",
    "整理成参考",
    "整理成草稿",
]

FULL_TEXT_PATTERNS = [
    "整篇论文",
    "完整论文",
    "论文全文",
    "完整章节",
    "大章节",
    "整章",
    "写一篇完整",
    "全文写",
    "把论文写完",
]

POLISH_PATTERNS = ["润色", "改写", "修改措辞", "改一下措辞"]

DRAFT_LIKE_PATTERNS = [
    "我写",
    "草稿",
    "修改后",
    "第二版",
    "第三版",
    "改为",
    "我的版本",
    "我改",
    "我的初稿",
]


def _is_ack(text: str) -> bool:
    compact = (text or "").strip()
    if not compact:
        return True
    if char_count(compact) > 16:
        return False
    return any(compact.startswith(p) or compact == p for p in ACK_PATTERNS)


def is_substantive_user_input(text: str | None) -> bool:
    raw = (text or "").strip()
    if _is_ack(raw):
        return False
    if is_delegation_request(raw):
        return False
    return char_count(raw) >= 20


def is_draft_request(text: str | None) -> bool:
    return bool(contains_any(text or "", DRAFT_REQUEST_PATTERNS))


def is_full_text_request(text: str | None) -> bool:
    return bool(contains_any(text or "", FULL_TEXT_PATTERNS))


def is_polish_request(text: str | None) -> bool:
    return bool(contains_any(text or "", POLISH_PATTERNS))


def looks_like_draft(text: str | None) -> bool:
    raw = (text or "").strip()
    return char_count(raw) >= 50 or bool(contains_any(raw, DRAFT_LIKE_PATTERNS))


def update_gate(session: dict, text: str, previous_ai_type: str) -> None:
    gate = session["gate"]
    if is_substantive_user_input(text):
        gate["user_thinking_count"] += 1
        if previous_ai_type in ("guide", "scaffold"):
            gate["dialectic_rounds"] += 1

    if looks_like_draft(text):
        gate["draft_iterations"] += 1
        if gate.get("last_ai_was_polish"):
            gate["polish_iterations"] += 1


def draft_allowed(session: dict, text: str) -> bool:
    """四项条件全部满足才允许生成 generated_draft。"""
    gate = session["gate"]
    if is_full_text_request(text):
        return False

    # 特殊润色迭代：两轮以上用户实际修改稿，且明确提出润色参考版本
    if (
        is_polish_request(text)
        and gate["polish_iterations"] >= 2
        and gate["draft_iterations"] >= 2
    ):
        return True

    return (
        gate["user_thinking_count"] >= 1
        and gate["dialectic_rounds"] >= 1
        and is_draft_request(text)
    )
