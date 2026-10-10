"""应用整体样式表（QSS）。"""

from __future__ import annotations

FONT_FAMILY = '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif'

ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"

APP_STYLE = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: #1f2937;
}}
QWidget#Root {{
    background-color: #f4f5f7;
}}

/* 头部 */
QLabel#AppTitle {{
    font-size: 19px;
    font-weight: 700;
    color: #111827;
}}
QLabel#AppSubtitle {{
    font-size: 12px;
    color: #6b7280;
}}

/* 状态卡 */
QFrame#StatusCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #eef2ff, stop:1 #e0f2fe);
    border: 1px solid #dbeafe;
    border-radius: 14px;
}}
QLabel#Countdown {{
    font-size: 38px;
    font-weight: 700;
    color: {ACCENT};
}}
QLabel#CountdownCaption {{
    font-size: 12px;
    color: #6b7280;
}}
QLabel#StatusPill {{
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}}

/* 卡片 */
QFrame#Card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}}
QLabel#CardTitle {{
    font-size: 14px;
    font-weight: 600;
    color: #111827;
}}
QLabel#Hint {{
    font-size: 12px;
    color: #6b7280;
}}

/* 按钮 */
QPushButton {{
    border-radius: 8px;
    padding: 7px 16px;
    min-height: 20px;
}}
QPushButton#Primary {{
    background: {ACCENT};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton#Primary:hover {{ background: {ACCENT_DARK}; }}
QPushButton#Primary:pressed {{ background: #1e40af; }}
QPushButton#Secondary {{
    background: #ffffff;
    border: 1px solid #d1d5db;
    color: #374151;
}}
QPushButton#Secondary:hover {{ background: #f3f4f6; }}
QPushButton#Danger {{
    background: #ffffff;
    border: 1px solid #fca5a5;
    color: #dc2626;
    padding: 5px 12px;
}}
QPushButton#Danger:hover {{ background: #fef2f2; }}
QPushButton#LinkButton {{
    background: transparent;
    border: none;
    color: {ACCENT};
    font-weight: 600;
    padding: 5px 8px;
}}
QPushButton#LinkButton:hover {{ color: {ACCENT_DARK}; }}

/* 输入控件 */
QSpinBox, QTimeEdit {{
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
}}
QSpinBox:focus, QTimeEdit:focus {{ border: 1px solid {ACCENT}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
}}

/* 滚动区透明 */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #d1d5db; border-radius: 4px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: #9ca3af; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

# 状态胶囊配色：背景色, 文字色
PILL_COLORS = {
    "running": ("#dcfce7", "#16a34a"),
    "paused": ("#e5e7eb", "#4b5563"),
    "out_of_period": ("#fef3c7", "#d97706"),
    "snoozing": ("#dbeafe", "#2563eb"),
    "resting": ("#ede9fe", "#7c3aed"),
}


def pill_style(kind: str) -> str:
    bg, fg = PILL_COLORS.get(kind, PILL_COLORS["paused"])
    return (
        f"background-color: {bg}; color: {fg};"
        "padding: 4px 14px; border-radius: 12px;"
        "font-size: 12px; font-weight: 600;"
    )
