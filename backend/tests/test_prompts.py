from app.prompts import BASE_SYSTEM, build_system_prompt
from app.rules.textutil import strip_markdown


def test_base_contains_core_positioning():
    assert "先独立、后协作、再审查" in BASE_SYSTEM
    assert "绝对不能直接代写完整论文" in BASE_SYSTEM
    assert "草稿生成解锁规则" in BASE_SYSTEM
    assert "分层引导" in BASE_SYSTEM
    assert "generated_draft" in BASE_SYSTEM


def test_base_forbids_markdown_and_requires_plain_format():
    assert "不要用粗体" in BASE_SYSTEM
    assert "【】标题" in BASE_SYSTEM


def test_module_and_stage_composition():
    prompt = build_system_prompt("literature", 2)
    assert "文献线索与检索" in prompt
    assert "第二层" in prompt
    assert "句式支架" in prompt


def test_draft_permission_is_injected():
    prompt = build_system_prompt("claim", 0, True)
    assert "草稿许可" in prompt
    assert "AI参考草稿素材" in prompt


def test_module_switch_changes_module_line():
    literature = build_system_prompt("literature", 0)
    claim = build_system_prompt("claim", 0)
    assert "【本轮所选模块】文献线索与检索" in literature
    assert "【本轮所选模块】核心观点探讨" in claim
    assert literature != claim


def test_strip_markdown_removes_symbols():
    raw = "### 标题\n\n**加粗**\n\n- 项目一\n- 项目二\n\n> 引用"
    cleaned = strip_markdown(raw)
    assert "#" not in cleaned
    assert "**" not in cleaned
    assert "\n- " not in cleaned
    assert "标题" in cleaned
    assert "项目一" in cleaned
