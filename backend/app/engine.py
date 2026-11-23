from __future__ import annotations

import html as html_lib
import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app import llm
from app.config import settings
from app.prompts import MODULE_ORDER, MODULES, build_system_prompt
from app.rules.copy_lock import COPY_LOCK_DISCLAIMER, OPTIONS, evaluate_micro_test
from app.rules.delegation import advance_stage, is_delegation_request
from app.rules.draft_gate import (
    draft_allowed,
    is_polish_request,
    update_gate,
)
from app.rules.textutil import char_count, strip_markdown

PLAN_KEYS = ("question", "evidence", "doubts", "next_step")
PLAN_LABELS = {
    "question": "我的问题",
    "evidence": "当前已有的证据",
    "doubts": "尚存疑点 / 待思考",
    "next_step": "下一步打算做什么",
}
PLAN_PLACEHOLDERS = {
    "question": "写下你的核心研究问题",
    "evidence": "整理你手上已有的资料、观点、证据",
    "doubts": "还没想明白、有待辨析的问题",
    "next_step": "接下来计划完成的思考或任务",
}

RISK_CHECKLIST = [
    ("信息真实性", "AI 给出的文献、数据与事实是否已由你核验来源？"),
    ("研究逻辑一致性", "问题、证据与结论是否在回答同一件事？"),
    ("独立理解", "你能否不看生成文本，用自己的话复述当前判断？"),
    ("批判性判断", "你是否写下了对立可能或适用边界？"),
    ("成果归属", "核心观点与结论是否确为你本人的思考？"),
]

DRAFT_WARNING = "【⚠️以下为AI参考草稿素材，仅用于写作参照，不能直接复制提交作业，需要你结合自身研究重新改写】"
DRAFT_REMINDER = "⚠️已生成AI参考草稿，请查阅左侧风险审查清单开展自我核查"

STAGE4_TEXT = (
    "你已经连续多次要求我直接产出成品。按照「思拆」的定位，我不能替代你完成写作或决策，"
    "也不会继续提供支架。\n\n"
    "现在只有两个选择：\n"
    "① 缩小问题，拆分小点继续思考；\n"
    "② 保存进度退出。\n\n"
    "如果你把你的想法、草稿写出来给到我，我就可以尝试为你生成一份仅供参考的草稿片段。"
)

OPTION_QUESTIONS = {
    "tweak": "指出一处你准备结合自身研究修改的句子或判断，并说明为什么。",
    "contrary": "写出一条与刚才 AI 输出不同的角度或反例，并说明它可能成立的条件。",
    "bounds": "分别写出这套说法大概成立、以及可能不成立的一个具体条件。",
}

SCAFFOLD_MARKERS = ("填：", "（填", "填空", "骨架", "格子", "句式支架", "【仅思路示范", "____", "待填", "（空）")

