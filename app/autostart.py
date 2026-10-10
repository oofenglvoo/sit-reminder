"""开机自启动管理（Windows 注册表 Run 键）。

通过 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run 写入启动项，
无需管理员权限。非 Windows 平台或注册表不可用时安全降级。
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # 非 Windows
    winreg = None  # type: ignore[assignment]

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "SitReminder"
LEGACY_VALUE_NAME = "SedentaryReminder"


def is_supported() -> bool:
    return winreg is not None and sys.platform == "win32"


def launch_command() -> str:
    """返回用于自启动的命令行字符串。

    - 打包运行：直接指向 exe，并以最小化到托盘模式启动。
    - 源码运行：优先使用 pythonw.exe，避免弹出控制台窗口。
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'

    python = Path(sys.executable)
    pythonw = python.with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else python
    script = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{exe}" "{script}" --minimized'


def is_enabled() -> bool:
    """当前是否已注册开机自启动。"""
    if not is_supported():
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(value)
    except OSError:
        return False


def enable() -> bool:
    """写入开机自启动项，成功返回 True。"""
    if not is_supported():
        return False
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command())
        return True
    except OSError:
        return False


def disable() -> bool:
    """删除开机自启动项，成功或本就不存在返回 True。"""
    if not is_supported():
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, VALUE_NAME)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def _delete_value(name: str) -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def remove_legacy() -> None:
    """清理旧版本名（SedentaryReminder）残留的自启动项。"""
    if not is_supported():
        return
    _delete_value(LEGACY_VALUE_NAME)


def set_enabled(enabled: bool) -> bool:
    """按需开启或关闭开机自启动。"""
    return enable() if enabled else disable()
