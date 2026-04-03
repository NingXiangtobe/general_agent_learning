from langchain_core.tools import tool
from agent.services.skill_loader import skill_loader_instance

@tool
def load_skill(name: str) -> str:
    """Load specialized knowledge or standard operating procedures (SOP) by skill name."""
    print(f"\033[35m[翻阅手册]\033[0m 正在加载技能: {name}...")
    return skill_loader_instance.get_content(name)