EXTRACT_SYSTEM = """你是信息提取器。只依据用户发言，提取用户自己写出的内容，输出严格 JSON。
规则：
1. question：用户想研究的问题。若用户只是在向 AI 提要求（如“帮我整理”“直接写”“据此写摘要”），不要当作研究问题。
2. evidence：用户已经写出的资料、观点、判断、证据，可以合并多条。
3. doubts：用户明确说过不确定、困惑、还没想明白的点。不要推断。
4. next_step：用户明确说打算做什么。不要把“帮我整理”“帮我润色”之类的请求当作下一步。
5. 没有对应内容就填空字符串；禁止编造，禁止元评论，禁止写“用户未提供”。
JSON 结构：{"question":"...","evidence":"...","doubts":"...","next_step":"..."}
不要输出 JSON 以外的任何文字。"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _empty_plan() -> dict:
    return {k: "" for k in PLAN_KEYS}


def _empty_gate() -> dict:
    return {
        "user_thinking_count": 0,
        "dialectic_rounds": 0,
        "draft_iterations": 0,
        "polish_iterations": 0,
        "last_ai_was_polish": False,
    }


def create_session(task_type: str = "general", topic: str = "") -> dict:
    topic = (topic or "").strip()
    session: dict[str, Any] = {
        "id": _new_id(),
        "created_at": _now(),
        "task_type": task_type,
        "topic": topic,
        "current_module": "general",
        "messages": [
            {
                "id": _new_id(),
                "role": "system",
                "kind": "welcome",
                "content": (
                    "我是思拆。你可以直接选一个模块，写下草稿、判断或真实困惑；不选模块也可以。\n\n"
                    "我不会直接代写完整论文或大章节。只有在你展现独立思考、完成一轮思辨来回、"
                    "并明确请求参考片段时，才会生成局部参考草稿；点击复制前必须完成批判性微测试。"
                ),
                "content_type": "guide",
                "copyable": True,
                "copy_unlocked": True,
                "substantive": False,
                "module": "general",
                "stage": 0,
                "ts": _now(),
            }
        ],
        "plan": _empty_plan(),
        "gate": _empty_gate(),
        "delegation_stage": 0,
        "log": {
            "user_inputs": [],
            "module_usage": {},
            "copy_events": [],
        },
        "ui": {
            "copy_test_message_id": "",
            "copy_test_followup": False,
            "copy_lock_disclaimer": COPY_LOCK_DISCLAIMER,
        },
    }
    return session


def _reset_ui(session: dict) -> None:
    session["ui"]["copy_test_message_id"] = ""
    session["ui"]["copy_test_followup"] = False


def _append_message(session: dict, **fields) -> dict:
    message = {
        "id": _new_id(),
        "ts": _now(),
        "module": session["current_module"],
        "stage": session.get("delegation_stage", 0),
        "copyable": True,
        "substantive": False,
        "copy_unlocked": True,
        "content_type": "guide",
        **fields,
    }
    session["messages"].append(message)
    return message


def _find_message(session: dict, message_id: str) -> dict:
    for message in session["messages"]:
        if message["id"] == message_id:
            return message
    raise KeyError("消息不存在")


def _last_ai_type(session: dict) -> str:
    for message in reversed(session["messages"]):
        if message["role"] == "assistant" and message.get("kind") != "welcome":
            return message.get("content_type", "guide")
    return ""


def _record_user_input(session: dict, text: str) -> None:
    session["log"]["user_inputs"].append(
        {"text": text, "ts": _now(), "module": session["current_module"]}
    )
    usage = session["log"]["module_usage"]
    usage[session["current_module"]] = usage.get(session["current_module"], 0) + 1


def _build_messages(session: dict, stage: int, allow_draft: bool) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for message in session["messages"]:
        if message.get("role") not in ("user", "assistant"):
            continue
        if message.get("kind") in ("welcome", "stage4"):
            continue
        content = (message.get("content") or "").strip()[:2000]
        if content:
            history.append({"role": message["role"], "content": content})
    history = history[-max(1, settings.siche_history_limit) :]
    return [
        {"role": "system", "content": build_system_prompt(session["current_module"], stage, allow_draft)},
        *history,
    ]


def _classify_content_type(stage: int, content: str) -> str:
    """阶段 2/3 必为 scaffold；其他阶段出现填空/骨架/示范标记也按 scaffold 处理。"""
    if stage in (2, 3):
        return "scaffold"
    if any(marker in (content or "") for marker in SCAFFOLD_MARKERS):
        return "scaffold"
    return "guide"


def _ensure_draft_warning(content: str) -> str:
    if "AI参考草稿素材" not in content:
        content = DRAFT_WARNING + "\n\n" + content
    if "已生成AI参考草稿" not in content:
        content = content.rstrip() + "\n\n" + DRAFT_REMINDER
    return content


async def assist(session: dict, message: str, module: str | None = None) -> dict:
    text = (message or "").strip()
    if not text:
        return session

    _reset_ui(session)
    if module in MODULES:
        session["current_module"] = module
    if not session["topic"]:
        session["topic"] = text[:30]

    session["messages"].append(
        {
            "id": _new_id(),
            "role": "user",
            "kind": "user",
            "content": text,
            "content_type": "user",
            "copyable": True,
            "copy_unlocked": True,
            "substantive": False,
            "module": session["current_module"],
            "stage": session.get("delegation_stage", 0),
            "ts": _now(),
        }
    )
    _record_user_input(session, text)

    previous_type = _last_ai_type(session)
    gate_before = deepcopy(session["gate"])
    update_gate(session, text, previous_type)

    if draft_allowed(session, text):
        session["delegation_stage"] = 0
        try:
            content = await llm.chat_completion(_build_messages(session, 0, True))
        except Exception:
            session["gate"] = gate_before
            raise
        content = _ensure_draft_warning(strip_markdown(content))
        _append_message(
            session,
            role="assistant",
            kind="draft",
            content=content,
            content_type="generated_draft",
            substantive=True,
            copyable=True,
            copy_unlocked=False,
        )
        session["gate"]["last_ai_was_polish"] = False
        return session

    previous_stage = int(session.get("delegation_stage", 0) or 0)
    stage = advance_stage(session, text)
    if stage >= 4:
        _append_message(
            session,
            role="assistant",
            kind="stage4",
            content=STAGE4_TEXT,
            content_type="guide",
            options=["缩小问题", "保存进度退出"],
        )
        return session

    try:
        content = await llm.chat_completion(_build_messages(session, stage, False))
    except Exception:
        session["delegation_stage"] = previous_stage
        session["gate"] = gate_before
        raise

    content = strip_markdown(content)
    content_type = _classify_content_type(stage, content)
    _append_message(
        session,
        role="assistant",
        kind="analysis",
        content=content,
        content_type=content_type,
        substantive=True,
        copyable=True,
        copy_unlocked=(content_type == "guide"),
    )
    session["gate"]["last_ai_was_polish"] = bool(
        is_polish_request(text) and content_type == "guide"
    )
    return session


def _find_copy_event(session: dict, message_id: str, event_id: str | None = None) -> dict | None:
    events = session["log"]["copy_events"]
    if event_id:
        for event in events:
            if event["id"] == event_id:
                return event
    for event in reversed(events):
        if event["message_id"] == message_id and event["unlock_result"] == "pending":
            return event
    return None


def request_copy(session: dict, message_id: str) -> dict:
    message = _find_message(session, message_id)
    if message.get("role") != "assistant":
        raise KeyError("只能复制思拆的回复")

    content_type = message.get("content_type", "guide")
    requires_test = content_type in ("scaffold", "generated_draft") and not message.get("copy_unlocked")
    event = {
        "id": _new_id(),
        "ts": _now(),
        "message_id": message_id,
        "summary": (message.get("content") or "")[:80],
        "content_type": content_type,
        "requires_test": requires_test,
        "test_question": "",
        "test_option": "",
        "answer": "",
        "unlock_result": "pending" if requires_test else "success",
        "refused": False,
    }
    session["log"]["copy_events"].append(event)

    if not requires_test:
        return {
            "requires_test": False,
            "event_id": event["id"],
            "content_type": content_type,
            "content": message.get("content", ""),
        }

    session["ui"]["copy_test_message_id"] = message_id
    session["ui"]["copy_test_followup"] = False
    return {
        "requires_test": True,
        "event_id": event["id"],
        "content_type": content_type,
        "forced": content_type == "generated_draft",
        "disclaimer": COPY_LOCK_DISCLAIMER,
    }


def submit_micro_test(
    session: dict,
    message_id: str,
    option: str,
    text: str,
    event_id: str | None = None,
) -> dict:
    message = _find_message(session, message_id)
    if message.get("role") != "assistant":
        raise KeyError("该消息不需要复制审查")

    event = _find_copy_event(session, message_id, event_id)
    if event is None:
        event = {
            "id": _new_id(),
            "ts": _now(),
            "message_id": message_id,
            "summary": (message.get("content") or "")[:80],
            "content_type": message.get("content_type", "guide"),
            "requires_test": True,
            "test_question": "",
            "test_option": "",
            "answer": "",
            "unlock_result": "pending",
            "refused": False,
        }
        session["log"]["copy_events"].append(event)

    is_followup = bool(
        session["ui"].get("copy_test_followup")
        and session["ui"].get("copy_test_message_id") == message_id
    )
    result = evaluate_micro_test(text, option, is_followup=is_followup)

    event["test_question"] = OPTION_QUESTIONS.get(option, "")
    event["test_option"] = OPTIONS.get(option, option)
    event["answer"] = text
    event["unlock_result"] = "success" if result.status == "unlock" else "failed"

    if result.status == "followup":
        session["ui"]["copy_test_message_id"] = message_id
        session["ui"]["copy_test_followup"] = True
        return {
            "status": "followup",
            "reason": result.reason,
            "followup_question": result.followup_question,
            "unlocked": False,
            "event_id": event["id"],
        }

    if result.status == "unlock":
        message["copy_unlocked"] = True
        session["ui"]["copy_test_message_id"] = ""
        session["ui"]["copy_test_followup"] = False
        return {
            "status": "unlock",
            "reason": result.reason,
            "followup_question": "",
            "unlocked": True,
            "content": message.get("content", ""),
            "event_id": event["id"],
        }

    return {
        "status": "locked",
        "reason": result.reason,
        "followup_question": "",
        "unlocked": False,
        "event_id": event["id"],
    }


def refuse_micro_test(session: dict, message_id: str, event_id: str | None = None) -> dict:
    _find_message(session, message_id)
    event = _find_copy_event(session, message_id, event_id)
    if event is not None:
        event["unlock_result"] = "failed"
        event["refused"] = True
    session["ui"]["copy_test_message_id"] = ""
    session["ui"]["copy_test_followup"] = False
    return {
        "status": "refused",
        "reason": "你选择暂不完成微测试。本条回复的一键复制保持锁定，文本仍可阅读。",
        "event_id": event["id"] if event else "",
    }


def update_plan(session: dict, fields: dict) -> dict:
    for key in PLAN_KEYS:
        if key in fields:
            session["plan"][key] = (fields.get(key) or "").strip()
    return session


def _parse_json_object(raw: str) -> dict:
    content = (raw or "").strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no json object")
    return json.loads(content[start : end + 1])


def _fallback_prefill(user_texts: list[str]) -> dict:
    fields = _empty_plan()
    for text in user_texts:
        raw = (text or "").strip()
        if not raw:
            continue
        if not fields["question"] and any(k in raw for k in ("问题", "想问", "研究问题")):
            fields["question"] = raw
        elif not fields["evidence"] and any(k in raw for k in ("证据", "数据", "文献", "观察到")):
            fields["evidence"] = raw
        elif not fields["doubts"] and any(k in raw for k in ("困惑", "不确定", "疑点", "还没想")):
            fields["doubts"] = raw
        elif not fields["next_step"] and any(k in raw for k in ("下一步", "打算", "准备")):
            fields["next_step"] = raw
    return fields


async def prefill_plan(session: dict) -> dict:
    user_texts = [m["content"] for m in session["messages"] if m.get("role") == "user"]
    has_existing = any((session["plan"].get(k) or "").strip() for k in PLAN_KEYS)
    if not user_texts:
        return {"fields": _empty_plan(), "has_existing": has_existing}

    fields = _empty_plan()
    try:
        raw = await llm.chat_completion(
            [
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": "\n\n".join(user_texts)},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        data = _parse_json_object(raw)
        for key in PLAN_KEYS:
            fields[key] = str(data.get(key) or "").strip()
    except Exception:
        fields = _fallback_prefill(user_texts)

    return {"fields": fields, "has_existing": has_existing}


def _export_plan(session: dict) -> dict:
    values = {key: (session["plan"].get(key) or "").strip() for key in PLAN_KEYS}
    if not any(values.values()):
        return {"empty": True, "note": "本会话未填写规划单", "fields": {}}
    return {
        "empty": False,
        "note": "",
        "fields": [
            {"label": PLAN_LABELS[key], "content": values[key] or "暂无填写内容"}
            for key in PLAN_KEYS
        ],
    }


def _export_conversation(session: dict) -> list[dict]:
    items = []
    for message in session["messages"]:
        role = "用户" if message.get("role") == "user" else "AI"
        item = {
            "role": role,
            "timestamp": message.get("ts", ""),
            "content": message.get("content", ""),
        }
        if role == "AI":
            item["content_type"] = message.get("content_type", "guide")
        items.append(item)
    return items


def _render_export_html(doc: dict) -> str:
    esc = html_lib.escape
    meta = doc["meta"]
    convo = doc["conversation"]
    plan = doc["plan"]
    events = doc["copy_events"]
    risk = doc["risk_checklist"]

    convo_html = []
    for item in convo:
        ct = f'<span class="ct">{esc(item["content_type"])}</span>' if item.get("content_type") else ""
        convo_html.append(
            f'<article class="msg {("user" if item["role"] == "用户" else "ai")}">'
            f'<div class="meta">【{esc(item["role"])}】{ct} {esc(item["timestamp"])}</div>'
            f'<div class="body">{esc(item["content"])}</div></article>'
        )

    if plan["empty"]:
        plan_html = f'<p class="muted">{esc(plan["note"])}</p>'
    else:
        rows = "".join(
            f'<tr><th>{esc(row["label"])}</th><td>{esc(row["content"])}</td></tr>'
            for row in plan["fields"]
        )
        plan_html = f'<table class="plan">{rows}</table>'

    if events:
        event_rows = []
        for event in events:
            event_rows.append(
                "<tr>"
                f"<td>{esc(str(event.get('ts', '')))}</td>"
                f"<td>{esc(str(event.get('summary', '')))}</td>"
                f"<td>{esc(str(event.get('content_type', '')))}</td>"
                f"<td>{'是' if event.get('requires_test') else '否'}</td>"
                f"<td>{esc(str(event.get('test_question') or '—'))}</td>"
                f"<td>{esc(str(event.get('answer') or '—'))}</td>"
                f"<td>{esc(str(event.get('unlock_result', '')))}</td>"
                "</tr>"
            )
        events_html = (
            '<details><summary>复制与微测试日志（点击展开）</summary>'
            '<table class="events"><thead><tr>'
            "<th>时间</th><th>AI消息摘要</th><th>content_type</th><th>触发微测试</th>"
            "<th>微测试题目</th><th>用户完整作答</th><th>解锁结果</th>"
            "</tr></thead><tbody>"
            + "".join(event_rows)
            + "</tbody></table></details>"
        )
    else:
        events_html = '<p class="muted">本会话未点击界面复制按钮。</p>'

    risk_html = "".join(
        f"<li><strong>{esc(title)}</strong><br>{esc(hint)}</li>" for title, hint in risk
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{esc(meta["title"])} · 思拆会话记录</title>
<style>
  body {{ margin: 0; background: #f3ebdd; color: #1c1814; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 40px 24px 80px; }}
  h1, h2 {{ font-family: "Songti SC", "SimSun", serif; font-weight: 600; }}
  h1 {{ font-size: 32px; margin: 0 0 8px; }}
  h2 {{ font-size: 22px; margin: 36px 0 12px; border-bottom: 1px solid rgba(28,24,20,.18); padding-bottom: 6px; }}
  .meta-table {{ border-collapse: collapse; font-size: 14px; }}
  .meta-table th {{ text-align: left; padding: 4px 16px 4px 0; color: #5a5248; font-weight: 500; }}
  .msg {{ border: 1px solid rgba(28,24,20,.12); background: #fbf7f0; padding: 12px 16px; margin: 10px 0; }}
  .msg.user {{ border-color: rgba(31,58,95,.3); background: #fff; margin-left: 32px; }}
  .msg.ai {{ margin-right: 16px; }}
  .msg .meta {{ font-size: 12px; color: #5a5248; margin-bottom: 6px; }}
  .msg .body {{ white-space: pre-wrap; line-height: 1.8; }}
  .ct {{ color: #b83a2a; margin-left: 6px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid rgba(28,24,20,.15); padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #e9dfcd; font-weight: 600; }}
  .plan th {{ width: 180px; }}
  .events td {{ white-space: pre-wrap; }}
  .muted {{ color: #5a5248; }}
  details summary {{ cursor: pointer; font-weight: 600; margin: 8px 0; }}
  ul {{ line-height: 1.9; }}
  .note {{ background: #fbf7f0; border-left: 3px solid #b83a2a; padding: 12px 16px; }}
</style>
</head>
<body>
<main>
  <h1>{esc(meta["title"])}</h1>
  <table class="meta-table">
    <tr><th>会话创建时间</th><td>{esc(meta["created_at"])}</td></tr>
    <tr><th>导出时间</th><td>{esc(meta["exported_at"])}</td></tr>
    <tr><th>工具说明</th><td>{esc(meta["tool_note"])}</td></tr>
  </table>

  <h2>完整对话记录</h2>
  {''.join(convo_html)}

  <h2>研究规划单</h2>
  {plan_html}

  <h2>复制与微测试日志</h2>
  {events_html}

  <h2>风险审查清单</h2>
  <ul>{risk_html}</ul>

  <h2>备注</h2>
  <p class="note">{esc(doc["note"])}</p>
</main>
</body>
</html>"""


