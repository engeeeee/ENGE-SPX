"""Appearance controls owned by the terminal window."""
from functools import lru_cache
from string import Template

from PySide6.QtCore import QByteArray, QSignalBlocker, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QApplication, QButtonGroup, QColorDialog, QComboBox,
                               QDialog, QFontComboBox, QFormLayout, QFrame,
                               QHBoxLayout, QLabel, QPushButton, QSlider,
                               QSpinBox, QStackedWidget, QStyle,
                               QStyleOptionSlider, QVBoxLayout, QWidget)

from .brand import ICONS
from .terminal_preferences import BADGES, COLOR_FIELDS, COLOR_PRESETS, COLOR_ROLES, MATERIALS
from .window_effects import GLASS_BACKENDS

_GLYPHS = {
    "options": '<circle cx="5" cy="12" r="1.7" fill="{color}" stroke="none"/><circle cx="12" cy="12" r="1.7" fill="{color}" stroke="none"/><circle cx="19" cy="12" r="1.7" fill="{color}" stroke="none"/>',
    "quick_input": '<polyline points="5 16 10 11 5 6"/><line x1="12" y1="17" x2="19" y2="17"/>',
    "files": '<path d="M3 7V5h7l2 2h9v11H3z"/>',
}


@lru_cache(maxsize=64)
def terminal_glyph(name, color, size=16):
    body = _GLYPHS[name].format(color=color)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def _blend(first, second, weight):
    a, b = QColor(first), QColor(second)
    return QColor(*(round(weight * x + (1 - weight) * y) for x, y in zip(a.getRgb()[:3], b.getRgb()[:3]))).name()


def option_icon_color(colors, values):
    return values.get("color_session_foreground") or _blend(colors["session_foreground"], colors["session_background"], 0.78)


_TERMINAL_STYLE = Template("""
QMainWindow#SmartTerminal { background: $frame; }
QFrame#TerminalShell { background: $frame; border: 1px solid $frame_border; color: $foreground; }
QWidget#TitleBar { background: $title_background; border-bottom: 1px solid $divider; }
QWidget#TitleBar QLabel#Caption { color: $title_foreground; font-size: 12px; font-weight: 500; letter-spacing: 0.2px; }
QPushButton#WindowControl, QPushButton#WindowClose { background: transparent; border: none; border-radius: 5px; color: $title_foreground; padding: 0; }
QPushButton#WindowControl { font-size: 15px; }
QPushButton#WindowClose { font-size: 19px; }
QPushButton#WindowControl:hover { color: $title_hover_text; background: $title_hover; }
QPushButton#WindowClose:hover { color: #ffffff; background: $close_hover; }
QFrame#SessionBar { background: $session_background; border-bottom: 1px solid $divider; }
QLabel#ToolBadge { color: $badge_foreground; background: $badge_background; border: 1px solid $badge_border; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; }
QLabel#ProjectName { color: $session_foreground; font-size: 12px; font-weight: 500; }
QLabel#ConnectionState { color: $connection_foreground; background: $connection_bg; border: 1px solid $connection_border; border-radius: 10px; padding: 4px 10px; font-size: 11px; font-weight: 600; }
QLabel#ConnectionState[state="waiting"] { color: $option_text; background: $waiting_bg; border: 1px solid $divider; font-weight: 500; }
QLabel#ConnectionState[state="ended"] { color: $footer_foreground; background: transparent; border: 1px solid $divider; font-weight: 500; }
QToolButton#TerminalOptions { color: $option_text; background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 0; }
QToolButton#TerminalOptions:hover { color: $option_hover_text; background: $session_hover; border-color: $divider; }
QToolButton#QuickInputButton, QToolButton#FileBrowserButton { color: $option_text; background: $control_bg; border: 1px solid $divider; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 500; }
QToolButton#QuickInputButton:hover, QToolButton#FileBrowserButton:hover { color: $option_hover_text; background: $control_hover_bg; border-color: $control_hover_border; }
QToolButton#QuickInputButton:disabled, QToolButton#FileBrowserButton:disabled { color: $footer_foreground; background: transparent; border-color: transparent; }
QFrame#TerminalFooter { background: $footer_background; border-top: 1px solid $divider; }
QLabel#TerminalMessage { color: $footer_foreground; font-size: 11px; }
QLabel#FontSize { color: $font_size_text; font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 11px; }
QMenu#TerminalMenu { color: $menu_foreground; background: $menu_background; border: 1px solid $menu_border; border-radius: 8px; padding: 5px; }
QMenu#TerminalMenu::item { padding: 7px 16px; border-radius: 5px; }
QMenu#TerminalMenu::item:selected { background: $menu_selection_background; color: $menu_selection_foreground; }
QMenu#TerminalMenu::item:disabled { color: $menu_disabled; }
QMenu#TerminalMenu::separator { height: 1px; background: $menu_separator; margin: 5px 8px; }
QScrollBar:vertical { background: $scrollbar_track; width: 8px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: $scrollbar_thumb; min-height: 36px; border-radius: 3px; margin: 2px 1px; }
QScrollBar::handle:vertical:hover { background: $scrollbar_hover; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
""")


