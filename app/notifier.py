"""提醒发送：Windows Toast + 置顶弹窗 + 提示音。"""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtWidgets import QSystemTrayIcon

from . import __app_name__
from .config import AppConfig
from .popup import ReminderPopup, RestCountdownPopup
from .resources import sound_path

TOAST_TITLE = "久坐提醒"
TOAST_BODY = "该起来活动一下了，站起来伸展一下、走动几步吧。"


class Notifier(QObject):
    """统一触发三种提醒方式，并把弹窗的用户操作转成信号。"""

    acknowledged = Signal()  # 用户点击“我起来了”
    snoozed = Signal()       # 用户点击“稍后提醒”

    def __init__(
        self,
        tray_icon: QSystemTrayIcon | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._tray = tray_icon
        self._toaster = None
        self._sound = None
        self._popup: ReminderPopup | None = None
        self._popup_affects = False
        self._rest_popup: RestCountdownPopup | None = None

        self._init_toaster()
        self._init_sound()

    # ---------- 初始化 ----------
    def _init_toaster(self) -> None:
        try:
            from windows_toasts import WindowsToaster

            self._toaster = WindowsToaster(__app_name__)
        except Exception:
            self._toaster = None

    def _init_sound(self) -> None:
        try:
            from PySide6.QtMultimedia import QSoundEffect

            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(str(sound_path())))
            effect.setVolume(0.8)
            self._sound = effect
        except Exception:
            self._sound = None

    # ---------- 对外接口 ----------
    def notify(self, config: AppConfig) -> None:
        """按配置发送提醒。"""
        if config.notify.toast:
            self._send_toast(TOAST_TITLE, TOAST_BODY)
        if config.notify.sound:
            self._play_sound()
        if config.notify.popup:
            self._show_popup(
                config.snooze_minutes,
                config.popup_auto_close_seconds,
                affects_tracker=True,
            )

    def test(self, config: AppConfig) -> None:
        """测试提醒：尝试全部发送，但不影响真实的提醒倒计时。"""
        self._send_toast(TOAST_TITLE, TOAST_BODY)
        self._play_sound()
        self._show_popup(
            config.snooze_minutes,
            config.popup_auto_close_seconds,
            affects_tracker=False,
        )

    def show_rest_countdown(self, duration_seconds: int) -> None:
        """显示休息倒计时；手动关闭弹窗不影响实际休息计时。"""
        if duration_seconds <= 0:
            return
        if self._rest_popup is not None:
            self._rest_popup.close()
        popup = RestCountdownPopup(duration_seconds)
        self._rest_popup = popup
        popup.destroyed.connect(
            lambda _obj=None, closing_popup=popup: self._on_rest_popup_destroyed(
                closing_popup
            )
        )
        popup.show()

    # ---------- 内部实现 ----------
    def _send_toast(self, title: str, body: str) -> None:
        if self._toaster is not None:
            try:
                from windows_toasts import Toast

                self._toaster.show_toast(Toast([title, body]))
                return
            except Exception:
                pass
        # 回退：托盘气泡
        if self._tray is not None:
            try:
                self._tray.showMessage(title, body, QSystemTrayIcon.Information, 8000)
            except Exception:
                pass

    def _play_sound(self) -> None:
        if self._sound is not None:
            try:
                if self._sound.status() == self._sound.Status.Ready:
                    self._sound.play()
                    return
            except Exception:
                pass
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _show_popup(
        self,
        snooze_minutes: int,
        auto_close_seconds: int,
        affects_tracker: bool,
    ) -> None:
        if self._popup is not None and self._popup.isVisible():
            self._popup.raise_()
            self._popup.activateWindow()
            if affects_tracker and not self._popup_affects:
                self._connect_popup(self._popup)
                self._popup_affects = True
            return

        popup = ReminderPopup(snooze_minutes, auto_close_seconds)
        if affects_tracker:
            self._connect_popup(popup)
        popup.destroyed.connect(self._on_popup_destroyed)
        self._popup = popup
        self._popup_affects = affects_tracker
        popup.show()

    def _connect_popup(self, popup: ReminderPopup) -> None:
        popup.acknowledged.connect(self.acknowledged)
        popup.snoozed.connect(self.snoozed)

    def _on_popup_destroyed(self) -> None:
        self._popup = None
        self._popup_affects = False

    def _on_rest_popup_destroyed(self, popup: RestCountdownPopup) -> None:
        if self._rest_popup is popup:
            self._rest_popup = None
