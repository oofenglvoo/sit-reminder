"""久坐计时与时段判定（纯逻辑，不依赖 Qt，便于单元测试）。

调度模型（“锚点对齐”）：
- 时段内提醒时间严格对齐时段起点：起点 + N × 间隔（如 09:00、间隔 45 分 → 09:45、10:30…）。
- 每次提醒后进入“休息”状态，默认 3 分钟；休息期间不计久坐，倒计时显示休息剩余。
- 程序在时段中途启动时，锚点对齐到最近一个已过的整点，不补发错过的提醒。
- 「我起来了」：先休息，再从零计满一个间隔。
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from enum import Enum, auto

from .config import Period


class Event(Enum):
    NONE = auto()
    REMIND = auto()


class Status(Enum):
    RUNNING = auto()        # 久坐计时中
    PAUSED = auto()         # 已暂停
    OUT_OF_PERIOD = auto()  # 不在时段内
    SNOOZING = auto()       # 稍后提醒中
    RESTING = auto()        # 休息中


class SitTracker:
    def __init__(
        self,
        interval_seconds: int,
        periods: list[Period],
        enabled: bool = True,
        rest_seconds: int = 0,
    ) -> None:
        self.interval_seconds = max(1, int(interval_seconds))
        self.rest_seconds = max(0, int(rest_seconds))
        self.periods = list(periods)
        self.enabled = enabled

        self._paused = False
        self._anchor: datetime | None = None
        self._period_key: tuple[str, str] | None = None
        self._rest_until: datetime | None = None
        self._snooze_until: datetime | None = None
        self._last_tick: datetime | None = None

    # ---------- 设置 ----------
    def set_periods(self, periods: list[Period]) -> None:
        self.periods = list(periods)
        self._period_key = None  # 强制重新对齐时段

    def set_interval(self, interval_seconds: int) -> None:
        self.interval_seconds = max(1, int(interval_seconds))

    def set_rest(self, rest_seconds: int) -> None:
        self.rest_seconds = max(0, int(rest_seconds))

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    @property
    def _rest_span(self) -> int:
        """有效休息时长，始终小于一个间隔。"""
        return min(self.rest_seconds, max(0, self.interval_seconds - 1))

    # ---------- 控制 ----------
    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def reset(self) -> None:
        """用户“我起来了”：先休息，再从零计满一个间隔。"""
        now = self._last_tick or datetime.now()
        span = self._rest_span
        self._snooze_until = None
        self._rest_until = now + timedelta(seconds=span) if span > 0 else None
        self._anchor = now + timedelta(seconds=span)

    def snooze(self, seconds: int) -> None:
        """稍后提醒：到点立即提醒，之后恢复正常节奏。"""
        now = self._last_tick or datetime.now()
        self._snooze_until = now + timedelta(seconds=max(1, int(seconds)))
        self._rest_until = None

    # ---------- 状态查询 ----------
    def is_active(self, t: time) -> bool:
        return any(p.contains(t) for p in self.periods)

    def _current_period(self, t: time) -> Period | None:
        for period in self.periods:
            if period.contains(t):
                return period
        return None

    def status(self, now: datetime) -> Status:
        if self._snooze_until is not None and now < self._snooze_until:
            return Status.SNOOZING
        if not self.enabled or self._paused:
            return Status.PAUSED
        if self._current_period(now.time()) is None:
            return Status.OUT_OF_PERIOD
        if self._rest_until is not None and now < self._rest_until:
            return Status.RESTING
        return Status.RUNNING

    def remaining_seconds(self, now: datetime) -> float:
        if self._snooze_until is not None and now < self._snooze_until:
            return max(0.0, (self._snooze_until - now).total_seconds())
        current = self.status(now)
        if current is Status.RESTING and self._rest_until is not None:
            return max(0.0, (self._rest_until - now).total_seconds())
        if current is Status.RUNNING and self._anchor is not None:
            next_remind = self._anchor + timedelta(seconds=self.interval_seconds)
            return max(0.0, (next_remind - now).total_seconds())
        return float(self.interval_seconds)

    # ---------- 主循环 ----------
    def _enter_period(self, now: datetime, period: Period) -> None:
        """进入时段时把锚点对齐到最近一个已过的整点。"""
        period_start_dt = datetime.combine(now.date(), period.start_time())
        interval = self.interval_seconds
        elapsed = (now - period_start_dt).total_seconds()
        if elapsed < 0:
            self._anchor = period_start_dt
            self._rest_until = None
        else:
            n = int(elapsed // interval)
            self._anchor = period_start_dt + timedelta(seconds=n * interval)
            self._rest_until = None
            if n >= 1:
                rest_end = self._anchor + timedelta(seconds=self._rest_span)
                if now < rest_end:
                    self._rest_until = rest_end
        self._period_key = (period.start, period.end)

    def tick(self, now: datetime) -> Event:
        self._last_tick = now

        if not self.enabled or self._paused:
            return Event.NONE

        # 稍后提醒期：到点立即提醒
        if self._snooze_until is not None:
            if now >= self._snooze_until:
                self._snooze_until = None
                span = self._rest_span
                self._anchor = now
                self._rest_until = (
                    now + timedelta(seconds=span) if span > 0 else None
                )
                return Event.REMIND
            return Event.NONE

        period = self._current_period(now.time())
        if period is None:
            self._anchor = None
            self._rest_until = None
            self._period_key = None
            return Event.NONE

        key = (period.start, period.end)
        if self._anchor is None or self._period_key != key:
            self._enter_period(now, period)
            return Event.NONE

        # 到达（或越过）提醒整点：对齐推进锚点并触发一次提醒
        if now >= self._anchor + timedelta(seconds=self.interval_seconds):
            steps = int(
                (now - self._anchor).total_seconds() // self.interval_seconds
            )
            self._anchor = self._anchor + timedelta(seconds=steps * self.interval_seconds)
            span = self._rest_span
            self._rest_until = (
                self._anchor + timedelta(seconds=span) if span > 0 else None
            )
            return Event.REMIND

        return Event.NONE
