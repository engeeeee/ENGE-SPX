"""Day (white + scallion green + Claude orange) and Night (pure black + white + blue controls) themes."""
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
        "canvas": "#000000",
        "sidebar": "#000000",
        "titlebar": "#000000",
        "paper": "#0B0B0D",
        "field": "#070708",
        "inset": "#08080A",
        "line": "#1E1E21",
        "edge": "#343439",
        "ink": "#FFFFFF",
        "muted": "#B8B8BE",
        "faint": "#7D7D85",
        "primary": "#1D4B9E",
        "on_primary": "#FFFFFF",
        "primary_hover": "#255BC0",
        "primary_down": "#163B7E",
        "clay": "#FFFFFF",
        "accent": "#FFFFFF",
        "accent_bright": "#2B64CC",
        "hero": "#08080A",
        "hero_end": "#111114",
        "hero_line": "#26262B",
        "wash": "#0F1D3A",
        "nav_line": "#264B8F",
        "sub_wash": "#0C1830",
        "sub_line": "#20407A",
        "select_bg": "#1B1B1F",
        "hover": "#151518",
        "disabled": "#0C0C0E",
        "quiet": "#55555C",
        "rail": "#151518",
        "thumb": "#2A2A2F",
        "thumb_hover": "#3D3D45",
        "check_bg": "#1F54B5",
        "check_line": "#3872DB",
        "status_ready": "#2B6BE0",
        "status_wait": "#FFFFFF",
        "status_idle": "#6E6E76",
        "close_hover": "#9E2A2B",
        "close_ink": "#FFFFFF",
    },
    "light": {
        "canvas": "#FFFFFF",
        "sidebar": "#F5F8F6",
        "titlebar": "#FFFFFF",
        "paper": "#FFFFFF",
        "field": "#FFFFFF",
        "inset": "#F5F8F6",
        "line": "#E1E9E3",
        "edge": "#BACAC0",
        "ink": "#121A15",
        "muted": "#49584F",
        "faint": "#6B7B71",
        "primary": "#D97757",
        "on_primary": "#FFFFFF",
        "primary_hover": "#C86444",
        "primary_down": "#B45536",
        "clay": "#C45D3C",
        "accent": "#237E49",
        "accent_bright": "#329D5E",
        "hero": "#F6FBF7",
        "hero_end": "#E9F6EE",
        "hero_line": "#BEDEC9",
        "wash": "#E9F6EE",
        "nav_line": "#B5DBC2",
        "sub_wash": "#EDF8F1",
        "sub_line": "#C5E3D0",
        "select_bg": "#E9F6EE",
        "hover": "#EFF5F1",
        "disabled": "#F3F6F4",
        "quiet": "#8E9C94",
        "rail": "#E6EFE9",
        "thumb": "#C3D1C8",
        "thumb_hover": "#9CB0A3",
        "check_bg": "#329D5E",
        "check_line": "#257E4A",
        "status_ready": "#2E9E5B",
        "status_wait": "#D97757",
        "status_idle": "#8A9990",
        "close_hover": "#C94A38",
        "close_ink": "#FFFFFF",
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
    "ssh": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m7 9 3 3-3 3m6 0h4"/>',
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
        ("ButtonText", "ink"), ("Highlight", "select_bg"), ("HighlightedText", "ink"),
        ("PlaceholderText", "faint"), ("ToolTipBase", "paper"), ("ToolTipText", "ink"),
    ):
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(colors[token]))
    app.setPalette(palette)
    tokens = {
        **colors,
        "display_font": "SimSun" if os.name == "nt" else "Noto Serif CJK SC",
        "check_icon": (ICONS / "check.svg").as_posix().replace('"', '\\"'),
        "chevron_icon": (ICONS / f"chevron-{theme}.svg").as_posix().replace('"', '\\"'),
    }
    app.setStyleSheet(re.sub(r"@([a-z_]+)@", lambda match: tokens[match[1]], STYLES))
    app.setProperty("spxTheme", theme)


