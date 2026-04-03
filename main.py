import sys
from langchain_core.messages import HumanMessage, AIMessage

from claude_code_mini.core.config import PLAN_FILE, HOT_STATE_FILE
from claude_code_mini.state.persistence import load_hot_state, append_cold_log, save_hot_state, \
    reset_workspace_for_new_task
from claude_code_mini.tools.plan import read_plan_content
from claude_code_mini.agents.coordinator import agent_loop

if __name__ == "__main__":
    print("--------------------原神启动--------------------------------")

    # 1. 启动时先加载热记忆
    history = load_hot_state()

    # 2. 探针：检查任务状态
    has_legacy_state = False
    plan_content = ""

    if PLAN_FILE.exists():
        plan_content = read_plan_content().strip()
        # 如果计划不为空，且还有没打 [x] 的任务，说明上次是异常中断的
        if plan_content and ("[ ]" in plan_content or "[>]" in plan_content):
            has_legacy_state = True

    # 3. 拦截器与清理分流
    if has_legacy_state:
        print("\n\033[41;37m [系统警告] 检测到上次运行有未完成的任务！ \033[0m")
        print("当前 PLAN.md 中存在待办事项，详情如下：\n")

        print("\033[33m" + "=" * 50)
        print(plan_content)
        print("=" * 50 + "\033[0m\n")

        print("  - 输入 'c' 键：加载热记忆，继续完成上次的旧任务")
        print("  - 直接输入新需求：物理销毁旧任务和热记忆，开启绝对干净的新会话\n")

        try:
            first_input = input("\033[36m输入 >> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

        if first_input.lower() == 'c':
            print("\033[32m[恢复] 正在复用热记忆，恢复旧任务上下文...\033[0m")
            # 此时 history 变量里已经装满了 load_hot_state() 拿到的记忆
            history.append(HumanMessage(content="Please review the PLAN.md and continue unfinished tasks."))
            agent_loop(history)
        elif first_input.lower() in ("q", "exit", ""):
            sys.exit(0)
        else:
            print("\033[35m[重置] 正在执行物理清理协议...\033[0m")
            history = reset_workspace_for_new_task()

            # 把用户的输入直接作为新会话的起点
            query = first_input
            history.append(HumanMessage(content=query))
            append_cold_log("user", query)
            save_hot_state(history)
            agent_loop(history)

    else:
        # 如果没有任何未完成的任务（全部 [x] 了，或者压根没计划）
        # 只要存在残留的文件或内存记忆，直接静默清理！
        if history or PLAN_FILE.exists() or HOT_STATE_FILE.exists():
            print("\033[32m[初始化] 上次任务已完成或为空，正在自动清理旧热记忆，准备就绪。\033[0m")
            history = reset_workspace_for_new_task()

    # ==== 下面是正常的、没有旧任务干扰的循环 ====
    while True:
        try:
            query = input("\033[36m输入 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break

        if query.strip().lower() in ("q", "exit", ""):
            break

        history.append(HumanMessage(content=query))
        append_cold_log("user", query)
        save_hot_state(history)

        agent_loop(history)

        last_msg = history[-1]
        if isinstance(last_msg, AIMessage) and last_msg.content:
            print(f"\n{last_msg.content}")