from langchain_core.tools import tool
from agent.services.background import BG

@tool
def background_run(command: str, timeout: int = 120) -> str:
    """
    Run a command in the background. IMMEDIATELY returns a task_id.
    YOU MUST use this for long-running tasks like 'npm install', 'pip install',
    downloading large files, compiling, or starting servers (e.g., 'python -m http.server').

    Args:
        command: the powershell command to execute
    Return:
        the response,like: Background task {task_id} started: {command}"
    """
    return BG.run(command, timeout)

@tool
def check_background(task_id: str = None) -> str:
    """
    Check background task status.
    Args:
        task_id: task_id
    """
    return BG.check(task_id)