STYLES = """
QWidget { color: @ink@; font-size: 14px; }
QMainWindow, QDialog { background: @canvas@; }
QFrame#Shell { background: @canvas@; border: 1px solid @line@; border-radius: 10px; }
QWidget#TitleBar { background: @titlebar@; border-bottom: 1px solid @line@; }
QFrame#Sidebar { background: @sidebar@; border-right: 1px solid @line@; }
QFrame#SidebarRule { background: @line@; border: none; min-height: 1px; max-height: 1px; }
QFrame#SidebarFooter { background: transparent; border: none; border-top: 1px solid @line@; }
QScrollArea#SidebarScroll, QWidget#SidebarScrollBody { background: transparent; border: none; }
QScrollArea#SidebarScroll QScrollBar:vertical { background: transparent; width: 4px; margin: 2px 0; }
QScrollArea#SidebarScroll QScrollBar::handle:vertical { background: @thumb@; min-height: 24px; border-radius: 2px; }
QFrame#SubNavBranch { background: transparent; border: none; border-left: 1px solid @line@; margin-left: 18px; padding-left: 8px; }
QFrame#SubNavBranch[compact="true"] { border-left: none; margin-left: 0px; padding-left: 0px; }
QFrame#StatusStrip { border-top: 1px solid @line@; background: @titlebar@; }
QFrame#Subnav { border-bottom: 1px solid @line@; }
QWidget#Page, QWidget#Viewport { background: @canvas@; }
QScrollArea { border: none; background: transparent; }
QFrame#Section { background: transparent; border: none; border-top: 1px solid @line@; }
QFrame#Hero {
    background: qlineargradient(x1:0, y1:0, x2:0.95, y2:1, stop:0 @hero@, stop:1 @hero_end@);
    border: 1px solid @hero_line@;
    border-radius: 14px;
}
QFrame#LaunchPanel { background: @paper@; border: 1px solid @line@; border-radius: 12px; }
QFrame#RoutePanel { background: @inset@; border: 1px solid @line@; border-radius: 12px; }
QFrame#Inset { background: @inset@; border: 1px solid @line@; border-radius: 8px; }
QLabel { background: transparent; border: none; }
QLabel#Heading { font-family: "@display_font@"; font-size: 30px; font-weight: 600; }
QLabel#HeroTitle { font-family: "@display_font@"; font-size: 33px; font-weight: 600; }
QLabel#HeroTitle[compact="true"] { font-size: 24px; }
QLabel#ProjectTitle { font-family: "@display_font@"; font-size: 22px; font-weight: 600; }
QLabel#SectionTitle { font-size: 16px; font-weight: 600; }
QLabel#Brand { font-family: "Georgia"; font-size: 16px; font-weight: 700; letter-spacing: 0.4px; }
QLabel#SidebarGroup { color: @faint@; font-size: 11px; font-weight: 600; letter-spacing: 0.6px; }
QLabel#StatusDot { border-radius: 4px; background: @status_idle@; }
QLabel#StatusDot[state="ready"] { background: @status_ready@; }
QLabel#StatusDot[state="waiting"] { background: @status_wait@; }
QLabel#RouteText { font-family: "Consolas"; font-size: 14px; }
QLabel#Metric { font-size: 18px; font-weight: 600; }
QLabel#Muted { color: @muted@; font-size: 13px; }
QLabel#Caption { color: @faint@; font-size: 12px; }
QLabel#Accent { color: @clay@; font-size: 12px; font-weight: 600; }
QLabel#Chip { color: @muted@; background: @inset@; border: 1px solid @line@; border-radius: 12px; padding: 4px 10px; font-size: 12px; }
QPushButton { background: @paper@; border: 1px solid @line@; border-radius: 7px; padding: 8px 14px; font-size: 13px; font-weight: 500; }
QPushButton:hover { background: @hover@; border-color: @edge@; }
QPushButton:pressed { background: @inset@; }
QPushButton:focus { border-color: @accent_bright@; }
QPushButton:checked { background: @wash@; border-color: @nav_line@; color: @accent@; font-weight: 600; }
QPushButton:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QPushButton#Primary { background: @primary@; color: @on_primary@; border-color: @primary@; font-weight: 600; }
QPushButton#Primary:hover { background: @primary_hover@; border-color: @primary_hover@; }
QPushButton#Primary:pressed { background: @primary_down@; }
QPushButton#Primary:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QPushButton#Ghost { background: transparent; border-color: transparent; color: @muted@; }
QPushButton#Ghost:hover { background: @hover@; color: @ink@; }
QPushButton#Nav {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 8px 11px;
    color: @muted@;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#Nav:hover { background: @hover@; color: @ink@; }
QPushButton#Nav:checked { background: @wash@; border-color: @nav_line@; color: @accent@; font-weight: 600; }
QPushButton#Nav[compact="true"] { text-align: center; padding: 9px 4px; }
QPushButton#SubNavItem {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    color: @faint@;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#SubNavItem:hover { background: @hover@; color: @ink@; }
QPushButton#SubNavItem:checked { background: @sub_wash@; border-color: @sub_line@; color: @accent@; font-weight: 600; }
QPushButton#SubNavItem[compact="true"] { text-align: center; padding: 5px 2px; font-size: 11px; }
QPushButton#LaunchTile { text-align: left; padding: 14px 13px; background: @paper@; border: 1px solid @line@; border-radius: 9px; font-weight: 600; }
QPushButton#LaunchTile:hover { background: @hover@; border-color: @nav_line@; }
QPushButton#LaunchTile:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QPushButton#WindowControl, QPushButton#WindowClose { background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 2px; color: @muted@; }
QPushButton#WindowControl { font-size: 15px; }
QPushButton#WindowClose { font-size: 19px; }
QPushButton#WindowControl:hover { background: @hover@; color: @ink@; }
QPushButton#WindowTheme {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 2px;
    color: @muted@;
}
QPushButton#WindowTheme:hover { background: @hover@; color: @ink@; }
QPushButton#WindowTheme:focus, QPushButton#Nav:focus, QPushButton#SubNavItem:focus { border-color: @accent_bright@; }
QPushButton#WindowClose:hover { background: @close_hover@; color: @close_ink@; }
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox, QDoubleSpinBox { background: @field@; border: 1px solid @line@; border-radius: 7px; padding: 9px 11px; color: @ink@; selection-background-color: @select_bg@; selection-color: @ink@; }
QPlainTextEdit#LogConsole { background: @inset@; border: 1px solid @line@; padding: 14px; border-radius: 10px; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: @edge@; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: @accent_bright@; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: @quiet@; border-color: @line@; }
QComboBox { padding-right: 30px; }
QComboBox::drop-down { width: 28px; border: none; subcontrol-origin: padding; subcontrol-position: center right; }
QComboBox::down-arrow { image: url("@chevron_icon@"); width: 14px; height: 14px; }
QComboBox QAbstractItemView { background: @paper@; border: 1px solid @edge@; selection-background-color: @select_bg@; selection-color: @ink@; padding: 5px; }
QListWidget#SSHMachineList { background: @field@; border: 1px solid @line@; border-radius: 8px; padding: 4px; }
QListWidget#SSHMachineList::item { padding: 10px 8px; border-radius: 5px; }
QListWidget#SSHMachineList::item:selected { background: @select_bg@; color: @ink@; }
QTableView#SFTPDirectory { background: @field@; alternate-background-color: @inset@; border: 1px solid @line@; border-radius: 8px; gridline-color: @line@; selection-background-color: @select_bg@; selection-color: @ink@; }
QTableView#SFTPDirectory QHeaderView::section { background: @paper@; color: @muted@; border: none; border-bottom: 1px solid @line@; padding: 8px; }
QCheckBox { spacing: 9px; color: @muted@; font-size: 13px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid @edge@; border-radius: 4px; background: @field@; }
QCheckBox::indicator:checked { background: @check_bg@; border: 1px solid @check_line@; image: url("@check_icon@"); }
QCheckBox::indicator:disabled { border-color: @line@; background: @disabled@; }
QProgressBar { background: @rail@; border: none; border-radius: 3px; height: 5px; max-height: 5px; color: transparent; }
QProgressBar::chunk { background: @accent_bright@; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: @thumb@; min-height: 32px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: @thumb_hover@; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QToolTip { color: @ink@; background: @paper@; border: 1px solid @edge@; padding: 5px; }
QMenu { background: @paper@; color: @ink@; border: 1px solid @edge@; padding: 5px; }
QMenu::item { padding: 8px 18px; border-radius: 4px; }
QMenu::item:selected { background: @select_bg@; }
QMenu::item:disabled { color: @faint@; }
"""
