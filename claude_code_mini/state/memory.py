import json
from typing import List
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, AIMessage

from claude_code_mini.core.config import base_llm, KEEP_RECENT

def estimate_size(messages: List[BaseMessage]) -> int:
    """快速估算当前上下文长度 (字符级别)"""
    return sum(len(str(m.content)) for m in messages)

def micro_compact(messages: List[BaseMessage]):
    """L1 微压缩：原地截断历史 ToolMessage 的超长返回值，仅保留最近的 KEEP_RECENT 个。"""
    tool_msg_indices = [i for i, msg in enumerate(messages) if isinstance(msg, ToolMessage)]
    if len(tool_msg_indices) <= KEEP_RECENT:
        return

    indices_to_clear = tool_msg_indices[:-KEEP_RECENT]
    for idx in indices_to_clear:
        msg = messages[idx]
        if isinstance(msg.content, str) and len(msg.content) > 100:
            msg.content = f"[Previous: used {msg.name} (Output truncated to save memory)]"

def auto_compact(messages: List[BaseMessage]) -> List[BaseMessage]:
    # 构建供大模型阅读的历史文本
    conversation_text = ""
    for msg in messages:
        msg_type = type(msg).__name__
        conversation_text += f"{msg_type}: {msg.content}\n"
    conversation_text = conversation_text[:100000]

    print("\033[36m[内存管理] 正在呼叫大模型生成上下文浓缩快照...\033[0m")
    summary_prompt = HumanMessage(
        content="Summarize this conversation for continuity. Include: \n"
                "1) What was accomplished\n"
                "2) Current state and pending TODOs\n"
                "3) Key decisions made\n"
                "Be concise but preserve critical details.\n\n" + conversation_text
    )

    # 注意：这里调用的是未绑定 tool 的 base_llm，防止总结时乱用工具
    summary_response = base_llm.invoke([summary_prompt])
    summary = summary_response.content

    # 彻底重置历史
    return [
        HumanMessage(content=f"[Conversation compressed.]\n\n{summary}"),
        AIMessage(content="Understood. I have the context from the summary. Continuing with the tasks.")
    ]