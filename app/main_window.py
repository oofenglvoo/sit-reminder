"""主设置窗口。"""

from __future__ import annotations

from PySide6.QtCore import QTime, Qt, QSize, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
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


class _OptionCheckBox(QCheckBox):
    """DPI-independent custom checkbox with a crisp vector checkmark."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("OptionCheck")
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName("设置选项")
        self.setFixedSize(26, 30)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect_size = 18.0
        rect = self.rect()
        x = (rect.width() - rect_size) / 2
        y = (rect.height() - rect_size) / 2
        box = QPainterPath()
        box.addRoundedRect(x, y, rect_size, rect_size, 5.5, 5.5)

        if not self.isEnabled():
            fill = QColor("#e9efec") if self.isChecked() else QColor("#f5f7f6")
            border = QColor("#d9e2de")
            check_color = QColor("#97aaa1")
        elif self.isChecked():
            fill = QColor("#16856b")
            border = QColor("#16856b")
            check_color = QColor("#ffffff")
        elif self.underMouse():
            fill = QColor("#f0f7f3")
            border = QColor("#72aa94")
            check_color = QColor("#ffffff")
        else:
            fill = QColor("#ffffff")
            border = QColor("#c6d3cd")
            check_color = QColor("#ffffff")

        painter.setPen(QPen(border, 1.2))
        painter.setBrush(fill)
        painter.drawPath(box)

        if self.isChecked():
            check = QPainterPath()
            check.moveTo(x + 4.2, y + 9.3)
            check.lineTo(x + 7.5, y + 12.3)
            check.lineTo(x + 13.8, y + 5.7)
            painter.setPen(QPen(check_color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(check)

        if self.hasFocus():
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(22, 133, 107, 90), 1.0))
            focus = QPainterPath()
            focus.addRoundedRect(x - 3, y - 3, rect_size + 6, rect_size + 6, 8, 8)
            painter.drawPath(focus)

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt 命名)
        return QSize(26, 30)

    def nextCheckState(self) -> None:  # noqa: N802 (Qt 命名)
        self.setChecked(not self.isChecked())


def _time_edit(value: str) -> QTimeEdit:
    edit = NoWheelTimeEdit()
    edit.setDisplayFormat("HH:mm")
    edit.setTime(QTime.fromString(value, "HH:mm"))
    return edit


def _card(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    """创建统一风格的内容卡片。"""
    frame = QFrame()
    frame.setObjectName("Card")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(18, 16, 18, 16)
    outer.setSpacing(14)

    heading = QVBoxLayout()
    heading.setSpacing(3)
    title_label = QLabel(title)
    title_label.setObjectName("CardTitle")
    heading.addWidget(title_label)
    if subtitle:
        detail = QLabel(subtitle)
        detail.setObjectName("CardSubtitle")
        detail.setWordWrap(True)
        heading.addWidget(detail)
    outer.addLayout(heading)

    body = QVBoxLayout()
    body.setContentsMargins(0, 0, 0, 0)
    body.setSpacing(10)
    outer.addLayout(body)
    return frame, body


def _field_row(title: str, detail: str, control: QWidget) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)

    text = QVBoxLayout()
    text.setSpacing(2)
    label = QLabel(title)
    label.setObjectName("FieldTitle")
    description = QLabel(detail)
    description.setObjectName("FieldDetail")
    description.setWordWrap(True)
    text.addWidget(label)
    text.addWidget(description)
    layout.addLayout(text, 1)
    control.setMinimumWidth(132)
    layout.addWidget(control)
    return row


class PeriodRow(QFrame):
    """一行时段编辑：开始 - 结束 + 删除。"""

    removed = Signal(object)

    def __init__(self, period: Period, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.start_edit = _time_edit(period.start)
        self.end_edit = _time_edit(period.end)

        remove = QPushButton("移除")
        remove.setObjectName("Danger")
        remove.setCursor(Qt.PointingHandCursor)
        remove.setToolTip("移除此提醒时段")
        remove.clicked.connect(lambda: self.removed.emit(self))

        period_icon = QLabel("◷")
        period_icon.setObjectName("PeriodIcon")
        layout.addWidget(period_icon)
        layout.addWidget(self.start_edit, 1)
        to_label = QLabel("至")
        to_label.setObjectName("MutedLabel")
        layout.addWidget(to_label)
        layout.addWidget(self.end_edit, 1)
        layout.addWidget(remove)

    def period(self) -> Period:
        return Period(
            start=self.start_edit.time().toString("HH:mm"),
            end=self.end_edit.time().toString("HH:mm"),
        )


class _OptionRow(QWidget):
    """整行均可点击的偏好设置选项。"""

    def __init__(self, title: str, detail: str) -> None:
        super().__init__()
        self.setObjectName("OptionRow")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(14)

        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("FieldTitle")
        self.title.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.detail = QLabel(detail)
        self.detail.setObjectName("FieldDetail")
        self.detail.setAttribute(Qt.WA_TransparentForMouseEvents)
        text.addWidget(self.title)
        text.addWidget(self.detail)
        layout.addLayout(text, 1)

        self.checkbox = _OptionCheckBox()
        self.checkbox.setAccessibleName(title)
        layout.addWidget(self.checkbox, alignment=Qt.AlignRight | Qt.AlignVCenter)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        if event.button() == Qt.LeftButton:
            self.checkbox.setChecked(not self.checkbox.isChecked())
            event.accept()
            return
        super().mousePressEvent(event)


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
        self.resize(600, 820)
        self.setMinimumSize(520, 680)
        try:
            self.setWindowIcon(QIcon(str(icon_path())))
        except Exception:
            pass

        self._build_ui()
        self.load_config(config)

    # ---------- 构建界面 ----------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(18)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status_card())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("Root")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 4)
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
        icon_label.setObjectName("BrandIcon")
        icon_label.setFixedSize(48, 48)
        pixmap = QIcon(str(icon_path())).pixmap(QSize(48, 48))
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        subtitle = QLabel(f"让规律活动，成为工作节奏的一部分  ·  v{__version__}")
        subtitle.setObjectName("AppSubtitle")
        text_box.addWidget(title)
        text_box.addWidget(subtitle)
        layout.addLayout(text_box)
        layout.addStretch(1)

        return header

    def _build_status_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("HeroCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.countdown_caption = QLabel("下一次活动")
        self.countdown_caption.setObjectName("CountdownCaption")
        top.addWidget(self.countdown_caption)
        top.addStretch(1)
        self.status_pill = QLabel("—")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.setStyleSheet(pill_style("paused"))
        top.addWidget(self.status_pill)
        layout.addLayout(top)

        self.countdown_label = QLabel("--:--")
        self.countdown_label.setObjectName("Countdown")
        layout.addWidget(self.countdown_label)

        self.status_label = QLabel("正在为你保持节奏")
        self.status_label.setObjectName("HeroDetail")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("TimerProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        layout.addSpacing(7)
        layout.addWidget(self.progress)
        return card

    def _build_reminder_card(self) -> QWidget:
        card, body = _card("提醒节奏", "按你的工作节奏安排提醒与休息时间。")

        self.interval_spin = NoWheelSpinBox()
        self.interval_spin.setRange(MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES)
        self.interval_spin.setSuffix(" 分钟")
        body.addWidget(_field_row("久坐提醒间隔", "每隔一段时间提醒你起身活动", self.interval_spin))

        self.snooze_spin = NoWheelSpinBox()
        self.snooze_spin.setRange(1, 120)
        self.snooze_spin.setSuffix(" 分钟")
        body.addWidget(_field_row("稍后提醒", "暂时不方便时，延后再次提醒", self.snooze_spin))

        self.rest_spin = NoWheelSpinBox()
        self.rest_spin.setRange(0, 120)
        self.rest_spin.setSuffix(" 分钟")
        body.addWidget(_field_row("活动休息", "确认起身后，留出一段休息时间", self.rest_spin))

        self.auto_close_spin = NoWheelSpinBox()
        self.auto_close_spin.setRange(0, 3600)
        self.auto_close_spin.setSuffix(" 秒")
        body.addWidget(_field_row("弹窗自动关闭", "设为 0 时，弹窗会一直显示", self.auto_close_spin))
        return card

    def _build_periods_card(self) -> QWidget:
        card, body = _card("提醒时段", "只在这些时间段内计时，时段外自动暂停。")

        self.periods_container = QWidget()
        self.periods_layout = QVBoxLayout(self.periods_container)
        self.periods_layout.setContentsMargins(0, 0, 0, 0)
        self.periods_layout.setSpacing(8)
        self.periods_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.periods_container)
        scroll.setMinimumHeight(90)
        scroll.setMaximumHeight(180)
        body.addWidget(scroll)

        add_button = QPushButton("＋ 添加时段")
        add_button.setObjectName("LinkButton")
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(
            lambda: self._add_period_row(Period("09:00", "10:00"))
        )
        body.addWidget(add_button, alignment=Qt.AlignRight)
        return card

    def _build_notify_card(self) -> QWidget:
        card, body = _card("提醒方式", "选择你希望收到提醒的方式，可同时开启多项。")
        self.toast_check = self._option("系统通知", "在 Windows 通知中心显示提醒")
        self.popup_check = self._option("置顶弹窗", "显示可操作的提醒窗口")
        self.sound_check = self._option("提示音", "播放轻柔提示音")
        for check in (self.toast_check, self.popup_check, self.sound_check):
            body.addWidget(check.option_row)
        return card

    @staticmethod
    def _option(title: str, detail: str) -> QCheckBox:
        row = _OptionRow(title, detail)
        check = row.checkbox
        check.option_row = row
        return check

    def _build_system_card(self) -> QWidget:
        card, body = _card("系统偏好", "控制应用启动时的行为。")
        self.autostart_check = self._option("开机时启动", "登录 Windows 后自动在后台运行")
        body.addWidget(self.autostart_check.option_row)

        self.autostart_hint = QLabel()
        self.autostart_hint.setObjectName("Hint")
        self.autostart_hint.setWordWrap(True)
        body.addWidget(self.autostart_hint)

        if not autostart_supported():
            self.autostart_check.setEnabled(False)
            self.autostart_hint.setText("当前系统不支持开机自启动设置。")
        else:
            self.autostart_hint.setText("开机后自动在后台运行，静默驻留托盘。")
        self.autostart_hint.setObjectName("CardSubtitle")
        return card

    def _build_footer(self) -> QHBoxLayout:
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.test_button = QPushButton("试听提醒")
        self.test_button.setObjectName("Secondary")
        self.test_button.setCursor(Qt.PointingHandCursor)
        self.test_button.clicked.connect(self.testRequested)

        self.pause_button = QPushButton("暂停计时")
        self.pause_button.setObjectName("QuietButton")
        self.pause_button.setCursor(Qt.PointingHandCursor)
        self.pause_button.clicked.connect(self.pauseToggled)

        self.save_button = QPushButton("保存设置")
        self.save_button.setObjectName("Primary")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._on_save)

        buttons.addWidget(self.test_button)
        buttons.addWidget(self.pause_button)
        buttons.addStretch(1)
        self.save_feedback = QLabel("设置仅在保存后生效")
        self.save_feedback.setObjectName("SaveFeedback")
        buttons.addWidget(self.save_feedback)
        buttons.addWidget(self.save_button)
        return buttons

    # ---------- 配置加载/收集 ----------
    def load_config(self, config: AppConfig) -> None:
        self._config = config
        self.interval_spin.setValue(config.interval_minutes)
        self.snooze_spin.setValue(config.snooze_minutes)
        self.rest_spin.setValue(config.rest_minutes)
        self.auto_close_spin.setValue(config.popup_auto_close_seconds)
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
            autostart=self.autostart_check.isChecked(),
        )
        config.notify.toast = self.toast_check.isChecked()
        config.notify.popup = self.popup_check.isChecked()
        config.notify.sound = self.sound_check.isChecked()
        return config

    def _on_save(self) -> None:
        self._config = self.collect_config()
        self.configApplied.emit(self._config)
        self.save_feedback.setText("✓ 已保存")

    # ---------- 状态更新 ----------
    def update_status(self, status: Status, remaining_seconds: float) -> None:
        status_detail = {
            Status.RUNNING: "专注工作一段时间后，记得起来活动。",
            Status.PAUSED: "计时已暂停，准备好后可随时恢复。",
            Status.OUT_OF_PERIOD: "当前不在提醒时段内，之后会自动继续。",
            Status.SNOOZING: "已为你延后提醒，稍后再回来活动。",
            Status.RESTING: "很好，给自己一点活动和放松时间。",
        }
        self.status_label.setText(status_detail.get(status, "保持轻松，规律活动。"))
        self.status_pill.setText(STATUS_TEXT.get(status, "—"))
        self.status_pill.setStyleSheet(pill_style(STATUS_KIND.get(status, "paused")))

        if status is Status.RESTING:
            self.countdown_caption.setText("本次休息还剩")
        elif status is Status.SNOOZING:
            self.countdown_caption.setText("稍后提醒将在")
        else:
            self.countdown_caption.setText("距离下一次提醒")

        if status in (Status.RUNNING, Status.SNOOZING, Status.RESTING):
            minutes = int(remaining_seconds) // 60
            seconds = int(remaining_seconds) % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            total_seconds = {
                Status.RUNNING: self._config.interval_seconds,
                Status.SNOOZING: self._config.snooze_minutes * 60,
                Status.RESTING: self._config.rest_seconds,
            }[status]
            elapsed = max(0, total_seconds - int(remaining_seconds))
            self.progress.setValue(min(100, int(elapsed * 100 / max(1, total_seconds))))
        else:
            self.countdown_label.setText("--:--")
            self.progress.setValue(0)

    def set_paused(self, paused: bool) -> None:
        self.pause_button.setText("恢复计时" if paused else "暂停计时")

    # ---------- 窗口行为 ----------
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        event.ignore()
        self.hide()
