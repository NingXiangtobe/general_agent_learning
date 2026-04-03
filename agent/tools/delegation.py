import concurrent.futures
import re
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from agent.core.config import child_llm
from agent.core.locks import FILE_LOCK_MGR
from agent.state.persistence import append_cold_log, PLAN_FILE
from agent.tools.plan import read_plan_content
from agent.agents.prompts import SUBAGENT_SYSTEM_PROMPT

from agent.tools.os_cmd import powershell
from agent.tools.file_ops import read_file, write_file, edit_file
from agent.tools.skills_tool import load_skill
from agent.tools.web import web_search

CHILD_TOOLS = [powershell, read_file, write_file, edit_file, load_skill, web_search]
CHILD_TOOL_MAP = {t.name: t for t in CHILD_TOOLS}
llm = child_llm.bind_tools(CHILD_TOOLS)


def spawn_worker(task_id: str, task_desc: str) -> str:
    """Fully autonomous worker. No artifact sharing."""
    prompt = f"EXECUTE TASK: {task_id}\nDESCRIPTION: {task_desc}\nYou are autonomous. Solve this completely using your tools or skills."
    msgs = [HumanMessage(content=prompt)]

    for _ in range(15):
        resp = llm.invoke([SUBAGENT_SYSTEM_PROMPT] + msgs)
        msgs.append(resp)
        append_cold_log(f"worker_{task_id}", f"AI: {resp.content}")

        if not resp.tool_calls:
            return resp.content

        for tc in resp.tool_calls:
            tool_name = tc['name']
            obs = CHILD_TOOL_MAP[tool_name].invoke(tc['args']) if tool_name in CHILD_TOOL_MAP else "Tool missing."
            msgs.append(ToolMessage(content=str(obs), tool_call_id=tc['id'], name=tool_name))
            append_cold_log(f"worker_{task_id}",
                            f"Tool : {tool_name} \nTOOL ARGS : {tc['args']}\nTOOL RESULT: {str(obs)[:200]}")
    return "Timeout"


@tool
def dispatch_workers() -> str:
    """Run all ready autonomous tasks in parallel."""
    if not PLAN_FILE.exists(): return "No plan."

    with FILE_LOCK_MGR.get_lock(str(PLAN_FILE)):
        content = PLAN_FILE.read_text(encoding="utf-8")

    all_ready_candidates = re.findall(r"- \[(?: |\>)\] \[ID: (.*?)\] \[DEPS: (.*?)\] (.*)", content)
    completed_ids = set(re.findall(r"- \[x\] \[ID: (.*?)\]", content))

    ready_tasks = []
    for tid, deps, desc in all_ready_candidates:
        dep_list = [] if deps == "none" else [d.strip() for d in deps.split(",")]
        if all(d in completed_ids for d in dep_list):
            ready_tasks.append((tid, desc))

    if not ready_tasks:
        return "No tasks ready. (Ensure dependencies are marked [x])"

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exe:
        fs = {exe.submit(spawn_worker, t[0], t[1]): t[0] for t in ready_tasks}
        for f in concurrent.futures.as_completed(fs):
            tid = fs[f]
            try:
                res = f.result()
                results.append(f"Task {tid} completed: {res}")

                # 自动在黑板打勾
                with FILE_LOCK_MGR.get_lock(str(PLAN_FILE)):
                    curr = read_plan_content()
                    updated_curr = re.sub(
                        rf"- \[(?: |\>)\] \[ID: {tid}\]",
                        f"- [x] [ID: {tid}]",
                        curr
                    )
                    PLAN_FILE.write_text(updated_curr, encoding="utf-8")
            except Exception as e:
                results.append(f"Task {tid} failed: {e}")

    return "Batch execution summary:\n" + "\n".join(results)