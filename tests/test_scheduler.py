"""scheduler 与 config 的单元测试（不依赖 Qt）。"""

from __future__ import annotations

from datetime import datetime, timedelta, time

import pytest

from app.config import AppConfig, NotifySettings, Period
from app.autostart import launch_command
from app.scheduler import Event, SitTracker, Status

DAY = datetime(2026, 1, 1)


def dt(hour: int, minute: int, second: int = 0) -> datetime:
    return DAY.replace(hour=hour, minute=minute, second=second)


# ---------------- Period ----------------
def test_period_contains_boundaries():
    p = Period("09:00", "12:00")
    assert p.contains(time(9, 0)) is True
    assert p.contains(time(10, 30)) is True
    assert p.contains(time(12, 0)) is False  # 结束时刻不含
    assert p.contains(time(8, 59)) is False


def test_period_validity():
    assert Period("09:00", "12:00").is_valid() is True
    assert Period("12:00", "09:00").is_valid() is False
    assert Period("bad", "12:00").is_valid() is False


def test_period_from_dict_rejects_invalid():
    assert Period.from_dict({"start": "09:00", "end": "10:00"}) is not None
    assert Period.from_dict({"start": "10:00", "end": "09:00"}) is None
    assert Period.from_dict("nope") is None


def test_is_active_multiple_periods():
    tracker = SitTracker(60, [Period("09:00", "12:00"), Period("14:00", "18:00")])
    assert tracker.is_active(time(10, 0)) is True
    assert tracker.is_active(time(13, 0)) is False
    assert tracker.is_active(time(15, 0)) is True


# ---------------- 对齐时段起点 ----------------
def test_aligns_to_period_start():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")])
    assert tracker.tick(dt(9, 0)) is Event.NONE  # 进入时段，锚点=09:00
    assert tracker.remaining_seconds(dt(9, 0)) == pytest.approx(45 * 60)
    assert tracker.tick(dt(9, 44)) is Event.NONE
    assert tracker.tick(dt(9, 45)) is Event.REMIND  # 09:00 + 45 分
    # 下一次仍对齐：10:30
    assert tracker.remaining_seconds(dt(9, 45)) == pytest.approx(45 * 60)
    assert tracker.tick(dt(10, 30)) is Event.REMIND


def test_mid_period_start_aligns_to_previous_grid():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")])
    assert tracker.tick(dt(9, 30)) is Event.NONE  # 中途启动
    # 下一次对齐点是 09:45，只剩 15 分钟
    assert tracker.remaining_seconds(dt(9, 30)) == pytest.approx(15 * 60)
    assert tracker.tick(dt(9, 45)) is Event.REMIND


def test_mid_period_start_late():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")])
    tracker.tick(dt(11, 0))  # 09:00 后已过 2 个整点(09:45,10:30)
    assert tracker.remaining_seconds(dt(11, 0)) == pytest.approx(15 * 60)  # → 11:15
    assert tracker.status(dt(11, 0)) is Status.RUNNING


# ---------------- 休息 ----------------
def test_rest_after_reminder():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")], rest_seconds=180)
    tracker.tick(dt(9, 0))
    assert tracker.tick(dt(9, 45)) is Event.REMIND
    assert tracker.status(dt(9, 46)) is Status.RESTING
    assert tracker.remaining_seconds(dt(9, 46)) == pytest.approx(120)
    assert tracker.tick(dt(9, 46)) is Event.NONE
    # 休息结束后继续久坐计时
    assert tracker.status(dt(9, 48)) is Status.RUNNING
    assert tracker.remaining_seconds(dt(9, 48)) == pytest.approx(42 * 60)


def test_mid_period_start_inside_rest_window():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")], rest_seconds=180)
    tracker.tick(dt(10, 31))  # 刚过 10:30 整点，处于休息窗口
    assert tracker.status(dt(10, 31)) is Status.RESTING
    assert tracker.remaining_seconds(dt(10, 31)) == pytest.approx(120)
    assert tracker.status(dt(10, 34)) is Status.RUNNING
    assert tracker.remaining_seconds(dt(10, 34)) == pytest.approx(41 * 60)


