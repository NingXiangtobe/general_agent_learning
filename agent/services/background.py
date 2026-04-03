import threading
import uuid
from queue import Queue
from agent.tools.os_cmd import powershell

class BackgroundManager:
    def __init__(self):
        self.tasks = {}
        self.notifications = Queue() # 线程安全队列充当信箱

    def run(self, command: str, timeout: int = 120) -> str:
        tid = str(uuid.uuid4())[:8]
        self.tasks[tid] = {"status": "running", "command": command, "result": None}
        # 启动守护线程，避免主循环卡死
        threading.Thread(target=self._exec, args=(tid, command, timeout), daemon=True).start()
        return f"Background task {tid} started: {command[:80]}"

    def _exec(self, tid: str, command: str, timeout: int):
        try:
            output_str = powershell.invoke({"command": command})

            if output_str.startswith("Error:") or output_str.startswith("Run Error:"):
                self.tasks[tid].update({"status": "error", "result": output_str[:50000]})
            else:
                self.tasks[tid].update({"status": "completed", "result": output_str[:50000]})

        except Exception as e:
            # 兜底捕获：防止 powershell 工具本身发生未捕获的严重崩溃
            self.tasks[tid].update({"status": "error", "result": f"System Crash: {str(e)}"})

        # 将最终结果推入信箱，等待主 Agent 去 drain()
        self.notifications.put({
            "task_id": tid,
            "status": self.tasks[tid]["status"],
            "result": self.tasks[tid]["result"][:500]
        })

    def check(self, tid: str = None) -> str:
        if tid:
            t = self.tasks.get(tid)
            return f"[{t['status']}] {t.get('result', '(running)')}" if t else f"Unknown: {tid}"
        return "\n".join(f"{k}: [{v['status']}] {v['command'][:60]}" for k, v in self.tasks.items()) or "No bg tasks."

    def drain(self) -> list:
        # 供主循环排空信箱
        notifs = []
        while not self.notifications.empty():
            notifs.append(self.notifications.get_nowait())
        return notifs

BG = BackgroundManager()