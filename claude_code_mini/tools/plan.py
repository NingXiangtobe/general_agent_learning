from typing import List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from claude_code_mini.core.config import PLAN_FILE
from claude_code_mini.core.locks import FILE_LOCK_MGR
from claude_code_mini.tools.file_ops import smart_read_text


class PlanNode(BaseModel):
    id: str = Field(description="Task ID")
    desc: str = Field(description="Task detail")
    deps: List[str] = Field(description="Dependencies")
    status: str = Field(description="pending, in_progress, completed")


class PlanInput(BaseModel):
    tasks: List[PlanNode]


def read_plan_content() -> str:
    """内部普通函数：严谨读取 PLAN.md"""
    return smart_read_text(PLAN_FILE) or "No plan yet."

@tool
def get_plan() -> str:
    """
    get PLAN.md content
    """
    return read_plan_content()

@tool(args_schema=PlanInput)
def update_plan(tasks: List[PlanNode]) -> str:
    """Update PLAN.md."""
    lines = ["# PROJECT PLAN\n"]
    for t in tasks:
        m = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(t.status, "[ ]")
        lines.append(f"- {m} [ID: {t.id}] [DEPS: {', '.join(t.deps) if t.deps else 'none'}] {t.desc}")
    content = "\n".join(lines)
    with FILE_LOCK_MGR.get_lock(str(PLAN_FILE)):
        PLAN_FILE.write_text(content, encoding="utf-8")
    return "PLAN.md updated."
