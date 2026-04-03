from pathlib import Path
from typing import Optional, Union
from langchain_core.tools import tool

from claude_code_mini.core.locks import FILE_LOCK_MGR

def safe_path(p: str) -> Path:
    path = Path(p).absolute()
    return path

def smart_read_text(file_path: Union[str, Path]) -> str:
    """严谨的、带回退机制的文件读取。支持类型自适应、I/O 异常捕获与降级告警。"""
    path_obj = Path(file_path)

    if not path_obj.exists():
        return ""

    if not path_obj.is_file():
        print(f"\033[31m[I/O 拦截] {path_obj} 是一个目录或无效文件。\033[0m")
        return f"[Error: {path_obj.name} is not a valid file]"

    for enc in ['utf-8', 'gbk']:
        try:
            content = path_obj.read_text(encoding=enc)
            if enc != 'utf-8':
                print(f"\033[33m[编码告警] 文件 {path_obj.name} 使用 {enc} 读取，请注意可能的编码污染。\033[0m")
            return content
        except UnicodeDecodeError:
            continue
        except PermissionError:
            print(f"\033[31m[I/O 拦截] 权限拒绝，文件被占用: {path_obj.name}\033[0m")
            return f"[Error: Permission denied reading {path_obj.name}]"
        except Exception as e:
            return f"[Error: Unexpected I/O exception {str(e)}]"

    print(f"\033[31m[严重告警] 文件 {path_obj.name} 包含不可恢复的乱码，已强制使用 replace 模式兜底。\033[0m")
    try:
        with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[Critical Error: {str(e)}]"

@tool
def read_file(path: str, limit: Optional[int] = None) -> str:
    """
    Read contents from file in the Sandbox.

    Args:
        path: 要读取的目标沙箱文件的绝对或相对路径。
        limit: 限制读取的最大行数。如果为 None，则读取全量文件。
    """
    try:
        text = safe_path(path).read_text(encoding="utf-8")
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """
    Write exact content to a file in the Sandbox, creating directories if necessary.

    Args:
        path: 要写入的目标沙箱文件的绝对或相对路径。
        content: 要写入的内容
    """
    try:
        fp = safe_path(path)
        with FILE_LOCK_MGR.get_lock(path):
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"

@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """
    Replace exact text in a file in the Sandbox. The old_text must match exactly.

    Args:
        path: 要编辑的目标沙箱文件的绝对或相对路径。
        old_text: 被覆盖的旧内容
        new_text: 新内容，去覆盖旧内容
    """
    try:
        p = safe_path(path)
        with FILE_LOCK_MGR.get_lock(path):
            if not p.exists(): return f"Error: {path} not found."
            current_content = p.read_text(encoding="utf-8")
            if old_text not in current_content:
                return f"Error: CONTENT_DRIFT_DETECTED. File {path} has changed. Re-read it."

            updated_content = current_content.replace(old_text, new_text, 1)
            p.write_text(updated_content, encoding="utf-8")
        return f"Successfully edited {path}."
    except Exception as e:
        return f"Error: {e}"