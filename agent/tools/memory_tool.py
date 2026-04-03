from langchain_core.tools import tool

@tool
def compact(focus: str = "") -> str:
    """
    Trigger manual conversation compression.
    Use this when you feel the context history is getting too long or cluttered.
    Args:
        focus: What specific details or current state to preserve in the summary.
    """
    return f"Manual compression requested. Focus: {focus}"