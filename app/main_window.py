"""主设置窗口。"""

from __future__ import annotations

from PySide6.QtCore import QTime, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from . import __app_name__, __version__
from .autostart import is_supported as autostart_supported
from .config import (
    MAX_INTERVAL_MINUTES,
    MIN_INTERVAL_MINUTES,
    AppConfig,
    Period,
)
from .resources import icon_path
from .scheduler import Status
from .style import pill_style

STATUS_TEXT = {
    Status.RUNNING: "计时中",
    Status.PAUSED: "已暂停",
    Status.OUT_OF_PERIOD: "不在时段内",
    Status.SNOOZING: "稍后提醒中",
    Status.RESTING: "休息中",
}

STATUS_KIND = {
    Status.RUNNING: "running",
    Status.PAUSED: "paused",
    Status.OUT_OF_PERIOD: "out_of_period",
    Status.SNOOZING: "snoozing",
    Status.RESTING: "resting",
}


class NoWheelSpinBox(QSpinBox):
    """滚轮不改变数值，事件交给外层滚动区（页面正常滚动）。"""

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        event.ignore()


class NoWheelTimeEdit(QTimeEdit):
    """滚轮不改变时间，事件交给外层滚动区（页面正常滚动）。"""

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        event.ignore()


def _time_edit(value: str) -> QTimeEdit:
    edit = NoWheelTimeEdit()
    edit.setDisplayFormat("HH:mm")
    edit.setTime(QTime.fromString(value, "HH:mm"))
    return edit


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """创建一张白色卡片，返回 (卡片, 内容布局)。"""
    frame = QFrame()
    frame.setObjectName("Card")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(16, 14, 16, 14)
    outer.setSpacing(10)

    title_label = QLabel(title)
    title_label.setObjectName("CardTitle")
    outer.addWidget(title_label)

    body = QVBoxLayout()
    body.setContentsMargins(0, 0, 0, 0)
    body.setSpacing(8)
    outer.addLayout(body)
    return frame, body


class PeriodRow(QFrame):
    """一行时段编辑：开始 - 结束 + 删除。"""

    removed = Signal(object)

    def __init__(self, period: Period, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.start_edit = _time_edit(period.start)
        self.end_edit = _time_edit(period.end)

        remove = QPushButton("删除")
        remove.setObjectName("Danger")
        remove.setCursor(Qt.PointingHandCursor)
        remove.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.start_edit)
        layout.addWidget(QLabel("至"))
        layout.addWidget(self.end_edit)
        layout.addStretch(1)
        layout.addWidget(remove)

    def period(self) -> Period:
        return Period(
            start=self.start_edit.time().toString("HH:mm"),
            end=self.end_edit.time().toString("HH:mm"),
        )


