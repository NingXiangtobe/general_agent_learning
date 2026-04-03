from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage

from agent.core.config import base_llm, THRESHOLD_CHARS
from agent.state.persistence import save_hot_state, append_cold_log
from agent.state.memory import micro_compact, estimate_size, auto_compact
from agent.services.background import BG
from agent.tools import TOOLS, TOOL_MAP
from agent.agents.prompts import build_dynamic_system_prompt
from agent.tools.plan import read_plan_content

# 绑定全局工具
llm = base_llm.bind_tools(TOOLS)


def agent_loop(message: List[BaseMessage]):
    rounds_since_dispatch = 0
    has_reflected = False

    while True:
        micro_compact(message)
        if estimate_size(message) > THRESHOLD_CHARS:
            print("\n\033[31m[系统告警] Context size threshold exceeded. Auto-compacting...\033[0m")
            message[:] = auto_compact(message)

        notifs = BG.drain()
        if notifs:
            txt = "\n".join(f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs)
            message.append(HumanMessage(content=f"<background-results>\n{txt}\n</background-results>"))
            message.append(AIMessage(content="Noted background results."))

        response = llm.invoke([build_dynamic_system_prompt()] + message)
        message.append(response)

        append_cold_log("coordinator", response.content or f"[Tool Calls]: {response.tool_calls}")
        save_hot_state(message)

        if not response.tool_calls:
            if not has_reflected:
                print("\033[35m[系统干预] Agent 试图结束任务，触发最终审查 (Reflection)...\033[0m")

                # 严谨获取原始问题（过滤掉 reminder 和 reflection 标签）
                last_human_query = next(
                    (msg.content for msg in reversed(message)
                     if isinstance(msg,
                                   HumanMessage) and "<reminder>" not in msg.content and "<reflection>" not in msg.content),
                    "无"
                )

                reflection_prompt = f"""<reflection>
            You are about to finish the task. Before you stop, critically review your work against the 【CURRENT PLAN STATUS】:
            【CURRENT PLAN STATUS】:
             {read_plan_content()}

             【LAST USER REQUEST】:
             {last_human_query}

            CRITICAL CHECKLIST:
            1. Are there any currently tasks NOT marked as completed [x]?
            2. If there are any [ ] or [>], you MUST use `dispatch_workers` or manual tools to finish them.
            3. If the PLAN is fully checked [x] but the user's request "{last_human_query}" is still not met,
             use 'update_plan' to update the PLAN first.
            4. Don't be too strict! Unless the 【CURRENT PLAN STATUS】 is significantly different from the 【LAST USER REQUEST】, 
             if all tasks are marked as completed, it's fine.

            If you are sure the physical state likely matches the request, 
            provide a summary and end with: "ALL_TASKS_COMPLETED". Otherwise, KEEP WORKING.
            </reflection>"""

                message.append(HumanMessage(content=reflection_prompt))
                has_reflected = True
                continue  # 强制进入下一轮 LLM 思考，不准退出
            else:
                if "ALL_TASKS_COMPLETED" in response.content:
                    print("\033[32m[审查通过] Agent 确认所有任务圆满完成。\033[0m")
                else:
                    print("\033[33m[审查结束] Agent 提交了最终结果。\033[0m")
                break

        did_dispatch = False
        manual_compact_triggered = False

        for tool_call in response.tool_calls:
            has_reflected = False
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name in ["dispatch_workers", "update_plan"]:
                did_dispatch = True
            elif tool_name == "compact":
                manual_compact_triggered = True

            try:
                if tool_name in TOOL_MAP:
                    print(f"\033[33m> 开始执行 {tool_name}...\033[0m")
                    observation = TOOL_MAP[tool_name].invoke(tool_args)
                else:
                    observation = f"Unknown tool: {tool_name}"
            except Exception as e:
                observation = f"Tool Execution Error: {e}"

            print(f"执行结果: \n{str(observation)[:500]}")
            message.append(
                ToolMessage(
                    content=str(observation),
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )
            append_cold_log("coordinator",
                            f"TOOL: {tool_name}\nTOOL ARGS: {tool_args} \nTOOL RESULT: {str(observation)}")

            save_hot_state(message)

        if manual_compact_triggered:
            message[:] = auto_compact(message)

        rounds_since_dispatch = 0 if did_dispatch else rounds_since_dispatch + 1
        if rounds_since_dispatch >= 4:
            message.append(HumanMessage(
                content="""<reminder>
                You are stalling. 
                Check PLAN.md and call `dispatch_workers` if tasks are pending, or `update_plan` if missing dependencies.
                </reminder>"""))

            print("\033[35m[系统干预] 强制防跑题提醒：Check your PLAN.\033[0m")