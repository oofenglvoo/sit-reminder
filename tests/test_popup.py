"""休息倒计时弹窗的生命周期测试。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from app.popup import ReminderPopup, RestCountdownPopup


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _drag(widget, start: QPoint, end: QPoint) -> None:
    app = _app()
    press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        start,
        start,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    move = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        end,
        end,
        Qt.NoButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    app.sendEvent(widget, press)
    app.sendEvent(widget, move)


def test_rest_popup_counts_down_and_closes_at_zero():
    app = _app()
    popup = RestCountdownPopup(2)
    popup.show()
    app.processEvents()

    assert popup.countdown.text() == "00:02"
    popup._tick()
    assert popup.countdown.text() == "00:01"
    assert popup.isVisible()

    popup._tick()
    assert popup.countdown.text() == "00:00"
    assert not popup.isVisible()
    app.processEvents()


def test_rest_popup_can_be_closed_manually():
    app = _app()
    popup = RestCountdownPopup(60)
    popup.show()
    app.processEvents()

    popup.close_button.click()
    assert not popup.isVisible()
    app.processEvents()


def test_rest_popup_can_be_dragged():
    app = _app()
    popup = RestCountdownPopup(60)
    popup.show()
    app.processEvents()

    origin = popup.pos()
    _drag(popup, QPoint(200, 40), QPoint(260, 90))
    assert popup.pos() == origin + QPoint(60, 50)
    popup.close()
    app.processEvents()


def test_reminder_popup_can_be_dragged():
    app = _app()
    popup = ReminderPopup(snooze_minutes=5)
    popup.show()
    app.processEvents()

    origin = popup.pos()
    _drag(popup, QPoint(200, 40), QPoint(150, 20))
    assert popup.pos() == origin + QPoint(-50, -20)
    popup.close()
    app.processEvents()
