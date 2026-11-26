"""Appearance controls owned by the terminal window."""
from string import Template

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QColorDialog, QComboBox, QDialog, QDialogButtonBox,
                               QFontComboBox, QFormLayout, QHBoxLayout, QLabel,
                               QPushButton, QSlider, QSpinBox, QStyle,
                               QStyleOptionSlider, QTabWidget, QVBoxLayout, QWidget)

from .terminal_preferences import BADGES, COLOR_FIELDS, COLOR_PRESETS, COLOR_ROLES, MATERIALS
from .window_effects import GLASS_BACKENDS

_TERMINAL_STYLE = Template("""
QMainWindow#SmartTerminal { background: $frame; }
QFrame#TerminalShell { background: $frame; border: 1px solid $frame_border; color: $foreground; }
QWidget#TitleBar { background: $title_background; border-bottom: 1px solid $divider; }
QWidget#TitleBar QLabel#Caption { color: $title_foreground; font-size: 12px; }
QPushButton#WindowControl, QPushButton#WindowClose { background: transparent; border: none; border-radius: 4px; color: $title_foreground; font-size: 16px; padding: 0; }
QPushButton#WindowControl:hover { color: $title_hover_text; background: $title_hover; }
QPushButton#WindowClose:hover { color: #fff0e5; background: #8b423b; }
QFrame#SessionBar { background: $session_background; border-bottom: 1px solid $divider; }
QLabel#ToolBadge { color: $badge_foreground; background: $badge_background; border: 1px solid $badge_border; border-radius: 5px; padding: 4px 10px; font-size: 12px; font-weight: 600; }
QLabel#ProjectName { color: $session_foreground; font-size: 12px; }
QLabel#ConnectionState { color: $connection_foreground; font-size: 11px; }
QToolButton#TerminalOptions { color: $option_text; background: transparent; border: none; border-radius: 5px; font-size: 22px; }
QToolButton#TerminalOptions:hover { color: $option_hover_text; background: $session_hover; }
QToolButton#QuickInputButton, QToolButton#FileBrowserButton { color: $option_text; background: transparent; border: 1px solid $divider; border-radius: 5px; padding: 4px 9px; font-size: 12px; }
QToolButton#QuickInputButton:hover, QToolButton#FileBrowserButton:hover { color: $option_hover_text; background: $session_hover; }
QToolButton#QuickInputButton:disabled, QToolButton#FileBrowserButton:disabled { color: $footer_foreground; border-color: transparent; }
QFrame#TerminalFooter { background: $footer_background; border-top: 1px solid $divider; }
QLabel#TerminalMessage { color: $footer_foreground; font-size: 11px; }
QLabel#FontSize { color: $font_size_text; font-size: 11px; }
QMenu#TerminalMenu { color: $menu_foreground; background: $menu_background; border: 1px solid $menu_border; border-radius: 7px; padding: 5px; }
QMenu#TerminalMenu::item { padding: 7px 18px; border-radius: 4px; }
QMenu#TerminalMenu::item:selected { background: $menu_selection_background; color: $menu_selection_foreground; }
QMenu#TerminalMenu::item:disabled { color: $menu_disabled; }
QMenu#TerminalMenu::separator { height: 1px; background: $menu_separator; margin: 5px 9px; }
QScrollBar:vertical { background: $scrollbar_track; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: $scrollbar_thumb; min-height: 36px; border-radius: 4px; margin: 1px; }
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
        return (color.darker(115) if color.lightness() > 128 else color.lighter(145)).name()

    theme = dict(colors)
    border = values.get("color_border")
    session_text = values.get("color_session_foreground")
    menu_text = QColor(colors["menu_foreground"])
    menu_base = QColor(colors["menu_background"])
    muted_menu = QColor(*(round(.55 * x + .45 * y) for x, y in zip(menu_text.getRgb()[:3], menu_base.getRgb()[:3]))).name()
    theme.update(
        frame="transparent" if glass else colors["background"],
        frame_border=border or ("rgba(232, 227, 220, 45)" if glass else colors["border"]),
        divider=border or ("rgba(232, 227, 220, 24)" if glass else "#39352f"),
        title_hover=hover(values.get("color_title_background") or colors["background"]),
        title_hover_text=values.get("color_title_foreground") or "#eee7dc",
        session_hover=hover(values.get("color_session_background") or colors["background"]),
        option_text=session_text or "#aaa296",
        option_hover_text=session_text or "#f0d2bc",
        badge_border=border or BADGES[values["tint"]][2],
        font_size_text=values.get("color_footer_foreground") or "#8e847a",
        menu_border=border or "#54483c",
        menu_separator=border or "#423a31",
        menu_disabled=muted_menu if values.get("color_menu_foreground") else "#71685e",
        scrollbar_track="transparent" if glass and not values.get("color_scrollbar_track") else colors["scrollbar_track"],
        scrollbar_hover=hover(colors["scrollbar_thumb"]) if values.get("color_scrollbar_thumb") else "#7e604b",
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


class AppearanceDialog(QDialog):
    def __init__(self, terminal):
        super().__init__(terminal, Qt.WindowType.Tool)
        self.terminal = terminal
        self.setWindowTitle("终端外观")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        display = QWidget()
        form = QFormLayout(display)
        tabs.addTab(display, "字体与背景")
        tabs.addTab(ColorPage(terminal), "配色")

        self.material = QComboBox(self)
        for key, label in MATERIALS.items():
            self.material.addItem(label, key)
        form.addRow("背景效果", self.material)
        self.tint = QComboBox(self)
        self.tint.setToolTip("在配色页恢复终端背景后，可切换预设色调。")
        for key, label in (("clay", "暖灰"), ("purple", "紫晶"), ("graphite", "石墨")):
            self.tint.addItem(label, key)
        form.addRow("背景配色", self.tint)

        self.opacity = OpacitySlider(self)
        self.percent = QSpinBox(self)
        self.percent.setRange(self.opacity.minimum(), self.opacity.maximum())
        self.percent.setSuffix("%")
        self.percent.setKeyboardTracking(False)
        self.percent.setAccessibleName("背景不透明度百分比")
        row = QHBoxLayout()
        row.addWidget(self.opacity, 1)
        row.addWidget(self.percent)
        form.addRow("背景不透明度", row)
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        form.addRow(self.status)

        self.fonts = QFontComboBox(self)
        self.fonts.setEditable(False)
        self.fonts.setFontFilters(QFontComboBox.FontFilter.MonospacedFonts)
        form.addRow("字体", self.fonts)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setSuffix(" pt")
        form.addRow("字号", self.font_size)
        done = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        done.button(QDialogButtonBox.StandardButton.Close).setText("关闭")
        done.rejected.connect(self.close)
        layout.addWidget(done)

        prefs = terminal.preferences
        self.material.currentIndexChanged.connect(lambda _: prefs.set("appearance", self.material.currentData()))
        self.tint.currentIndexChanged.connect(lambda _: prefs.set("tint", self.tint.currentData()))
        self.fonts.currentFontChanged.connect(lambda font: prefs.set("font_family", font.family()))
        self.font_size.valueChanged.connect(lambda value: prefs.set("font_size", value))
        self.opacity.sliderMoved.connect(self.show_percent)
        self.opacity.valueChanged.connect(lambda value: prefs.set("opacity", value))
        self.percent.valueChanged.connect(self.opacity.setValue)
        prefs.changed.connect(self.sync)
        self.sync(prefs.value)

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
            hint = "选择透明背景后可调整。"
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
        form = QFormLayout(self)
        self.preset = QComboBox()
        self.preset.addItems([*COLOR_PRESETS, "自定义"])
        form.addRow("预设", self.preset)
        self.role = QComboBox()
        for key, (name, _) in COLOR_ROLES.items():
            self.role.addItem(name, key)
        form.addRow("界面元素", self.role)
        self.swatch = QPushButton()
        self.swatch.clicked.connect(self.choose)
        self.reset = QPushButton("恢复该项")
        self.reset.clicked.connect(lambda: self.prefs.set(COLOR_FIELDS[self.role.currentData()], None))
        row = QHBoxLayout()
        row.addWidget(self.swatch, 1)
        row.addWidget(self.reset)
        form.addRow("颜色", row)
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
        role = self.role.currentData()
        color = QColor(self.terminal.view.display_colors[role])
        self.swatch.setText(color.name().upper())
        ink = "#111111" if color.lightness() > 128 else "#ffffff"
        self.swatch.setStyleSheet(f"background: {color.name()}; color: {ink};")
        self.reset.setEnabled(self.prefs.value[COLOR_FIELDS[role]] is not None)

    def sync(self, values):
        custom = {role: values[field] for role, field in COLOR_FIELDS.items() if values[field] is not None}
        name = next((name for name, preset in COLOR_PRESETS.items() if preset == custom), "自定义")
        with QSignalBlocker(self.preset):
            self.preset.setCurrentText(name)
        self.sync_color()
