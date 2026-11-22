"""Two warm palettes for the native Qt shell and its dialogs."""
from functools import lru_cache
import os
import re

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ..brand import ICONS
from ..state import SPXError

THEME_FILE = "appearance.json"
THEMES = {
    "dark": {
        "canvas": "#1B1A17", "sidebar": "#211F1C", "paper": "#26241F",
        "field": "#22201C", "inset": "#201E1A", "line": "#413C33",
        "edge": "#64584B", "ink": "#F5EFE5", "muted": "#C0B6A8",
        "faint": "#A69B8B", "primary": "#DFA78A", "on_primary": "#2B1C15",
        "primary_hover": "#EAB69B", "primary_down": "#CF9478", "clay": "#E7AE92",
        "hero": "#302722", "hero_line": "#63483A", "wash": "#3C3028",
        "hover": "#343029", "disabled": "#2A2722", "quiet": "#857C6F",
        "rail": "#191714", "thumb": "#645849", "thumb_hover": "#877463",
    },
    "light": {
        "canvas": "#FAF9F5", "sidebar": "#F1EEE7", "paper": "#FFFEFB",
        "field": "#FFFCF8", "inset": "#F6F2EB", "line": "#DED7CA",
        "edge": "#AA9A87", "ink": "#28231E", "muted": "#5B5248",
        "faint": "#6D645A", "primary": "#A34D34", "on_primary": "#FFFFFF",
        "primary_hover": "#8D402A", "primary_down": "#793624", "clay": "#8D4029",
        "hero": "#F5E7DB", "hero_line": "#D7BAA7", "wash": "#EEE1D4",
        "hover": "#EFE9DF", "disabled": "#F0EBE3", "quiet": "#817467",
        "rail": "#ECE6DC", "thumb": "#BEB1A0", "thumb_hover": "#9D8875",
    },
}


def read_theme(store):
    try:
        value = store.read(THEME_FILE, {})
    except (OSError, SPXError):
        return "dark"
    if isinstance(value, dict) and value.get("schema") == 1 and value.get("theme") in ("dark", "light"):
        return value["theme"]
    return "dark"


GLYPHS = {
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
    "moon": '<path d="M20.9 13.4A9 9 0 0 1 10.6 3.1 9 9 0 1 0 20.9 13.4Z"/>',
    "overview": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "connection": '<circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="m8.5 8.5 7 7M15 3h6v6M3 15v6h6"/>',
    "network": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18M5 7h14M5 17h14"/>',
    "workspace": '<path d="M3 8V5h7l2 3h9v12H3z"/><path d="m8 12 3 3-3 3m6 0h3"/>',
    "downloads": '<path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5"/>',
    "logs": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "resources": '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/>',
    "settings": '<path d="M3 6h18M3 12h18M3 18h18m-13-15v6m9 0v6m-10 0v6"/>',
    "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    "external": '<path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7"/>',
    "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/>',
}


@lru_cache(maxsize=64)
def icon(name, color=THEMES["dark"]["muted"], size=20):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def apply(app, theme="dark"):
    previous = app.property("spxTheme")
    if previous == theme:
        return
    if previous is None:
        app.setStyle("Fusion")
        app.setFont(QFont("Microsoft YaHei UI" if os.name == "nt" else "Noto Sans CJK SC", 10))
    colors = THEMES[theme]
    palette = QPalette()
    for role, token in (
        ("Window", "canvas"), ("WindowText", "ink"), ("Base", "field"),
        ("AlternateBase", "inset"), ("Text", "ink"), ("Button", "paper"),
        ("ButtonText", "ink"), ("Highlight", "wash"), ("HighlightedText", "ink"),
        ("PlaceholderText", "faint"), ("ToolTipBase", "paper"), ("ToolTipText", "ink"),
    ):
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(colors[token]))
    app.setPalette(palette)
    tokens = {
        **colors,
        "display_font": "SimSun" if os.name == "nt" else "Noto Serif CJK SC",
        "check_icon": (ICONS / "check.svg").as_posix().replace('"', '\\"'),
    }
    app.setStyleSheet(re.sub(r"@([a-z_]+)@", lambda match: tokens[match[1]], STYLES))
    app.setProperty("spxTheme", theme)


