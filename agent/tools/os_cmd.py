import os
import re
import subprocess
from langchain_core.tools import tool

@tool
def powershell(command: str):
    """
    Run a command in the local Windows PowerShell environment, and wait for the result.
    IMPORTANT: You are on Windows. Use PowerShell commands (e.g., Get-ChildItem, Get-Content, Select-String)
    or standard Windows commands.

    Args:
        command: the powershell command to execute
    """
    # 1. 危险系统命令拦截
    system_dangers = [r"\bformat\s+[a-z]:", r"Stop-Computer", r"Remove-Item\s+-Recurse\s+[C-Z]:\\"]
    for danger_regex in system_dangers:
        if re.search(danger_regex, command, re.IGNORECASE):
            return f"Error: Dangerous system command blocked by regex '{danger_regex}'"

    # 2. 绕过并发锁的文件修改拦截
    file_mutators = [r">>", r"(?<!\w)>(?!\w)", r"Set-Content", r"Add-Content", r"Out-File"]
    for mutator in file_mutators:
        if re.search(mutator, command, re.IGNORECASE):
            return ("Error: File modification via PowerShell is blocked to ensure thread safety. "
                    "You MUST use the Python tools (read_file, write_file) to process and save file contents.")

    try:
        # 强制为所有的 Get-Content 注入 -Encoding UTF8
        patched_command = re.sub(r'(?i)(Get-Content\s+)', r'\1-Encoding UTF8 ', command)

        print(f"\033[33mPS> {patched_command}\033[0m")

        # 强制输出为 UTF-8
        enforcer = "chcp 65001 >$null; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        full_command = enforcer + patched_command

        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", full_command],
            cwd=os.getcwd(),
            capture_output=True,
            text=False,
            timeout=120
        )

        raw_output = r.stdout + r.stderr
        try:
            out = raw_output.decode('utf-8')
        except UnicodeDecodeError:
            out = raw_output.decode('gbk', errors='replace')

        result = out.strip() or "(no output)"
        return result[:50000]

    except Exception as e:
        return f"Run Error: {str(e)}"