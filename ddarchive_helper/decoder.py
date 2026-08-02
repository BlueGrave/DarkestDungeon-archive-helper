from __future__ import annotations

import json
import subprocess
import sys               # <-- 新增：引入 sys 模块
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import DDHelperError
from .logger import ActionLogger


class SaveDecoder:
    def __init__(self, jar_path: Path, logger: ActionLogger) -> None:
        self.jar_path = jar_path
        self.logger = logger

        # ====== 核心修改：动态获取 Java 路径 ======
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            # 保持向上两级定位到根目录
            base_dir = Path(__file__).resolve().parent.parent
            
        # 定义便携版 Java 的路径
        bundled_java = base_dir / "jre" / "bin" / "java.exe"
        
        # 如果检测到自带了 jre 文件夹，就使用自带的；否则使用系统的
        if bundled_java.exists():
            self.java_cmd = str(bundled_java)
        else:
            self.java_cmd = "java"

        # ====== 核心新增：配置 Windows 下隐藏子进程黑窗口 ======
        self._startupinfo = None
        if sys.platform == "win32":
            self._startupinfo = subprocess.STARTUPINFO()
            self._startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._startupinfo.wShowWindow = subprocess.SW_HIDE
        # ==========================================

    def ensure_ready(self) -> None:
        if not self.jar_path.exists():
            raise DDHelperError(f"DDSaveEditor.jar not found: {self.jar_path}")
        try:
            # subprocess.run(["java", "-version"], capture_output=True, text=True, check=False)
            # 将硬编码的 "java" 替换为 self.java_cmd，加上 startupinfo=self._startupinfo
            subprocess.run([self.java_cmd, "-version"], capture_output=True, text=True, check=False, startupinfo=self._startupinfo)
        except FileNotFoundError as exc:
            raise DDHelperError("Java runtime not found in PATH") from exc

    def decode_file(self, src_file: Path) -> Dict[str, Any]:
        if not src_file.exists():
            raise DDHelperError(f"Missing file: {src_file}")
        with tempfile.TemporaryDirectory(prefix="dd_decode_") as tmp_dir:
            out_file = Path(tmp_dir) / "decoded.json"
            cmd = [
                # "java",
                self.java_cmd,  # <-- 将这里的 "java" 替换为 self.java_cmd
                "-jar",
                str(self.jar_path),
                "decode",
                "-o",
                str(out_file),
                str(src_file),
            ]
            # 加上 startupinfo=self._startupinfo，彻底静默后台运行
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, startupinfo=self._startupinfo)
            if result.returncode != 0:
                raise DDHelperError(
                    f"Decode failed for {src_file.name}: {result.stderr.strip() or result.stdout.strip()}"
                )
            return json.loads(out_file.read_text(encoding="utf-8"))

    def read_inraid(self, profile_dir: Path) -> Optional[bool]:
        decoded = self.decode_file(profile_dir / "persist.game.json")
        base_root = decoded.get("base_root", {})
        inraid = base_root.get("inraid")
        if isinstance(inraid, bool):
            return inraid
        return None

    def read_steam_cloud_enabled(self, remote_root: Path) -> Optional[bool]:
        init_file = remote_root / "steam_init.json"
        if not init_file.exists():
            return None
        decoded = self.decode_file(init_file)
        base_root = decoded.get("base_root", {})
        value = base_root.get("steam_cloud_enabled")
        if isinstance(value, bool):
            return value
        return None
