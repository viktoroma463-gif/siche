from dataclasses import dataclass

from app.rules.textutil import char_count

MICRO_TEST_MIN = 80
MICRO_TEST_MAX = 300

OPTIONS = {
    "tweak": "接受并微调",
    "contrary": "补充对立思考",
    "bounds": "指出适用边界",
}


@dataclass
class MicroTestResult:
    status: str  # unlock | locked
    reason: str = ""
    followup_question: str = ""


def evaluate_micro_test(text: str, option: str, is_followup: bool = False) -> MicroTestResult:
    """只校验选项与 80–300 字，不校验作答对错；敷衍内容原样保存导出。"""
    raw = (text or "").strip()
    n = char_count(raw)
    if option not in OPTIONS:
        return MicroTestResult(status="locked", reason="请选择三项微测试之一后再提交。")
    if n < MICRO_TEST_MIN:
        return MicroTestResult(
            status="locked",
            reason=f"请将辨析写到至少 {MICRO_TEST_MIN} 字（当前 {n} 字），以便完成低负荷审查。",
        )
    if n > MICRO_TEST_MAX:
        return MicroTestResult(
            status="locked",
            reason=f"请将辨析控制在 {MICRO_TEST_MAX} 字以内（当前 {n} 字），保持低负荷微测试。",
        )
    return MicroTestResult(status="unlock", reason="已完成批判性微测试，对话内复制已解锁。")


COPY_LOCK_DISCLAIMER = (
    "本内容为认知辅助支架，不可以直接粘贴进作业/论文；"
    "截图无法规避该机制，本设计目的唤起自主反思。"
)
