"""系统托盘图标与右键菜单。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import __app_name__
from .resources import icon_path
from .scheduler import Status

STATUS_TEXT = {
    Status.RUNNING: "计时中",
    Status.PAUSED: "已暂停",
    Status.OUT_OF_PERIOD: "不在时段内",
    Status.SNOOZING: "稍后提醒中",
    Status.RESTING: "休息中",
}


class Tray(QSystemTrayIcon):
    showWindowRequested = Signal()
    pauseToggled = Signal()
    testRequested = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None) -> None:
        try:
            icon = QIcon(str(icon_path()))
        except Exception:
            icon = QIcon()
        super().__init__(icon, parent)
        self.setToolTip(__app_name__)

        menu = QMenu()
        title_action = QAction(__app_name__, menu)
        title_action.setEnabled(False)
        title_action.setObjectName("MenuTitle")
        menu.addAction(title_action)

        self.status_action = QAction("状态：正在启动", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        menu.addSeparator()

        show_action = QAction("打开设置", menu)
        show_action.triggered.connect(self.showWindowRequested)
        menu.addAction(show_action)

        self.pause_action = QAction("暂停", menu)
        self.pause_action.triggered.connect(self.pauseToggled)
        menu.addAction(self.pause_action)

        menu.addSeparator()
        test_action = QAction("测试提醒", menu)
        test_action.triggered.connect(self.testRequested)
        menu.addAction(test_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quitRequested)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showWindowRequested.emit()

    def set_paused(self, paused: bool) -> None:
        self.pause_action.setText("恢复" if paused else "暂停")

    def update_tooltip(self, status: Status, remaining_seconds: float) -> None:
        text = STATUS_TEXT.get(status, "")
        if status in (Status.RUNNING, Status.SNOOZING, Status.RESTING):
            minutes = int(remaining_seconds) // 60
            seconds = int(remaining_seconds) % 60
            countdown = f"{minutes:02d}:{seconds:02d}"
            self.setToolTip(f"{__app_name__} · {text} {countdown}")
            self.status_action.setText(f"状态：{text} · {countdown}")
        else:
            self.setToolTip(f"{__app_name__} · {text}")
            self.status_action.setText(f"状态：{text}")
