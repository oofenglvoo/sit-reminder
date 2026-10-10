"""资源与路径解析（兼容开发运行与 PyInstaller 打包）。"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """返回打包后或开发时的资源绝对路径。

    打包后资源位于 sys._MEIPASS；开发时位于项目根目录。
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    return Path(__file__).resolve().parent.parent / relative


def icon_path() -> Path:
    return resource_path("assets/icon.ico")


def sound_path() -> Path:
    return resource_path("assets/remind.wav")
