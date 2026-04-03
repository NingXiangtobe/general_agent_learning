from .os_cmd import powershell
from .file_ops import read_file, write_file, edit_file
from .web import web_search
from .skills_tool import load_skill
from .memory_tool import compact
from .plan import update_plan, get_plan
from .bg_tools import background_run, check_background
from .delegation import dispatch_workers

# 统合所有工具，暴露给 Lead Agent
TOOLS = [
    powershell, read_file, write_file, edit_file, load_skill, compact,
    update_plan, dispatch_workers, get_plan, background_run, check_background, web_search
]
TOOL_MAP = {t.name: t for t in TOOLS}