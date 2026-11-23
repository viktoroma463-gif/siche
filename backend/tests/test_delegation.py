from app.engine import create_session
from app.rules.delegation import advance_stage, is_delegation_request


def test_detects_direct_delegation_phrases():
    samples = [
        "我不会做",
        "你帮我决定",
        "直接给我一段",
        "据此写摘要",
        "帮我写论点",
        "帮我概括一下",
        "直接出稿",
        "帮我写一篇完整论文",
    ]
    for text in samples:
        assert is_delegation_request(text), text


def test_normal_reflection_is_not_delegation():
    assert not is_delegation_request("我认为通知会降低专注，因为注意会被反复打断。")
    assert not is_delegation_request("帮我分析一下这段论证的漏洞")


def test_stage_progression_and_reset():
    session = create_session()

    assert advance_stage(session, "直接帮我写") == 1
    assert advance_stage(session, "还是不会，你直接写") == 2
    assert advance_stage(session, "帮我写完整一点") == 3
    assert advance_stage(session, "直接给我成品") == 4
    assert advance_stage(session, "再来") == 4
    assert advance_stage(session, "我认为核心矛盾是注意资源有限，因为任务需要持续加工") == 0
