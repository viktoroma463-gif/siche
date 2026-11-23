from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateSessionIn(BaseModel):
    task_type: str = "general"
    topic: str = Field(default="", max_length=200)


class ModuleIn(BaseModel):
    module: str


class AssistIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    module: str = "general"


class MicroTestIn(BaseModel):
    option: Literal["tweak", "contrary", "bounds"]
    text: str = ""
    event_id: str = ""


class PlanIn(BaseModel):
    question: str = ""
    evidence: str = ""
    doubts: str = ""
    next_step: str = ""


class SessionOut(BaseModel):
    session: dict[str, Any]
