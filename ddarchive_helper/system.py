from __future__ import annotations

import subprocess
import sys  # <--- 确保加上这一行！

def is_darkest_running() -> bool:
    try:
        # 配置 Windows 下隐藏子进程黑窗口
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Darkest.exe"],
            capture_output=True,
            text=True,
            check=False,
            startupinfo=startupinfo, # <-- 传入隐藏参数
        )
        output = result.stdout.lower()
        
        return "darkest.exe" in output
    except Exception as exc:
        print(f"[Debug Tasklist] 发生致命异常: {exc}")  # <-- 如果报错能在这里看到
        return False