def terminal_stylesheet(colors, values, alpha, glass):
    def tinted(value):
        color = QColor(value)
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"

    def hover(value):
        color = QColor(value)
        if color.lightness() > 140:
            return color.darker(108).name()
        if color.lightness() < 24:
            return "#17171b"
        return color.lighter(135).name()

    is_light = QColor(colors["background"]).lightness() > 140
    border = values.get("color_border")
    theme = dict(colors)
    if border:
        badge_border = border
    elif values.get("color_badge_background") or values.get("color_badge_foreground"):
        badge_border = _blend(colors["badge_foreground"], colors["badge_background"], 0.34)
    else:
        badge_border = BADGES[values["tint"]][2]
    theme.update(
        frame="transparent" if glass else colors["background"],
        frame_border=border or (("rgba(18, 26, 21, 46)" if is_light else "rgba(255, 255, 255, 42)")
                                if glass else ("#cdd9d1" if is_light else _blend("#ffffff", colors["background"], 0.16))),
        divider=border or (("rgba(18, 26, 21, 30)" if is_light else "rgba(255, 255, 255, 24)") if glass else colors["border"]),
        title_hover=hover(colors["title_background"]),
        title_hover_text=values.get("color_title_foreground") or ("#121a15" if is_light else "#ffffff"),
        close_hover="#c94a38" if is_light else "#9e2a2b",
        session_hover=hover(colors["session_background"]),
        option_text=option_icon_color(colors, values),
        option_hover_text=values.get("color_session_foreground") or ("#121a15" if is_light else "#ffffff"),
        control_bg=_blend(colors["foreground"], colors["session_background"], 0.04 if is_light else 0.055),
        control_hover_bg=_blend(colors["cursor"], colors["session_background"], 0.15),
        control_hover_border=_blend(colors["cursor"], colors["border"], 0.55),
        badge_border=badge_border,
        connection_bg=_blend(colors["connection_foreground"], colors["session_background"], 0.12),
        connection_border=_blend(colors["connection_foreground"], colors["session_background"], 0.30),
        waiting_bg=_blend(colors["foreground"], colors["session_background"], 0.05),
        font_size_text=values.get("color_footer_foreground") or _blend(colors["footer_foreground"], colors["footer_background"], 0.88),
        menu_border=border or _blend("#000000" if is_light else "#ffffff", colors["menu_background"], 0.18),
        menu_separator=border or _blend(colors["menu_foreground"], colors["menu_background"], 0.12),
        menu_disabled=_blend(colors["menu_foreground"], colors["menu_background"], 0.44),
        scrollbar_track="transparent" if glass and not values.get("color_scrollbar_track") else colors["scrollbar_track"],
        scrollbar_hover=hover(colors["scrollbar_thumb"]),
    )
    for role in ("title_background", "session_background", "footer_background"):
        theme[role] = tinted(colors[role])
    return _TERMINAL_STYLE.substitute(theme)


