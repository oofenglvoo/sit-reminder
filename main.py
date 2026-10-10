"""久坐提醒 - 程序入口。

在指定时段内按可自定义间隔提醒用户起身活动：
Windows 系统通知 + 置顶弹窗 + 提示音，常驻系统托盘。
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from app import __app_name__
from app import autostart
from app.config import AppConfig, load as load_config, save as save_config
from app.main_window import MainWindow
from app.notifier import Notifier
from app.scheduler import Event, SitTracker
from app.style import APP_STYLE
from app.tray import Tray

TICK_INTERVAL_MS = 1000


class AppController(QObject):
    """把配置、计时、提醒、托盘与界面连接起来。"""

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self.config: AppConfig = load_config()

        self.tracker = SitTracker(
            interval_seconds=self.config.interval_seconds,
            periods=self.config.periods,
            enabled=self.config.enabled,
            rest_seconds=self.config.rest_seconds,
        )

        self.window = MainWindow(self.config)
        self.tray = Tray(self)
        self.notifier = Notifier(self.tray, self)

        self._wire_signals()

        self.timer = QTimer(self)
        self.timer.setInterval(TICK_INTERVAL_MS)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

    # ---------- 连线 ----------
    def _wire_signals(self) -> None:
        self.window.configApplied.connect(self._apply_config)
        self.window.testRequested.connect(self._test_notify)
        self.window.pauseToggled.connect(self._toggle_pause)

        self.tray.showWindowRequested.connect(self._show_window)
        self.tray.testRequested.connect(self._test_notify)
        self.tray.pauseToggled.connect(self._toggle_pause)
        self.tray.quitRequested.connect(self._quit)

        self.notifier.acknowledged.connect(self._on_acknowledged)
        self.notifier.snoozed.connect(self._on_snoozed)

    # ---------- 定时逻辑 ----------
    def _on_tick(self) -> None:
        now = datetime.now()
        if self.tracker.tick(now) is Event.REMIND:
            self.notifier.notify(self.config)

        status = self.tracker.status(now)
        remaining = self.tracker.remaining_seconds(now)
        self.window.update_status(status, remaining)
        self.tray.update_tooltip(status, remaining)

    # ---------- 提醒回调 ----------
    def _on_acknowledged(self) -> None:
        self.tracker.reset()

    def _on_snoozed(self) -> None:
        self.tracker.snooze(self.config.snooze_minutes * 60)

    def _test_notify(self) -> None:
        self.notifier.test(self.config)

    # ---------- 配置 ----------
    def _apply_config(self, config: AppConfig) -> None:
        self.config = config
        self.tracker.set_interval(config.interval_seconds)
        self.tracker.set_rest(config.rest_seconds)
        self.tracker.set_periods(config.periods)
        self.tracker.set_enabled(config.enabled)
        save_config(config)
        self._apply_autostart(config.autostart)
        self._show_window()

    def _apply_autostart(self, enabled: bool) -> None:
        try:
            autostart.set_enabled(enabled)
        except Exception:
            pass

    # ---------- 暂停 ----------
    def _toggle_pause(self) -> None:
        if self.tracker.is_paused:
            self.tracker.resume()
        else:
            self.tracker.pause()
        paused = self.tracker.is_paused
        self.window.set_paused(paused)
        self.tray.set_paused(paused)

    # ---------- 窗口 ----------
    def _show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def start(self) -> None:
        self._apply_autostart(self.config.autostart)
        try:
            autostart.remove_legacy()
        except Exception:
            pass
        self.tray.show()
        if not self.config.start_minimized:
            self._show_window()

    # ---------- 退出 ----------
    def _quit(self) -> None:
        save_config(self.config)
        self.timer.stop()
        self.tray.hide()
        self._app.quit()


def _acquire_single_instance() -> QLockFile | None:
    """获取单实例锁，已被占用时返回 None。"""
    lock_path = Path(tempfile.gettempdir()) / "sit-reminder.lock"
    lock = QLockFile(str(lock_path))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        return None
    return lock


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(APP_STYLE)

    lock = _acquire_single_instance()
    if lock is None:
        QMessageBox.information(None, __app_name__, "程序已经在运行了。")
        return 0

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.warning(None, __app_name__, "当前系统不支持系统托盘。")

    controller = AppController(app)
    controller.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
