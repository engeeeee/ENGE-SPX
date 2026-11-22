"""Appearance controls owned by the terminal window."""
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFontComboBox,
                               QFormLayout, QHBoxLayout, QLabel, QSlider, QSpinBox,
                               QStyle, QStyleOptionSlider)

from .terminal_preferences import MATERIALS
from .window_effects import GLASS_BACKENDS


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
        form = QFormLayout(self)

        self.material = QComboBox(self)
        for key, label in MATERIALS.items():
            self.material.addItem(label, key)
        form.addRow("背景效果", self.material)
        self.tint = QComboBox(self)
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
        done = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        done.button(QDialogButtonBox.StandardButton.Close).setText("关闭")
        done.rejected.connect(self.close)
        form.addRow(done)

        prefs = terminal.preferences
        self.material.currentIndexChanged.connect(lambda _: prefs.set("appearance", self.material.currentData()))
        self.tint.currentIndexChanged.connect(lambda _: prefs.set("tint", self.tint.currentData()))
        self.fonts.currentFontChanged.connect(lambda font: prefs.set("font_family", font.family()))
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
        with QSignalBlocker(self.opacity):
            self.opacity.setValue(values["opacity"])
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