class OpacitySlider(QSlider):
    def __init__(self, parent):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(30, 100)
        self.setMinimumWidth(180)
        self.setMinimumHeight(32)
        self.setTracking(False)
        self.drag_offset = 0

    def geometry_for(self, control, option):
        return self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, control, self)

    def seek(self, x):
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        groove = self.geometry_for(QStyle.SubControl.SC_SliderGroove, option)
        handle = self.geometry_for(QStyle.SubControl.SC_SliderHandle, option)
        position = x - self.drag_offset - groove.x() - handle.width() // 2
        span = max(1, groove.width() - handle.width())
        self.setSliderPosition(QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), position, span, option.upsideDown))

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        handle = self.geometry_for(QStyle.SubControl.SC_SliderHandle, option)
        x = round(event.position().x())
        center = handle.x() + handle.width() // 2
        self.drag_offset = x - center if handle.contains(event.position().toPoint()) else 0
        self.setSliderDown(True)
        self.seek(x)
        event.accept()

    def mouseMoveEvent(self, event):
        if not self.isSliderDown():
            return super().mouseMoveEvent(event)
        self.seek(round(event.position().x()))
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.isSliderDown():
            return super().mouseReleaseEvent(event)
        self.seek(round(event.position().x()))
        self.setSliderDown(False)
        event.accept()


def _appearance_stylesheet(theme_name):
    import re
    from .ui.style import THEMES

    colors = THEMES[theme_name if theme_name in THEMES else "dark"]
    tokens = {
        **colors,
        "chevron_icon": (ICONS / f"chevron-{'light' if theme_name == 'light' else 'dark'}.svg").as_posix().replace('"', '\\"'),
        "chevron_up_icon": (ICONS / f"chevron-up-{'light' if theme_name == 'light' else 'dark'}.svg").as_posix().replace('"', '\\"'),
    }
    return re.sub(r"@([a-z_]+)@", lambda match: tokens[match[1]], """
QDialog#AppearanceDialog { background: transparent; }
QFrame#AppearanceShell { background: @canvas@; border: 1px solid @edge@; border-radius: 10px; color: @ink@; }
QWidget#TitleBar { background: @titlebar@; border-bottom: 1px solid @line@; }
QWidget#TitleBar QLabel#Caption { color: @muted@; font-size: 12px; font-weight: 500; }
QPushButton#WindowControl, QPushButton#WindowClose { background: transparent; border: none; border-radius: 5px; color: @muted@; padding: 0; font-size: 18px; }
QPushButton#WindowClose:hover { background: @close_hover@; color: @close_ink@; }
QFrame#SegTrack { background: @inset@; border: 1px solid @line@; border-radius: 8px; }
QPushButton#SegTab { background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 6px 14px; font-size: 13px; font-weight: 500; color: @muted@; }
QPushButton#SegTab:hover { background: @hover@; color: @ink@; }
QPushButton#SegTab:checked { background: @wash@; border-color: @nav_line@; color: @accent@; font-weight: 600; }
QFrame#SectionCard { background: @inset@; border: 1px solid @line@; border-radius: 10px; }
QLabel#CardTitle { color: @faint@; font-size: 11px; font-weight: 600; letter-spacing: 0.4px; }
QLabel#FieldLabel { color: @muted@; font-size: 13px; background: transparent; border: none; }
QLabel#Muted { color: @faint@; font-size: 12px; background: transparent; border: none; }
QComboBox, QFontComboBox, QSpinBox { background: @field@; border: 1px solid @line@; border-radius: 7px; padding: 7px 10px; color: @ink@; font-size: 13px; }
QComboBox, QFontComboBox { padding-right: 28px; }
QSpinBox { padding-right: 24px; }
QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; width: 22px; border: none; border-left: 1px solid @line@; background: transparent; }
QSpinBox::up-button { subcontrol-position: top right; border-top-right-radius: 7px; }
QSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 7px; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: @hover@; }
QSpinBox::up-arrow { image: url("@chevron_up_icon@"); width: 10px; height: 10px; }
QSpinBox::down-arrow { image: url("@chevron_icon@"); width: 10px; height: 10px; }
QComboBox::drop-down, QFontComboBox::drop-down { width: 26px; border: none; subcontrol-origin: padding; subcontrol-position: center right; }
QComboBox::down-arrow, QFontComboBox::down-arrow { image: url("@chevron_icon@"); width: 14px; height: 14px; }
QComboBox QAbstractItemView, QFontComboBox QAbstractItemView { background: @paper@; color: @ink@; border: 1px solid @edge@; selection-background-color: @select_bg@; selection-color: @ink@; padding: 4px; }
QComboBox:hover, QFontComboBox:hover, QSpinBox:hover { border-color: @edge@; }
QComboBox:focus, QFontComboBox:focus, QSpinBox:focus { border-color: @accent_bright@; }
QComboBox:disabled, QFontComboBox:disabled, QSpinBox:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QSlider::groove:horizontal { background: @rail@; height: 6px; border-radius: 3px; }
QSlider::sub-page:horizontal { background: @accent_bright@; height: 6px; border-radius: 3px; }
QSlider::sub-page:horizontal:disabled { background: @thumb@; height: 6px; border-radius: 3px; }
QSlider::add-page:horizontal { background: @rail@; height: 6px; border-radius: 3px; }
QSlider::handle:horizontal { background: @canvas@; border: 2px solid @accent_bright@; width: 12px; height: 12px; margin: -5px 0; border-radius: 8px; }
QSlider::handle:horizontal:disabled { background: @inset@; border: 2px solid @thumb@; width: 12px; height: 12px; margin: -5px 0; border-radius: 8px; }
QPushButton#ActionSecondary { background: @paper@; border: 1px solid @line@; border-radius: 7px; padding: 7px 14px; font-size: 13px; font-weight: 500; color: @ink@; }
QPushButton#ActionSecondary:hover { background: @hover@; border-color: @edge@; }
QPushButton#ActionSecondary:disabled { background: @disabled@; color: @quiet@; border-color: @line@; }
QPushButton#Primary { background: @primary@; border: 1px solid @primary@; border-radius: 7px; padding: 7px 18px; font-size: 13px; font-weight: 600; color: @on_primary@; }
QPushButton#Primary:hover { background: @primary_hover@; border-color: @primary_hover@; }
QLabel#PreviewChip { border: 1px solid @edge@; border-radius: 5px; }
""")