# ---------------- 我起来了 ----------------
def test_reset_rests_then_full_interval():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")], rest_seconds=180)
    tracker.tick(dt(9, 0))
    tracker.reset()  # 基于 _last_tick=09:00
    assert tracker.status(dt(9, 1)) is Status.RESTING
    assert tracker.remaining_seconds(dt(9, 1)) == pytest.approx(120)
    assert tracker.status(dt(9, 3)) is Status.RUNNING
    # 从休息结束(09:03)起计满 45 分钟 → 09:48
    assert tracker.remaining_seconds(dt(9, 3)) == pytest.approx(45 * 60)
    assert tracker.tick(dt(9, 47)) is Event.NONE
    assert tracker.tick(dt(9, 48)) is Event.REMIND


# ---------------- 稍后提醒 ----------------
def test_snooze_then_remind():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")], rest_seconds=180)
    tracker.tick(dt(9, 0))
    tracker.tick(dt(9, 1))
    tracker.snooze(300)  # 基于 _last_tick=09:01 → 09:06
    assert tracker.status(dt(9, 2)) is Status.SNOOZING
    assert tracker.remaining_seconds(dt(9, 2)) == pytest.approx(240)
    assert tracker.tick(dt(9, 5)) is Event.NONE
    assert tracker.tick(dt(9, 6)) is Event.REMIND
    assert tracker.status(dt(9, 7)) is Status.RESTING  # 提醒后休息


# ---------------- 时段边界 ----------------
def test_leave_period_resets_anchor():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")])
    tracker.tick(dt(11, 0))
    assert tracker.status(dt(12, 0)) is Status.OUT_OF_PERIOD
    assert tracker.tick(dt(12, 0)) is Event.NONE
    # 重新进入时段应对齐新起点
    tracker.tick(dt(12, 1))  # 仍在时段外
    assert tracker.remaining_seconds(dt(12, 30)) == pytest.approx(45 * 60)


def test_paused_does_not_fire():
    tracker = SitTracker(45 * 60, [Period("09:00", "12:00")])
    tracker.tick(dt(9, 0))
    tracker.pause()
    assert tracker.status(dt(9, 46)) is Status.PAUSED
    assert tracker.tick(dt(9, 46)) is Event.NONE
    tracker.resume()


def test_sleep_skips_without_spam():
    tracker = SitTracker(45 * 60, [Period("09:00", "18:00")])
    tracker.tick(dt(9, 0))
    # 休眠后一次性跳到 14:00，只触发一次，锚点对齐到 13:30
    assert tracker.tick(dt(14, 0)) is Event.REMIND
    assert tracker.remaining_seconds(dt(14, 0)) == pytest.approx(15 * 60)


# ---------------- config ----------------
def test_config_roundtrip():
    cfg = AppConfig(
        interval_minutes=30,
        periods=[Period("08:00", "12:00"), Period("13:00", "17:00")],
        notify=NotifySettings(toast=False, popup=True, sound=False),
        snooze_minutes=10,
        rest_minutes=4,
        autostart=True,
    )
    restored = AppConfig.from_dict(cfg.to_dict())
    assert restored.interval_minutes == 30
    assert len(restored.periods) == 2
    assert restored.notify.toast is False
    assert restored.snooze_minutes == 10
    assert restored.rest_minutes == 4
    assert restored.autostart is True


def test_config_defaults_rest():
    assert AppConfig().rest_minutes == 3


def test_legacy_start_minimized_config_is_ignored():
    config = AppConfig.from_dict({"start_minimized": True})
    assert "start_minimized" not in config.to_dict()


def test_autostart_launch_command_starts_minimized():
    assert "--minimized" in launch_command()


def test_config_clamps_and_fixes_invalid():
    data = {
        "interval_minutes": 99999,
        "periods": [{"start": "10:00", "end": "09:00"}],  # 非法
        "snooze_minutes": -5,
        "rest_minutes": -1,
    }
    cfg = AppConfig.from_dict(data)
    assert cfg.interval_minutes <= 600
    assert len(cfg.periods) >= 1
    assert cfg.snooze_minutes >= 1
    assert cfg.rest_minutes >= 0


def test_config_from_garbage():
    assert AppConfig.from_dict(None).interval_minutes == 45
    assert AppConfig.from_dict([]).interval_minutes == 45
