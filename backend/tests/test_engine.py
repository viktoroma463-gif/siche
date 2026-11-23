import asyncio
import json

import app.llm as llm
from app.config import settings
from app.engine import (
    assist,
    create_session,
    export_session,
    prefill_plan,
    public_session,
    refuse_micro_test,
    request_copy,
    submit_micro_test,
    update_plan,
)
from app.llm import LLMNotConfigured, chat_completion

SPECIFIC = (
    "我接受其中关于「通知会打断连续注意」的提示，但准备把适用范围改窄："
    "仅针对需要保持工作记忆的阅读任务，而不包括机械抄写。"
    "我还认为睡眠不足可能是另一条解释，不能直接把正确率下降都算到通知头上。"
    "因此这条辅助只在实验室限时阅读情境里较有参考价值。"
)


def _fake(monkeypatch, reply="【分析】这一段里把相关关系写成了因果关系。"):
    async def fake(messages, **kwargs):
        fake.last_messages = messages
        return reply

    monkeypatch.setattr(llm, "chat_completion", fake)
    return fake


def _last_ai(session):
    return [m for m in session["messages"] if m["role"] == "assistant"][-1]


def test_normal_analysis_is_guide(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(assist(session, "我认为通知会降低专注，因为注意力会被反复打断。", "claim"))

    last = _last_ai(session)
    assert last["content_type"] == "guide"
    assert last["copy_unlocked"] is True
    assert session["gate"]["user_thinking_count"] == 1
    assert session["gate"]["dialectic_rounds"] == 0


def test_scaffold_markers_override_stage(monkeypatch):
    _fake(monkeypatch, "【主论点句】我认为，（填：变高/变低）会通过（填：中介）影响连续阅读。")
    session = create_session()
    asyncio.run(assist(session, "我认为通知会影响专注，因为注意力会被反复打断。", "claim"))

    last = _last_ai(session)
    assert last["content_type"] == "scaffold"
    assert last["copy_unlocked"] is False


def test_stage_two_is_scaffold(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(assist(session, "直接帮我写", "claim"))
    assert _last_ai(session)["content_type"] == "guide"

    asyncio.run(assist(session, "还是不会，直接写", "claim"))
    last = _last_ai(session)
    assert session["delegation_stage"] == 2
    assert last["content_type"] == "scaffold"
    assert last["copy_unlocked"] is False


def test_stage_four_does_not_call_llm(monkeypatch):
    calls = []

    async def fake(messages, **kwargs):
        calls.append(messages)
        return "引导内容"

    monkeypatch.setattr(llm, "chat_completion", fake)
    session = create_session()
    for text in ["直接帮我写", "还是不会", "帮我写完整一点", "直接给我成品"]:
        asyncio.run(assist(session, text, "literature"))

    assert session["delegation_stage"] == 4
    assert len(calls) == 3
    last = _last_ai(session)
    assert last["kind"] == "stage4"
    assert last["content_type"] == "guide"
    assert "缩小问题" in last["content"]
    assert "如果你把你的想法、草稿写出来" in last["content"]


def test_generated_draft_after_gate(monkeypatch):
    _fake(monkeypatch, "【局部参考】可以围绕注意资源竞争展开一小段。")
    session = create_session()
    asyncio.run(
        assist(
            session,
            "我认为通知频率越高，连续学习时段的专注时长越短，因为注意力会被反复拉回。",
            "claim",
        )
    )
    asyncio.run(
        assist(
            session,
            "我的想法是：通知频率越高，注意力被拉回次数越多，连续阅读时长就越短；"
            "请根据这段想法，帮我整理成参考草稿片段。",
            "claim",
        )
    )

    last = _last_ai(session)
    assert session["gate"]["dialectic_rounds"] == 1
    assert last["content_type"] == "generated_draft"
    assert "AI参考草稿素材" in last["content"]
    assert "已生成AI参考草稿" in last["content"]
    assert last["copy_unlocked"] is False


def test_guide_copy_is_direct_and_logged(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(assist(session, "我认为通知会降低专注，因为注意力会被反复打断。", "claim"))
    last = _last_ai(session)

    result = request_copy(session, last["id"])
    assert result["requires_test"] is False
    assert result["content_type"] == "guide"
    assert session["log"]["copy_events"][-1]["unlock_result"] == "success"


def test_scaffold_copy_requires_micro_test(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(assist(session, "直接帮我写", "claim"))
    asyncio.run(assist(session, "还是不会，直接写", "claim"))
    last = _last_ai(session)

    copy = request_copy(session, last["id"])
    assert copy["requires_test"] is True
    assert copy["forced"] is False
    assert session["log"]["copy_events"][-1]["unlock_result"] == "pending"

    result = submit_micro_test(session, last["id"], "bounds", SPECIFIC, copy["event_id"])
    assert result["status"] == "unlock"
    assert last["copy_unlocked"] is True
    event = session["log"]["copy_events"][-1]
    assert event["unlock_result"] == "success"
    assert event["answer"] == SPECIFIC
    assert event["test_question"]


def test_generated_draft_forced_and_refuse(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(
        assist(session, "我认为通知频率越高，专注时长越短，因为注意力会被反复拉回。", "claim")
    )
    asyncio.run(
        assist(
            session,
            "我的想法是：通知频率越高，注意力被拉回次数越多，连续阅读时长就越短；"
            "请根据这段想法，帮我整理成参考草稿片段。",
            "claim",
        )
    )
    last = _last_ai(session)

    copy = request_copy(session, last["id"])
    assert copy["requires_test"] is True
    assert copy["forced"] is True

    refuse_micro_test(session, last["id"], copy["event_id"])
    event = session["log"]["copy_events"][-1]
    assert event["unlock_result"] == "failed"
    assert event["refused"] is True
    assert last["copy_unlocked"] is False


def test_export_contains_all_sections_and_no_secret(monkeypatch):
    _fake(monkeypatch)
    session = create_session()
    asyncio.run(
        assist(session, "我认为通知频率越高，专注时长越短，因为注意力会被反复拉回。", "claim")
    )
    asyncio.run(
        assist(
            session,
            "我的想法是：通知频率越高，注意力被拉回次数越多，连续阅读时长就越短；"
            "请根据这段想法，帮我整理成参考草稿片段。",
            "claim",
        )
    )
    last = _last_ai(session)
    copy = request_copy(session, last["id"])
    submit_micro_test(session, last["id"], "bounds", SPECIFIC, copy["event_id"])
    update_plan(
        session,
        {"question": "通知频率是否影响连续阅读？", "evidence": "三篇实验研究", "doubts": "", "next_step": ""},
    )

    exported = export_session(session)
    html = exported["html"]
    doc = exported["json"]

    for marker in ("完整对话记录", "研究规划单", "复制与微测试日志", "风险审查清单", "本工具仅记录界面复制按钮操作"):
        assert marker in html
    assert "通知频率是否影响连续阅读？" in html
    assert SPECIFIC in html
    assert "generated_draft" in html
    assert "AI参考草稿素材" in html
    assert "sk-" not in html
    assert "sk-" not in json.dumps(doc, ensure_ascii=False)
    assert doc["plan"]["empty"] is False
    assert doc["conversation"]
    assert doc["copy_events"]
    assert len(doc["risk_checklist"]) == 5


def test_export_empty_plan_note():
    session = create_session()
    doc = export_session(session)["json"]
    assert doc["plan"]["empty"] is True
    assert "本会话未填写规划单" in export_session(session)["html"]


def test_prefill_plan_uses_user_messages_only(monkeypatch):
    captured = {}

    async def fake(messages, **kwargs):
        captured["messages"] = messages
        return '{"question":"Q","evidence":"E","doubts":"D","next_step":"N"}'

    monkeypatch.setattr(llm, "chat_completion", fake)
    session = create_session()
    session["messages"].append(
        {"id": "u1", "role": "user", "kind": "user", "content": "我的问题是什么？", "ts": "t"}
    )
    session["messages"].append(
        {"id": "a1", "role": "assistant", "kind": "analysis", "content": "AI 回复不应被提取", "ts": "t"}
    )

    result = asyncio.run(prefill_plan(session))
    assert result["fields"]["question"] == "Q"
    assert result["fields"]["next_step"] == "N"
    joined = captured["messages"][-1]["content"]
    assert "我的问题是什么" in joined
    assert "AI 回复不应被提取" not in joined


def test_public_session_has_five_modules(monkeypatch):
    session = create_session()
    public = public_session(session)
    assert [m["key"] for m in public["modules"]] == [
        "question",
        "literature",
        "claim",
        "evidence",
        "logic",
    ]
    assert public["runtime"]["llm"] == "deepseek"
    assert "plan" in public


def test_missing_key_raises_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "siche_deepseek_api_key", "")

    async def _run():
        await chat_completion([{"role": "user", "content": "hi"}])

    try:
        asyncio.run(_run())
    except LLMNotConfigured as exc:
        assert "SICHE_DEEPSEEK_API_KEY" in str(exc)
    else:
        raise AssertionError("应抛出 LLMNotConfigured")