def _card(title):
    frame = QFrame()
    frame.setObjectName("SectionCard")
    box = QVBoxLayout(frame)
    box.setContentsMargins(16, 13, 16, 14)
    box.setSpacing(10)
    heading = QLabel(title)
    heading.setObjectName("CardTitle")
    box.addWidget(heading)
    form = QFormLayout()
    form.setContentsMargins(0, 0, 0, 0)
    form.setHorizontalSpacing(14)
    form.setVerticalSpacing(10)
    box.addLayout(form)
    return frame, box, form


def _row_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("FieldLabel")
    return lbl


class AppearanceDialog(QDialog):
    def __init__(self, terminal):
        super().__init__(terminal, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        from .ui.widgets import TitleBar

        self.terminal = terminal
        self.setObjectName("AppearanceDialog")
        self.setWindowTitle("终端外观")
        self.setMinimumWidth(420)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        shell = QFrame(self)
        shell.setObjectName("AppearanceShell")
        outer.addWidget(shell)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        self.titlebar = TitleBar(self, "终端外观", dialog=True)
        self.titlebar.setFixedHeight(38)
        self.titlebar.layout().setContentsMargins(16, 0, 6, 0)
        layout.addWidget(self.titlebar)

        body = QVBoxLayout()
        body.setContentsMargins(20, 16, 20, 18)
        body.setSpacing(14)
        layout.addLayout(body)

        seg_track = QFrame(self)
        seg_track.setObjectName("SegTrack")
        seg_row = QHBoxLayout(seg_track)
        seg_row.setContentsMargins(3, 3, 3, 3)
        seg_row.setSpacing(4)
        self._tabs = QButtonGroup(self)
        self._tabs.setExclusive(True)
        self._pages = QStackedWidget(self)
        display_btn = QPushButton("字体与背景", seg_track)
        color_btn = QPushButton("配色", seg_track)
        for idx, btn in enumerate((display_btn, color_btn)):
            btn.setObjectName("SegTab")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._tabs.addButton(btn, idx)
            seg_row.addWidget(btn, 1)
        display_btn.setChecked(True)
        self._tabs.idClicked.connect(self._pages.setCurrentIndex)
        body.addWidget(seg_track)
        body.addWidget(self._pages)

        display = QWidget()
        display_layout = QVBoxLayout(display)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(12)

        bg_card, bg_box, bg_form = _card("窗口背景")
        self.material = QComboBox(self)
        for key, label in MATERIALS.items():
            self.material.addItem(label, key)
        bg_form.addRow(_row_label("背景效果"), self.material)
        self.tint = QComboBox(self)
        self.tint.setToolTip("在配色页恢复终端背景后，可切换预设色调。")
        for key, label in (("clay", "纯黑"), ("purple", "紫晶"), ("graphite", "石墨")):
            self.tint.addItem(label, key)
        bg_form.addRow(_row_label("背景配色"), self.tint)

        self.opacity = OpacitySlider(self)
        self.percent = QSpinBox(self)
        self.percent.setRange(self.opacity.minimum(), self.opacity.maximum())
        self.percent.setSuffix("%")
        self.percent.setKeyboardTracking(False)
        self.percent.setAccessibleName("背景不透明度百分比")
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.opacity, 1)
        row.addWidget(self.percent)
        bg_form.addRow(_row_label("不透明度"), row)
        self.status = QLabel(self)
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        bg_box.addWidget(self.status)
        display_layout.addWidget(bg_card)

        type_card, _, type_form = _card("字体与排版")
        self.fonts = QFontComboBox(self)
        self.fonts.setEditable(False)
        self.fonts.setFontFilters(QFontComboBox.FontFilter.MonospacedFonts)
        type_form.addRow(_row_label("等宽字体"), self.fonts)
        self.font_size = QSpinBox(self)
        self.font_size.setRange(8, 24)
        self.font_size.setSuffix(" pt")
        type_form.addRow(_row_label("字体大小"), self.font_size)
        display_layout.addWidget(type_card)
        display_layout.addStretch()

        self._pages.addWidget(display)
        self._pages.addWidget(ColorPage(terminal))

        footer = QHBoxLayout()
        note = QLabel("修改即时生效并自动保存")
        note.setObjectName("Muted")
        footer.addWidget(note)
        footer.addStretch()
        done = QPushButton("关闭", self)
        done.setObjectName("Primary")
        done.setCursor(Qt.CursorShape.PointingHandCursor)
        done.clicked.connect(self.close)
        footer.addWidget(done)
        body.addLayout(footer)

        prefs = terminal.preferences
        self.material.currentIndexChanged.connect(lambda _: prefs.set("appearance", self.material.currentData()))
        self.tint.currentIndexChanged.connect(lambda _: prefs.set("tint", self.tint.currentData()))
        self.fonts.currentFontChanged.connect(lambda font: prefs.set("font_family", font.family()))
        self.font_size.valueChanged.connect(lambda value: prefs.set("font_size", value))
        self.opacity.sliderMoved.connect(self.show_percent)
        self.opacity.valueChanged.connect(lambda value: prefs.set("opacity", value))
        self.percent.valueChanged.connect(self.opacity.setValue)
        prefs.changed.connect(self.sync)
        self.apply_chrome()
        self.sync(prefs.value)

    def apply_chrome(self):
        app = QApplication.instance()
        theme = (app.property("spxTheme") if app else None) or "dark"
        self.setStyleSheet(_appearance_stylesheet(theme))

    def showEvent(self, event):
        self.apply_chrome()
        super().showEvent(event)

    def show_percent(self, value):
        with QSignalBlocker(self.percent):
            self.percent.setValue(value)

    def sync(self, values):
        with QSignalBlocker(self.material), QSignalBlocker(self.tint), QSignalBlocker(self.fonts):
            self.material.setCurrentIndex(self.material.findData(values["appearance"]))
            self.tint.setCurrentIndex(self.tint.findData(values["tint"]))
            self.fonts.setCurrentFont(self.terminal.view.font)
        self.tint.setEnabled(values.get("color_background") is None)
        with QSignalBlocker(self.opacity):
            self.opacity.setValue(values["opacity"])
        with QSignalBlocker(self.font_size):
            self.font_size.setValue(values["font_size"])
        self.show_percent(values["opacity"])
        backend = self.terminal.backdrop_backend
        available = backend in GLASS_BACKENDS
        self.opacity.setEnabled(available)
        self.percent.setEnabled(available)
        if values["appearance"] == "solid":
            hint = "选择透明背景后可调整不透明度。"
        elif not available:
            hint = "当前系统透明效果不可用。"
        elif backend.endswith("-tint"):
            hint = "当前系统使用对应的云母色调。"
        else:
            hint = ""
        self.status.setText(hint)
        self.status.setVisible(bool(hint))