STYLES = """
QWidget { color: @ink@; font-size: 14px; }
QMainWindow, QDialog { background: @canvas@; }
QFrame#Shell { background: @canvas@; border: 1px solid @line@; border-radius: 11px; }
QWidget#TitleBar { background: @canvas@; border-bottom: 1px solid @line@; }
QFrame#WorkbenchNav { background: @sidebar@; border-bottom: 1px solid @line@; }
QFrame#StatusStrip { border-top: 1px solid @line@; background: @sidebar@; }
QFrame#Subnav { border-bottom: 1px solid @line@; }
QWidget#Page, QWidget#Viewport { background: @canvas@; }
QScrollArea { border: none; background: transparent; }
QFrame#Section { background: transparent; border: none; border-top: 1px solid @line@; }
QFrame#Hero {
    background: qlineargradient(x1:0, y1:0, x2:0.93, y2:1, stop:0 @hero@, stop:1 @wash@);
    border: 1px solid @hero_line@;
    border-radius: 16px;
}
QFrame#LaunchPanel { background: @paper@; border: 1px solid @line@; border-radius: 14px; }
QFrame#RoutePanel { background: @inset@; border: 1px solid @line@; border-radius: 12px; }
QFrame#Inset { background: @inset@; border: 1px solid @line@; border-radius: 8px; }
QLabel { background: transparent; border: none; }
QLabel#Heading { font-family: "@display_font@"; font-size: 36px; font-weight: 600; }
QLabel#HeroTitle { font-family: "@display_font@"; font-size: 39px; font-weight: 600; }
QLabel#ProjectTitle { font-family: "@display_font@"; font-size: 25px; font-weight: 600; }
QLabel#SectionTitle { font-size: 17px; font-weight: 600; }
QLabel#Brand { font-family: "Georgia"; font-size: 17px; font-weight: 600; }
QLabel#RouteText { font-family: "Consolas"; font-size: 15px; }
QLabel#Metric { font-size: 19px; font-weight: 600; }
QLabel#Muted { color: @muted@; font-size: 13px; }
QLabel#Caption { color: @faint@; font-size: 12px; }
QLabel#Accent { color: @clay@; font-size: 12px; font-weight: 600; }
QLabel#Chip { color: @muted@; background: @inset@; border: 1px solid @line@; border-radius: 12px; padding: 4px 10px; font-size: 12px; }
QPushButton { background: @paper@; border: 1px solid @line@; border-radius: 7px; padding: 9px 15px; font-size: 13px; font-weight: 500; }
QPushButton:hover { background: @hover@; border-color: @edge@; }
QPushButton:pressed { background: @inset@; }
QPushButton:focus { border-color: @clay@; }
QPushButton:checked { background: @wash@; border-color: @hero_line@; color: @clay@; }
QPushButton:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QPushButton#Primary { background: @primary@; color: @on_primary@; border-color: @primary@; font-weight: 600; }
QPushButton#Primary:hover { background: @primary_hover@; border-color: @primary_hover@; }
QPushButton#Primary:pressed { background: @primary_down@; }
QPushButton#Primary:disabled { background: @wash@; color: @quiet@; border-color: @line@; }
QPushButton#Ghost { background: transparent; border-color: transparent; color: @muted@; }
QPushButton#Ghost:hover, QPushButton#Nav:hover, QPushButton#SectionTab:hover { background: @hover@; color: @ink@; }
QPushButton#Nav, QPushButton#SectionTab, QPushButton#Manage {
    background: transparent; border: 1px solid transparent; padding: 9px 11px; color: @muted@; font-weight: 600;
}
QPushButton#Nav:checked, QPushButton#SectionTab:checked { background: @wash@; color: @clay@; }
QPushButton#Manage:hover { background: @hover@; }
QPushButton#LaunchTile { text-align: left; padding: 15px 13px; background: @paper@; border: 1px solid @line@; font-weight: 600; }
QPushButton#LaunchTile:hover { background: @hover@; border-color: @edge@; }
QPushButton#LaunchTile:disabled { background: @disabled@; color: @quiet@; }
QPushButton#WindowControl, QPushButton#WindowClose, QPushButton#WindowTheme { background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 2px; color: @muted@; }
QPushButton#WindowControl { font-size: 16px; }
QPushButton#WindowClose { font-size: 20px; }
QPushButton#WindowControl:hover, QPushButton#WindowTheme:hover { background: @hover@; color: @ink@; }
QPushButton#WindowTheme:focus, QPushButton#Nav:focus, QPushButton#SectionTab:focus, QPushButton#Manage:focus { border-color: @clay@; }
QPushButton#WindowClose:hover { background: #9C4D40; color: #FFF2EB; }
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox, QDoubleSpinBox { background: @field@; border: 1px solid @line@; border-radius: 7px; padding: 10px 11px; color: @ink@; selection-background-color: @wash@; selection-color: @ink@; }
QPlainTextEdit#LogConsole { background: @inset@; padding: 14px; border-radius: 10px; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: @edge@; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: @clay@; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: @quiet@; border-color: @line@; }
QComboBox { padding-right: 30px; }
QComboBox::drop-down { width: 28px; border: none; }
QComboBox QAbstractItemView { background: @paper@; border: 1px solid @edge@; selection-background-color: @wash@; selection-color: @ink@; padding: 5px; }
QCheckBox { spacing: 9px; color: @muted@; font-size: 13px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid @edge@; border-radius: 4px; background: @field@; }
QCheckBox::indicator:checked { background: #E4AF92; border: 1px solid @hero_line@; image: url("@check_icon@"); }
QCheckBox::indicator:disabled { border-color: @line@; background: @disabled@; }
QProgressBar { background: @rail@; border: none; border-radius: 3px; height: 5px; max-height: 5px; color: transparent; }
QProgressBar::chunk { background: @primary@; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: @thumb@; min-height: 35px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: @thumb_hover@; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QToolTip { color: @ink@; background: @paper@; border: 1px solid @edge@; padding: 5px; }
QMenu { background: @paper@; color: @ink@; border: 1px solid @edge@; padding: 5px; }
QMenu::item { padding: 8px 18px; border-radius: 4px; }
QMenu::item:selected { background: @wash@; }
QMenu::item:disabled { color: @faint@; }
"""