class MainWindow(QWidget):
    """设置与状态界面。关闭时隐藏到托盘。"""

    configApplied = Signal(object)   # AppConfig
    testRequested = Signal()
    pauseToggled = Signal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._period_rows: list[PeriodRow] = []

        self.setObjectName("Root")
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(460, 640)
        self.setMinimumWidth(440)
        try:
            self.setWindowIcon(QIcon(str(icon_path())))
        except Exception:
            pass

        self._build_ui()
        self.load_config(config)

    # ---------- 构建界面 ----------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status_card())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("Root")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(14)
        content_layout.addWidget(self._build_reminder_card())
        content_layout.addWidget(self._build_periods_card())
        content_layout.addWidget(self._build_notify_card())
        content_layout.addWidget(self._build_system_card())
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        root.addLayout(self._build_footer())

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon_label = QLabel()
        pixmap = QPixmap(str(icon_path()))
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        layout.addWidget(icon_label)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        subtitle = QLabel(f"定时起身活动，远离久坐危害 · v{__version__}")
        subtitle.setObjectName("AppSubtitle")
        text_box.addWidget(title)
        text_box.addWidget(subtitle)
        layout.addLayout(text_box)
        layout.addStretch(1)

        self.status_pill = QLabel("—")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.setStyleSheet(pill_style("paused"))
        layout.addWidget(self.status_pill, alignment=Qt.AlignTop)
        return header

    def _build_status_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("StatusCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(2)
        self.countdown_caption = QLabel("距下次提醒")
        self.countdown_caption.setObjectName("CountdownCaption")
        self.countdown_label = QLabel("--:--")
        self.countdown_label.setObjectName("Countdown")
        left.addWidget(self.countdown_caption)
        left.addWidget(self.countdown_label)
        layout.addLayout(left)
        layout.addStretch(1)

        self.status_label = QLabel("-")
        self.status_label.setObjectName("Hint")
        layout.addWidget(self.status_label, alignment=Qt.AlignBottom)
        return card

    def _build_reminder_card(self) -> QWidget:
        card, body = _card("提醒设置")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.interval_spin = NoWheelSpinBox()
        self.interval_spin.setRange(MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES)
        self.interval_spin.setSuffix(" 分钟")
        grid.addWidget(QLabel("提醒间隔"), 0, 0)
        grid.addWidget(self.interval_spin, 0, 1)

        self.snooze_spin = NoWheelSpinBox()
        self.snooze_spin.setRange(1, 120)
        self.snooze_spin.setSuffix(" 分钟")
        grid.addWidget(QLabel("稍后提醒时长"), 1, 0)
        grid.addWidget(self.snooze_spin, 1, 1)

        self.rest_spin = NoWheelSpinBox()
        self.rest_spin.setRange(0, 120)
        self.rest_spin.setSuffix(" 分钟")
        grid.addWidget(QLabel("默认休息时长"), 2, 0)
        grid.addWidget(self.rest_spin, 2, 1)

        self.auto_close_spin = NoWheelSpinBox()
        self.auto_close_spin.setRange(0, 3600)
        self.auto_close_spin.setSuffix(" 秒")
        grid.addWidget(QLabel("弹窗自动关闭"), 3, 0)
        grid.addWidget(self.auto_close_spin, 3, 1)

        grid.setColumnStretch(1, 1)
        body.addLayout(grid)

        hint = QLabel(
            "提醒严格对齐时段起点（起点 + N × 间隔），每次提醒后自动休息。"
            "弹窗自动关闭填 0 表示不自动关闭。"
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        body.addWidget(hint)
        return card

    def _build_periods_card(self) -> QWidget:
        card, body = _card("提醒时段")
        hint = QLabel("仅在这些时段内计时并提醒，时段外自动暂停。")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        body.addWidget(hint)

        self.periods_container = QWidget()
        self.periods_layout = QVBoxLayout(self.periods_container)
        self.periods_layout.setContentsMargins(0, 0, 0, 0)
        self.periods_layout.setSpacing(8)
        self.periods_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.periods_container)
        scroll.setMinimumHeight(96)
        scroll.setMaximumHeight(150)
        body.addWidget(scroll)

        add_button = QPushButton("+ 添加时段")
        add_button.setObjectName("LinkButton")
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(
            lambda: self._add_period_row(Period("09:00", "10:00"))
        )
        body.addWidget(add_button, alignment=Qt.AlignRight)
        return card

    def _build_notify_card(self) -> QWidget:
        card, body = _card("提醒方式")
        self.toast_check = QCheckBox("Windows 系统通知")
        self.popup_check = QCheckBox("弹出提醒窗口")
        self.sound_check = QCheckBox("播放提示音")
        for check in (self.toast_check, self.popup_check, self.sound_check):
            check.setCursor(Qt.PointingHandCursor)
            body.addWidget(check)
        return card

    def _build_system_card(self) -> QWidget:
        card, body = _card("系统")
        self.autostart_check = QCheckBox("开机自动启动")
        self.start_minimized_check = QCheckBox("启动时最小化到托盘")
        for check in (self.autostart_check, self.start_minimized_check):
            check.setCursor(Qt.PointingHandCursor)
            body.addWidget(check)

        self.autostart_hint = QLabel()
        self.autostart_hint.setObjectName("Hint")
        self.autostart_hint.setWordWrap(True)
        body.addWidget(self.autostart_hint)

        if not autostart_supported():
            self.autostart_check.setEnabled(False)
            self.autostart_hint.setText("当前系统不支持开机自启动设置。")
        else:
            self.autostart_hint.setText("开机后自动在后台运行，静默驻留托盘。")
        return card

    def _build_footer(self) -> QHBoxLayout:
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.test_button = QPushButton("测试提醒")
        self.test_button.setObjectName("Secondary")
        self.test_button.setCursor(Qt.PointingHandCursor)
        self.test_button.clicked.connect(self.testRequested)

        self.pause_button = QPushButton("暂停")
        self.pause_button.setObjectName("Secondary")
        self.pause_button.setCursor(Qt.PointingHandCursor)
        self.pause_button.clicked.connect(self.pauseToggled)

        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("Primary")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._on_save)

        buttons.addWidget(self.test_button)
        buttons.addWidget(self.pause_button)
        buttons.addStretch(1)
        buttons.addWidget(self.save_button)
        return buttons

    # ---------- 配置加载/收集 ----------
    def load_config(self, config: AppConfig) -> None:
        self._config = config
        self.interval_spin.setValue(config.interval_minutes)
        self.snooze_spin.setValue(config.snooze_minutes)
        self.rest_spin.setValue(config.rest_minutes)
        self.auto_close_spin.setValue(config.popup_auto_close_seconds)
        self.start_minimized_check.setChecked(config.start_minimized)
        self.autostart_check.setChecked(config.autostart)
        self.toast_check.setChecked(config.notify.toast)
        self.popup_check.setChecked(config.notify.popup)
        self.sound_check.setChecked(config.notify.sound)

        self._clear_period_rows()
        for period in config.periods:
            self._add_period_row(period)

    def _clear_period_rows(self) -> None:
        for row in list(self._period_rows):
            self._remove_period_row(row)

    def _add_period_row(self, period: Period) -> None:
        row = PeriodRow(period)
        row.removed.connect(self._remove_period_row)
        self._period_rows.append(row)
        self.periods_layout.insertWidget(self.periods_layout.count() - 1, row)

    def _remove_period_row(self, row: PeriodRow) -> None:
        if row in self._period_rows:
            self._period_rows.remove(row)
        row.setParent(None)
        row.deleteLater()

    def collect_config(self) -> AppConfig:
        """从界面读取配置；非法时段会被丢弃。"""
        periods: list[Period] = []
        for row in self._period_rows:
            period = row.period()
            if period.is_valid():
                periods.append(period)
        if not periods:
            periods = [Period("09:00", "18:00")]

        config = AppConfig(
            enabled=self._config.enabled,
            interval_minutes=self.interval_spin.value(),
            periods=periods,
            notify=self._config.notify,
            snooze_minutes=self.snooze_spin.value(),
            rest_minutes=self.rest_spin.value(),
            popup_auto_close_seconds=self.auto_close_spin.value(),
            start_minimized=self.start_minimized_check.isChecked(),
            autostart=self.autostart_check.isChecked(),
        )
        config.notify.toast = self.toast_check.isChecked()
        config.notify.popup = self.popup_check.isChecked()
        config.notify.sound = self.sound_check.isChecked()
        return config

    def _on_save(self) -> None:
        self._config = self.collect_config()
        self.configApplied.emit(self._config)

    # ---------- 状态更新 ----------
    def update_status(self, status: Status, remaining_seconds: float) -> None:
        self.status_label.setText(STATUS_TEXT.get(status, "-"))
        self.status_pill.setText(STATUS_TEXT.get(status, "—"))
        self.status_pill.setStyleSheet(pill_style(STATUS_KIND.get(status, "paused")))

        if status is Status.RESTING:
            self.countdown_caption.setText("休息剩余")
        elif status is Status.SNOOZING:
            self.countdown_caption.setText("稍后提醒")
        else:
            self.countdown_caption.setText("距下次提醒")

        if status in (Status.RUNNING, Status.SNOOZING, Status.RESTING):
            minutes = int(remaining_seconds) // 60
            seconds = int(remaining_seconds) % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        else:
            self.countdown_label.setText("--:--")

    def set_paused(self, paused: bool) -> None:
        self.pause_button.setText("恢复" if paused else "暂停")

    # ---------- 窗口行为 ----------
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        event.ignore()
        self.hide()
