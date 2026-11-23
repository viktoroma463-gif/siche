from app.engine import create_session
from app.rules.draft_gate import (
    draft_allowed,
    is_full_text_request,
    is_substantive_user_input,
    update_gate,
)


def test_acknowledgement_is_not_substantive():
    assert is_substantive_user_input("好的，明白了") is False
    assert is_substantive_user_input("我认为通知频率过高会打断连续阅读，因为注意力被反复拉回。") is True


def test_full_text_request_never_allowed():
    session = create_session()
    session["gate"].update(
        {"user_thinking_count": 3, "dialectic_rounds": 2, "draft_iterations": 2}
    )
    assert is_full_text_request("帮我写完整论文") is True
    assert draft_allowed(session, "帮我写完整论文") is False


def test_draft_requires_dialectic_round():
    session = create_session()
    text = "我的研究问题是通知频率如何影响连续阅读，这是我的草稿，帮我整理成参考片段。"
    update_gate(session, text, "")
    assert session["gate"]["user_thinking_count"] >= 1
    assert session["gate"]["dialectic_rounds"] == 0
    assert draft_allowed(session, text) is False


def test_draft_allowed_after_one_dialectic_round():
    session = create_session()
    first = "我认为通知频率越高，连续学习时段的专注时长越短，因为注意力被反复拉回。"
    update_gate(session, first, "")
    second = (
        "我的想法是：通知频率越高，注意力被拉回次数越多，连续阅读时长就越短；"
        "请根据这段想法，帮我整理成参考草稿片段。"
    )
    update_gate(session, second, "guide")
    assert session["gate"]["dialectic_rounds"] == 1
    assert draft_allowed(session, second) is True


def test_polish_iteration_opens_draft_gate():
    session = create_session()
    session["gate"].update(
        {
            "user_thinking_count": 2,
            "dialectic_rounds": 1,
            "draft_iterations": 2,
            "polish_iterations": 2,
        }
    )
    assert draft_allowed(session, "请帮我润色成参考版本") is True