class ColorPage(QWidget):
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal
        self.prefs = terminal.preferences
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        preset_card, preset_box, preset_form = _card("配色方案")
        self.preset = QComboBox()
        self.preset.addItems([*COLOR_PRESETS, "自定义"])
        preset_form.addRow(_row_label("预设"), self.preset)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(8)
        self._chips = {}
        for role, title in (("background", "背景"), ("foreground", "文字"), ("cursor", "光标"), ("selection_background", "选区")):
            item = QHBoxLayout()
            item.setSpacing(5)
            chip = QLabel()
            chip.setObjectName("PreviewChip")
            chip.setFixedSize(16, 16)
            cap = QLabel(title)
            cap.setObjectName("Muted")
            item.addWidget(chip)
            item.addWidget(cap)
            preview_row.addLayout(item)
            self._chips[role] = chip
        preview_row.addStretch()
        preset_box.addLayout(preview_row)
        root.addWidget(preset_card)

        detail_card, _, form = _card("元素微调")
        self.role = QComboBox()
        for key, (name, _) in COLOR_ROLES.items():
            self.role.addItem(name, key)
        form.addRow(_row_label("界面元素"), self.role)
        self.swatch = QPushButton()
        self.swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.swatch.clicked.connect(self.choose)
        self.reset = QPushButton("恢复该项")
        self.reset.setObjectName("ActionSecondary")
        self.reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset.clicked.connect(lambda: self.prefs.set(COLOR_FIELDS[self.role.currentData()], None))
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.swatch, 1)
        row.addWidget(self.reset)
        form.addRow(_row_label("颜色"), row)
        root.addWidget(detail_card)
        root.addStretch()

        self.preset.currentTextChanged.connect(self.select_preset)
        self.role.currentIndexChanged.connect(self.sync_color)
        self.prefs.changed.connect(self.sync)
        self.sync(self.prefs.value)

    def select_preset(self, name):
        if name in COLOR_PRESETS:
            selected = COLOR_PRESETS[name]
            self.prefs.update({field: selected.get(role) for role, field in COLOR_FIELDS.items()})

    def choose(self):
        role = self.role.currentData()
        initial = QColor(self.terminal.view.display_colors[role])
        color = QColorDialog.getColor(initial, self, "选择" + self.role.currentText())
        if color.isValid():
            self.prefs.set(COLOR_FIELDS[role], color.name())

    def sync_color(self):
        colors = self.terminal.view.display_colors
        for role, chip in self._chips.items():
            chip.setStyleSheet(f"background: {colors[role]};")
        role = self.role.currentData()
        color = QColor(colors[role])
        self.swatch.setText(f"{color.name().upper()}  ·  编辑")
        ink = "#111111" if color.lightness() > 128 else "#ffffff"
        border = "rgba(0, 0, 0, 0.25)" if color.lightness() > 128 else "rgba(255, 255, 255, 0.22)"
        self.swatch.setStyleSheet(
            f"QPushButton {{ background: {color.name()}; color: {ink}; border: 1px solid {border}; "
            f"border-radius: 7px; padding: 7px 12px; font-family: 'Consolas', monospace; font-size: 12px; font-weight: 600; }}"
        )
        self.reset.setEnabled(self.prefs.value[COLOR_FIELDS[role]] is not None)

    def sync(self, values):
        custom = {role: values[field] for role, field in COLOR_FIELDS.items() if values[field] is not None}
        name = next((name for name, preset in COLOR_PRESETS.items() if preset == custom), "自定义")
        with QSignalBlocker(self.preset):
            self.preset.setCurrentText(name)
        self.sync_color()
