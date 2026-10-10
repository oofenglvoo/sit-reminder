"""配置数据模型与 JSON 读写。

配置存放于 %APPDATA%\\SitReminder\\config.json。
所有读取都带校验与容错，坏配置不会导致程序崩溃。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

APP_DIR_NAME = "SitReminder"
LEGACY_APP_DIR_NAME = "SedentaryReminder"
CONFIG_FILE_NAME = "config.json"

DEFAULT_INTERVAL_MINUTES = 45
DEFAULT_SNOOZE_MINUTES = 5
DEFAULT_REST_MINUTES = 3
MIN_INTERVAL_MINUTES = 1
MAX_INTERVAL_MINUTES = 600
MAX_REST_MINUTES = 120


def config_dir() -> Path:
    """返回配置目录（%APPDATA%\\SitReminder）。"""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / APP_DIR_NAME


def legacy_config_path() -> Path:
    """旧版本配置路径（%APPDATA%\\SedentaryReminder\\config.json）。"""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / LEGACY_APP_DIR_NAME / CONFIG_FILE_NAME


def config_path() -> Path:
    return config_dir() / CONFIG_FILE_NAME


def _parse_time(value: str) -> time | None:
    """把 "HH:MM" 解析为 datetime.time，失败返回 None。"""
    if not isinstance(value, str):
        return None
    parts = value.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def _format_time(value: time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


@dataclass
class Period:
    """一个提醒生效时段。start 必须早于 end，不支持跨零点。"""

    start: str = "09:00"
    end: str = "18:00"

    def start_time(self) -> time | None:
        return _parse_time(self.start)

    def end_time(self) -> time | None:
        return _parse_time(self.end)

    def is_valid(self) -> bool:
        s, e = self.start_time(), self.end_time()
        return s is not None and e is not None and s < e

    def contains(self, t: time) -> bool:
        """判断时刻 t 是否落在 [start, end) 内。"""
        s, e = self.start_time(), self.end_time()
        if s is None or e is None:
            return False
        return s <= t < e

    @classmethod
    def from_dict(cls, data: Any) -> "Period | None":
        if not isinstance(data, dict):
            return None
        start = data.get("start")
        end = data.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            return None
        period = cls(start=start.strip(), end=end.strip())
        if not period.is_valid():
            return None
        return period


@dataclass
class NotifySettings:
    toast: bool = True
    popup: bool = True
    sound: bool = True

    @classmethod
    def from_dict(cls, data: Any) -> "NotifySettings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            toast=bool(data.get("toast", True)),
            popup=bool(data.get("popup", True)),
            sound=bool(data.get("sound", True)),
        )


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


@dataclass
class AppConfig:
    enabled: bool = True
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES
    periods: list[Period] = field(
        default_factory=lambda: [Period("09:00", "12:00"), Period("14:00", "18:00")]
    )
    notify: NotifySettings = field(default_factory=NotifySettings)
    snooze_minutes: int = DEFAULT_SNOOZE_MINUTES
    rest_minutes: int = DEFAULT_REST_MINUTES
    popup_auto_close_seconds: int = 0
    start_minimized: bool = True
    autostart: bool = False

    # ---- 序列化 ----
    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "periods": [asdict(p) for p in self.periods],
            "notify": asdict(self.notify),
            "snooze_minutes": self.snooze_minutes,
            "rest_minutes": self.rest_minutes,
            "popup_auto_close_seconds": self.popup_auto_close_seconds,
            "start_minimized": self.start_minimized,
            "autostart": self.autostart,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "AppConfig":
        if not isinstance(data, dict):
            return cls()

        raw_periods = data.get("periods")
        periods: list[Period] = []
        if isinstance(raw_periods, list):
            for item in raw_periods:
                period = Period.from_dict(item)
                if period is not None:
                    periods.append(period)
        if not periods:
            periods = cls().periods

        return cls(
            enabled=bool(data.get("enabled", True)),
            interval_minutes=_clamp_int(
                data.get("interval_minutes"),
                MIN_INTERVAL_MINUTES,
                MAX_INTERVAL_MINUTES,
                DEFAULT_INTERVAL_MINUTES,
            ),
            periods=periods,
            notify=NotifySettings.from_dict(data.get("notify")),
            snooze_minutes=_clamp_int(
                data.get("snooze_minutes"), 1, 120, DEFAULT_SNOOZE_MINUTES
            ),
            rest_minutes=_clamp_int(
                data.get("rest_minutes"), 0, MAX_REST_MINUTES, DEFAULT_REST_MINUTES
            ),
            popup_auto_close_seconds=_clamp_int(
                data.get("popup_auto_close_seconds"), 0, 3600, 0
            ),
            start_minimized=bool(data.get("start_minimized", True)),
            autostart=bool(data.get("autostart", False)),
        )

    # ---- 便捷属性 ----
    @property
    def interval_seconds(self) -> int:
        return self.interval_minutes * 60

    @property
    def rest_seconds(self) -> int:
        return self.rest_minutes * 60

    def validate(self) -> "AppConfig":
        """返回一份经过合法性修正的配置副本。"""
        return AppConfig.from_dict(self.to_dict())


def load(path: Path | None = None) -> AppConfig:
    """读取配置；文件不存在或损坏时返回默认配置。

    若新路径不存在但存在旧版本配置，则迁移旧配置并写入新路径。
    """
    if path is None:
        target = config_path()
        if not target.exists():
            legacy = legacy_config_path()
            if legacy.exists():
                config = _read(legacy)
                if config is not None:
                    save(config, target)
                    return config
        return _read(target) or AppConfig()
    return _read(path) or AppConfig()


def _read(target: Path) -> AppConfig | None:
    """读取并解析单个配置文件，失败返回 None。"""
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return AppConfig.from_dict(data)


def save(config: AppConfig, path: Path | None = None) -> Path:
    """保存配置，自动创建目录。"""
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def period_label(period: Period) -> str:
    return f"{period.start}-{period.end}"


def format_periods(periods: list[Period]) -> str:
    if not periods:
        return "未设置时段"
    return "、".join(period_label(p) for p in periods)
