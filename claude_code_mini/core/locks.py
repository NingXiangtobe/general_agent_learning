import threading
from pathlib import Path

class FileLockManager:
    """物理层安全防线：保证并发写入不冲突"""
    def __init__(self):
        self._locks = {}
        self._dict_lock = threading.Lock()

    def get_lock(self, path: str):
        full_path = str(Path(path).absolute())
        with self._dict_lock:
            if full_path not in self._locks:
                self._locks[full_path] = threading.Lock()
            return self._locks[full_path]

# 单例模式，全局唯一
FILE_LOCK_MGR = FileLockManager()