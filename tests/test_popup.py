"""休息倒计时弹窗的生命周期测试。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.popup import RestCountdownPopup


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


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
