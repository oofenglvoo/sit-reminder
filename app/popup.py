"""置顶提醒弹窗窗口。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
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
        self.setFixedWidth(420)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        try:
            self.setWindowIcon(QIcon(str(icon_path())))
        except Exception:
            pass

        self._build_ui(snooze_minutes)
        self._apply_style()
        self._center_on_screen()

    def _build_ui(self, snooze_minutes: int) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("PopupCard")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(22, 45, 38, 42))
        card.setGraphicsEffect(shadow)
        content = QVBoxLayout(card)
        content.setContentsMargins(28, 26, 28, 24)
        content.setSpacing(13)

        icon = QLabel("↗")
        icon.setObjectName("PopupIcon")
        icon.setAlignment(Qt.AlignCenter)
        content.addWidget(icon, alignment=Qt.AlignHCenter)

        eyebrow = QLabel("TAKE A SHORT BREAK")
        eyebrow.setObjectName("PopupEyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        content.addWidget(eyebrow)

        title = QLabel("起来活动一下")
        title.setObjectName("PopupTitle")
        title.setAlignment(Qt.AlignCenter)

        message = QLabel("你已经坐了一段时间。站起来伸展、走动几步，\n也可以看看远处，让身体放松一下。")
        message.setObjectName("PopupMessage")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)

        tip = QLabel("站起来　·　伸展一下　·　看看远处")
        tip.setObjectName("PopupTip")
        tip.setAlignment(Qt.AlignCenter)

        buttons = QHBoxLayout()
        buttons.setSpacing(9)

        self.snooze_button = QPushButton(f"稍后 {snooze_minutes} 分钟")
        self.snooze_button.setObjectName("SnoozeButton")
        self.snooze_button.clicked.connect(self._on_snooze)

        self.ack_button = QPushButton("好的，我起来了")
        self.ack_button.setObjectName("AckButton")
        self.ack_button.setDefault(True)
        self.ack_button.clicked.connect(self._on_ack)

        buttons.addWidget(self.ack_button)
        buttons.addWidget(self.snooze_button)

        content.addWidget(title)
        content.addWidget(message)
        content.addWidget(tip)
        content.addSpacing(4)
        content.addLayout(buttons)
        root.addWidget(card)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif; }
            QFrame#PopupCard { background: #ffffff; border: 1px solid #e4ebe7; border-radius: 20px; }
            QLabel#PopupIcon {
                min-width: 52px; max-width: 52px; min-height: 52px; max-height: 52px;
                border-radius: 26px; background: #e7f4ec; color: #16856b;
                font-size: 25px; font-weight: 700;
            }
            QLabel#PopupEyebrow { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #6a9a86; }
            QLabel#PopupTitle { font-size: 22px; font-weight: 700; color: #1c2d2a; }
            QLabel#PopupMessage { font-size: 13px; line-height: 1.5; color: #65746f; }
            QLabel#PopupTip {
                padding: 10px; border-radius: 9px; background: #f3f8f5;
                font-size: 11px; color: #668076;
            }
            QPushButton {
                padding: 10px 14px; border-radius: 9px; font-size: 12px; font-weight: 600;
            }
            QPushButton#SnoozeButton {
                border: 1px solid #e0e8e4; background: #ffffff; color: #576761;
            }
            QPushButton#SnoozeButton:hover { background: #f5f8f6; }
            QPushButton#AckButton { background: #16856b; color: #ffffff; border: 1px solid #16856b; }
            QPushButton#AckButton:hover { background: #116c58; border-color: #116c58; }
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


class RestCountdownPopup(QWidget):
    """起身确认后显示的休息倒计时，结束或手动关闭时消失。"""

    def __init__(self, duration_seconds: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._remaining = max(0, int(duration_seconds))
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self.setWindowTitle(f"{__app_name__} · 休息中")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(420)
        try:
            self.setWindowIcon(QIcon(str(icon_path())))
        except Exception:
            pass

        self._build_ui()
        self._apply_style()
        self._update_countdown()
        self._center_on_screen()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("RestCard")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(22, 45, 38, 42))
        card.setGraphicsEffect(shadow)
        content = QVBoxLayout(card)
        content.setContentsMargins(28, 26, 28, 24)
        content.setSpacing(13)

        icon = QLabel("✓")
        icon.setObjectName("RestIcon")
        icon.setAlignment(Qt.AlignCenter)
        content.addWidget(icon, alignment=Qt.AlignHCenter)

        eyebrow = QLabel("GOOD JOB")
        eyebrow.setObjectName("RestEyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        content.addWidget(eyebrow)

        title = QLabel("休息一下")
        title.setObjectName("RestTitle")
        title.setAlignment(Qt.AlignCenter)
        content.addWidget(title)

        message = QLabel("站起来走动、伸展一下。休息结束后，\n会自动开始下一轮久坐计时。")
        message.setObjectName("RestMessage")
        message.setAlignment(Qt.AlignCenter)
        content.addWidget(message)

        self.countdown = QLabel("00:00")
        self.countdown.setObjectName("RestCountdown")
        self.countdown.setAlignment(Qt.AlignCenter)
        content.addWidget(self.countdown)

        self.progress = QProgressBar()
        self.progress.setObjectName("RestProgress")
        self.progress.setRange(0, max(1, self._remaining))
        self.progress.setValue(self._remaining)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        content.addWidget(self.progress)

        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("RestCloseButton")
        self.close_button.clicked.connect(self.close)
        content.addWidget(self.close_button)
        root.addWidget(card)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif; }
            QFrame#RestCard { background: #ffffff; border: 1px solid #e4ebe7; border-radius: 20px; }
            QLabel#RestIcon {
                min-width: 52px; max-width: 52px; min-height: 52px; max-height: 52px;
                border-radius: 26px; background: #e7f4ec; color: #16856b;
                font-size: 25px; font-weight: 700;
            }
            QLabel#RestEyebrow { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #6a9a86; }
            QLabel#RestTitle { font-size: 22px; font-weight: 700; color: #1c2d2a; }
            QLabel#RestMessage { font-size: 13px; color: #65746f; }
            QLabel#RestCountdown { font-size: 42px; font-weight: 700; color: #16856b; }
            QProgressBar#RestProgress { border: none; border-radius: 3px; background: #e8f0ec; }
            QProgressBar#RestProgress::chunk { border-radius: 3px; background: #42a887; }
            QPushButton#RestCloseButton {
                padding: 10px 14px; border-radius: 9px; font-size: 12px; font-weight: 600;
                border: 1px solid #e0e8e4; background: #ffffff; color: #576761;
            }
            QPushButton#RestCloseButton:hover { background: #f5f8f6; }
            """
        )

    def _format_remaining(self) -> str:
        minutes, seconds = divmod(self._remaining, 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _update_countdown(self) -> None:
        self.countdown.setText(self._format_remaining())
        self.progress.setRange(0, max(1, self._remaining))
        self.progress.setValue(self._remaining)

    def _tick(self) -> None:
        self._remaining = max(0, self._remaining - 1)
        self._update_countdown()
        if self._remaining == 0:
            self._timer.stop()
            self.close()

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        self.move(
            geo.x() + (geo.width() - self.width()) // 2,
            geo.y() + (geo.height() - self.height()) // 3,
        )

    def showEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        if self._remaining > 0:
            self._timer.start()
