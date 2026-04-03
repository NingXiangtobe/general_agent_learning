import json
import time
from typing import List
from langchain_core.messages import BaseMessage, SystemMessage, message_to_dict, messages_from_dict

from agent.core.config import HOT_STATE_FILE, COLD_LOG_FILE, PLAN_FILE
from agent.core.locks import FILE_LOCK_MGR


def append_cold_log(role: str, content: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with FILE_LOCK_MGR.get_lock(str(COLD_LOG_FILE)):
        with open(COLD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] ===== {role.upper()} =====\n{content}\n")


def save_hot_state(messages: List[BaseMessage]):
    state_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
    dicts = [message_to_dict(m) for m in state_msgs]
    with FILE_LOCK_MGR.get_lock(str(HOT_STATE_FILE)):
        with open(HOT_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(dicts, f, ensure_ascii=False, indent=2)


def load_hot_state() -> List[BaseMessage]:
    if not HOT_STATE_FILE.exists(): return []
    try:
        with open(HOT_STATE_FILE, "r", encoding="utf-8") as f:
            return messages_from_dict(json.load(f))
    except:
        return []


def reset_workspace_for_new_task() -> List[BaseMessage]:
    # 1. 物理删除 PLAN.md
    if PLAN_FILE.exists():
        PLAN_FILE.unlink(missing_ok=True)
        print("\033[31m[清理] 旧任务计划 (PLAN.md) 已被物理删除。\033[0m")

    # 2. 物理删除热状态记忆 (Hot State)
    if HOT_STATE_FILE.exists():
        HOT_STATE_FILE.unlink(missing_ok=True)
        print("\033[31m[清理] 旧对话记忆 (.agent_hot_state.json) 已被物理删除。\033[0m")

    # 3. 彻底清空内存中的历史数组
    return []