def export_session(session: dict) -> dict:
    exported_at = _now()
    plan = _export_plan(session)
    conversation = _export_conversation(session)
    events = deepcopy(session["log"].get("copy_events", []))
    risk = [{"title": title, "hint": hint} for title, hint in RISK_CHECKLIST]
    meta = {
        "title": session["topic"] or "未命名写作任务",
        "created_at": session["created_at"],
        "exported_at": exported_at,
        "product": "思拆",
        "tool_note": "本记录由思拆生成，用于课程作业过程档案。generated_draft 代表 AI 参考草稿，不是用户原创正文。",
    }
    note = (
        "本工具仅记录界面复制按钮操作；手动选中网页文字、截图无法被程序记录。"
        "微测试作答不校验对错，原样保存，交由授课老师评估反思质量。"
    )
    doc = {
        "meta": meta,
        "conversation": conversation,
        "plan": plan,
        "copy_events": events,
        "risk_checklist": risk,
        "note": note,
    }
    return {"html": _render_export_html(doc), "json": doc}


def public_session(session: dict) -> dict:
    return {
        **session,
        "modules": [
            {"key": key, "label": MODULES[key]["label"], "hint": MODULES[key]["hint"]}
            for key in MODULE_ORDER
        ],
        "runtime": {
            "llm": "deepseek",
            "model": settings.siche_deepseek_model,
            "configured": settings.llm_configured,
        },
    }
