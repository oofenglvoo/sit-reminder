"""置顶提醒弹窗窗口。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import __app_name__
from .resources import icon_path


class ReminderPopup(QWidget):
    """无边框置顶弹窗，提供“我起来了 / 稍后提醒”两个操作。"""

    acknowledged = Signal()
    snoozed = Signal()

    def __init__(
        self,
        snooze_minutes: int,
        auto_close_seconds: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._auto_close_seconds = auto_close_seconds
        self._auto_timer: QTimer | None = None

        self.setWindowTitle(__app_name__)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFixedWidth(360)
        try:
            self.setWindowIcon(QIcon(str(icon_path())))
        except Exception:
            pass

        self._build_ui(snooze_minutes)
        self._apply_style()
        self._center_on_screen()

    def _build_ui(self, snooze_minutes: int) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        title = QLabel("该起来活动一下了")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        message = QLabel(
            "你已经久坐一段时间，站起来伸展一下、走动几步、看看远处吧。"
        )
        message.setObjectName("message")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.snooze_button = QPushButton(f"稍后提醒（{snooze_minutes} 分钟）")
        self.snooze_button.setObjectName("snooze")
        self.snooze_button.clicked.connect(self._on_snooze)

        self.ack_button = QPushButton("我起来了")
        self.ack_button.setObjectName("ack")
        self.ack_button.setDefault(True)
        self.ack_button.clicked.connect(self._on_ack)

        buttons.addWidget(self.snooze_button)
        buttons.addWidget(self.ack_button)

        root.addWidget(title)
        root.addWidget(message)
        root.addLayout(buttons)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background: #ffffff; }
            QLabel#title { font-size: 18px; font-weight: 600; color: #1f2937; }
            QLabel#message { font-size: 13px; color: #4b5563; }
            QPushButton {
                padding: 9px 14px; border-radius: 8px; font-size: 13px;
                border: 1px solid #d1d5db; background: #f9fafb; color: #374151;
            }
            QPushButton:hover { background: #f3f4f6; }
            QPushButton#ack {
                background: #2563eb; color: #ffffff; border: none; font-weight: 600;
            }
            QPushButton#ack:hover { background: #1d4ed8; }
            """
        )

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 3
        self.move(x, y)

    def _on_ack(self) -> None:
        self.acknowledged.emit()
        self.close()

    def _on_snooze(self) -> None:
        self.snoozed.emit()
        self.close()

    def showEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        if self._auto_close_seconds > 0:
            self._auto_timer = QTimer(self)
            self._auto_timer.setSingleShot(True)
            self._auto_timer.timeout.connect(self.close)
            self._auto_timer.start(self._auto_close_seconds * 1000)
