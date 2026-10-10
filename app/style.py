"""应用整体样式表（QSS）。"""

from __future__ import annotations

FONT_FAMILY = '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif'

ACCENT = "#16856b"
ACCENT_DARK = "#116c58"

APP_STYLE = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: #25313b;
}}
QWidget#Root {{ background: #f3f6f5; }}

QLabel#AppTitle {{ font-size: 21px; font-weight: 700; color: #18252c; }}
QLabel#AppSubtitle {{ font-size: 12px; color: #77848a; }}
QLabel#BrandIcon {{ min-width: 48px; min-height: 48px; }}

QFrame#HeroCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #183c3b, stop:1 #1c6153);
    border: 1px solid #245b50;
    border-radius: 18px;
}}
QLabel#CountdownCaption {{ font-size: 12px; font-weight: 600; color: #b7d8cd; }}
QLabel#Countdown {{ font-size: 48px; font-weight: 700; color: #ffffff; }}
QLabel#HeroDetail {{ font-size: 12px; color: #c1d8d1; }}
QLabel#StatusPill {{
    padding: 5px 11px; border-radius: 10px;
    font-size: 11px; font-weight: 600;
}}
QProgressBar#TimerProgress {{
    border: none; border-radius: 2px; background: #34665c;
}}
QProgressBar#TimerProgress::chunk {{ border-radius: 2px; background: #a9e2c4; }}

QFrame#Card {{
    background: #ffffff;
    border: 1px solid #e2e9e6;
    border-radius: 14px;
}}
QLabel#CardTitle {{ font-size: 15px; font-weight: 700; color: #1c292f; }}
QLabel#CardSubtitle {{ font-size: 11px; color: #839096; }}
QLabel#FieldTitle {{ font-size: 12px; font-weight: 600; color: #2c3940; }}
QLabel#FieldDetail {{ font-size: 11px; color: #849096; }}
QLabel#MutedLabel {{ color: #89959a; }}
QLabel#PeriodIcon {{
    min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px;
    border-radius: 8px; background: #eaf5f0; color: {ACCENT};
    font-size: 16px; qproperty-alignment: AlignCenter;
}}

QPushButton {{
    border-radius: 9px; padding: 8px 15px; min-height: 20px;
    font-size: 12px; font-weight: 600;
}}
QPushButton#Primary {{ background: {ACCENT}; color: #ffffff; border: 1px solid {ACCENT}; }}
QPushButton#Primary:hover {{ background: {ACCENT_DARK}; border-color: {ACCENT_DARK}; }}
QPushButton#Primary:pressed {{ background: #0e5848; }}
QPushButton#Secondary {{ background: #ffffff; border: 1px solid #dce5e1; color: #42514f; }}
QPushButton#Secondary:hover {{ background: #f5f9f7; border-color: #bdcec7; }}
QPushButton#QuietButton {{ background: transparent; border: 1px solid transparent; color: #667470; }}
QPushButton#QuietButton:hover {{ background: #e9efec; }}
QPushButton#Danger {{
    background: #fff; border: 1px solid #e6ece9; color: #9b5e5a;
    padding: 5px 10px; font-size: 11px;
}}
QPushButton#Danger:hover {{ background: #fff5f3; border-color: #f0d3ce; color: #a34740; }}
QPushButton#LinkButton {{
    background: #edf7f2; border: 1px solid #d8ece2; color: {ACCENT};
    padding: 7px 12px;
}}
QPushButton#LinkButton:hover {{ background: #e2f1e9; }}
QLabel#SaveFeedback {{ color: #87938f; font-size: 11px; }}

QSpinBox, QTimeEdit {{
    background: #f8faf9; border: 1px solid #e1e8e5; border-radius: 8px;
    padding: 5px 9px; min-height: 26px; color: #25313b;
    selection-background-color: #cce9dc;
}}
QSpinBox:hover, QTimeEdit:hover {{ border-color: #b7ccc3; background: #ffffff; }}
QSpinBox:focus, QTimeEdit:focus {{ border: 1px solid {ACCENT}; background: #ffffff; }}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{
    width: 18px; border: none; background: transparent;
}}
QCheckBox {{ spacing: 8px; background: transparent; }}
QWidget#OptionRow {{ border-radius: 9px; }}
QWidget#OptionRow:hover {{ background: #f2f8f5; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #cbd6d1; border-radius: 4px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: #a8b8b0; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 8px; background: transparent; }}

QMenu {{
    background: #ffffff; border: 1px solid #e1e8e5; border-radius: 10px;
    padding: 6px; color: #25313b;
}}
QMenu::item {{ padding: 8px 28px 8px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: #edf6f1; color: #176d58; }}
QMenu::separator {{ height: 1px; background: #e8eeeb; margin: 5px 8px; }}
"""

# 状态胶囊配色：背景色, 文字色
PILL_COLORS = {
    "running": ("#d8f2e4", "#12664d"),
    "paused": ("#e7ebea", "#586663"),
    "out_of_period": ("#f8edd1", "#8a641a"),
    "snoozing": ("#dcecf3", "#2e6676"),
    "resting": ("#e9e2f5", "#65528a"),
}


def pill_style(kind: str) -> str:
    bg, fg = PILL_COLORS.get(kind, PILL_COLORS["paused"])
    return (
        f"background-color: {bg}; color: {fg};"
        "padding: 5px 11px; border-radius: 10px;"
        "font-size: 11px; font-weight: 600;"
    )
