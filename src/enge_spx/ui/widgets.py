"""Small native widgets shared by pages and modal dialogs."""
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QBoxLayout,
                             QPushButton, QLineEdit, QComboBox, QCheckBox,
                             QProgressBar, QScrollArea, QDialog, QDialogButtonBox,
                             QDoubleSpinBox, QSpinBox, QAbstractSpinBox, QSizePolicy)


def label(text="", kind="", wrap=False):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if wrap:
        # A path or other unbroken value should wrap within the viewport.
        # Preserve the label's height-for-width flag when dropping its width hint.
        policy = widget.sizePolicy()
        policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
        widget.setSizePolicy(policy)
    if kind:
        widget.setObjectName(kind)
    return widget


def bind_text(widget, value):
    widget.setText(str(value.get()))
    value.changed.connect(lambda text: widget.setText(str(text)))
    return widget


def button(text, action, primary=False, ghost=False):
    widget = QPushButton(text)
    widget.setAutoDefault(False)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary or ghost:
        widget.setObjectName("Primary" if primary else "Ghost")
    widget.clicked.connect(lambda unused=False: action())
    return widget


def entry(value, placeholder="", secret=False):
    widget = QLineEdit()
    widget.setPlaceholderText(placeholder)
    if secret:
        widget.setEchoMode(QLineEdit.EchoMode.Password)
    widget.setText(str(value.get()))
    widget.textEdited.connect(value.set)
    value.changed.connect(lambda text: widget.setText(str(text)) if widget.text() != str(text) else None)
    return widget


class Combo(QComboBox):
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


def combo(value, options):
    widget = Combo()
    for text, data in options:
        widget.addItem(text, data)
    def selected(data):
        index = widget.findData(data)
        if widget.currentIndex() != index:
            widget.setCurrentIndex(index)
    selected(value.get())
    widget.currentIndexChanged.connect(lambda index: value.set(widget.itemData(index)) if index >= 0 else None)
    value.changed.connect(selected)
    return widget


def check(text, value, action=None):
    widget = QCheckBox(text)
    widget.setChecked(bool(value.get()))
    widget.toggled.connect(value.set)
    if action:
        widget.clicked.connect(lambda unused: action())
    value.changed.connect(lambda state: widget.setChecked(bool(state)) if widget.isChecked() != bool(state) else None)
    return widget


def budget_number(value, cpu=False, minimum=0):
    widget = QDoubleSpinBox() if cpu else QSpinBox()
    widget.setRange(0 if cpu else minimum, 128 if cpu else 131072)
    widget.setSingleStep(.25 if cpu else 128)
    if cpu:
        widget.setDecimals(2)
    if cpu or minimum == 0:
        widget.setSpecialValueText("不限")
    widget.setSuffix(" 核" if cpu else " MiB")
    widget.setKeyboardTracking(False)
    widget.setMinimumWidth(105)
    widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
    widget.setValue(value.get())
    widget.valueChanged.connect(value.set)
    def update(number):
        if widget.value() != number:
            widget.blockSignals(True)
            widget.setValue(number)
            widget.blockSignals(False)
    value.changed.connect(update)
    return widget


def progress(value):
    widget = QProgressBar()
    widget.setTextVisible(False)
    def update(amount):
        limits = (0, 0) if amount < 0 else (0, 1000)
        if (widget.minimum(), widget.maximum()) != limits:
            widget.setRange(*limits)
        if amount >= 0:
            widget.setValue(round(amount * 10))
    value.changed.connect(update)
    update(value.get())
    return widget


class Panel(QFrame):
    def __init__(self, title=None, caption=None, surface="Section"):
        super().__init__()
        self.setObjectName(surface)
        self.layout = QVBoxLayout(self)
        if surface == "Section":
            self.layout.setContentsMargins(0, 16, 0, 4)
        else:
            self.layout.setContentsMargins(22, 20, 22, 20)
        self.layout.setSpacing(12)
        if title:
            self.layout.addWidget(label(title, "SectionTitle"))
        if caption:
            self.layout.addWidget(label(caption, "Muted", True))

    def row(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)
        self.layout.addLayout(layout)
        return layout

    def field(self, title, widget, hint=None):
        title_label = label(title, "Muted")
        title_label.setBuddy(widget)
        widget.setAccessibleName(title)
        self.layout.addWidget(title_label)
        self.layout.addWidget(widget)
        if hint:
            self.layout.addWidget(label(hint, "Caption", True))
        return widget


class Page(QScrollArea):
    resized = Signal(int, int)
    def __init__(self, title=None, subtitle=None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setObjectName("Viewport")
        self.verticalScrollBar().setSingleStep(24)
        self.content = QWidget()
        self.content.setObjectName("Page")
        self.layout = QVBoxLayout(self.content)
        self.layout.setContentsMargins(32, 26, 32, 24)
        self.layout.setSpacing(22)
        if title:
            header = QVBoxLayout()
            header.setSpacing(5)
            header.addWidget(label(title, "Heading"))
            if subtitle:
                header.addWidget(label(subtitle, "Muted", True))
            self.layout.addLayout(header)
        self.setWidget(self.content)

    def panel(self, title=None, caption=None, *, surface="Section"):
        widget = Panel(title, caption, surface)
        self.layout.addWidget(widget)
        return widget

    def pair(self, left, right, *, breakpoint=860, weights=(1, 1), fill=False):
        group = QWidget()
        row = QHBoxLayout(group)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(24)
        for widget, weight in zip((left, right), weights):
            row.addWidget(widget, weight)
        if not fill:
            row.setAlignment(left, Qt.AlignmentFlag.AlignTop)
            row.setAlignment(right, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(group)

        def adapt(width, _height):
            direction = QBoxLayout.Direction.LeftToRight if width >= breakpoint else QBoxLayout.Direction.TopToBottom
            if row.direction() != direction:
                row.setDirection(direction)

        self.resized.connect(adapt)
        adapt(self.viewport().width(), self.viewport().height())
        return group

    def tabs(self, choices, select):
        bar = QFrame()
        bar.setObjectName("Subnav")
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 1)
        row.setSpacing(6)
        buttons = {}
        for key, title in choices:
            item = button(title, lambda value=key: select(value))
            item.setObjectName("SectionTab")
            item.setCheckable(True)
            row.addWidget(item)
            buttons[key] = item
        row.addStretch()
        self.layout.addWidget(bar)
        return buttons

    def finish(self):
        self.layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.viewport().height() < 350
        spacing = 14 if compact else 22
        if self.layout.spacing() != spacing:
            self.layout.setSpacing(spacing)
            margins = (24, 16, 24, 20) if compact else (32, 26, 32, 24)
            self.layout.setContentsMargins(*margins)
        self.resized.emit(self.viewport().width(), self.viewport().height())


class TitleBar(QWidget):
    def __init__(self, window, title="本机工作空间", dialog=False):
        super().__init__()
        self.setObjectName("TitleBar")
        self.window = window
        self.setFixedHeight(43)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 4, 7, 4)
        self.caption = label(title, "Caption")
        layout.addWidget(self.caption)
        layout.addStretch()
        self.controls = {}
        for name, glyph, action in ([] if dialog else [("minimize", "—", window.showMinimized), ("maximize", "□", self.toggle_maximize)]) + [("close", "×", window.reject if dialog else window.close)]:
            widget = button(glyph, action)
            widget.setObjectName("WindowClose" if name == "close" else "WindowControl")
            widget.setFixedSize(40, 30)
            widget.setAccessibleName({"close": "关闭", "maximize": "最大化或还原", "minimize": "最小化"}[name])
            layout.addWidget(widget)
            self.controls[name] = widget

    def toggle_maximize(self):
        self.window.showNormal() if self.window.isMaximized() else self.window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.window.windowHandle():
            self.window.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, event):
        if "maximize" in self.controls and event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()


class Dialog(QDialog):
    def __init__(self, parent, title, width=520):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(title)
        self.dialog_width = width
        self.setMinimumWidth(min(width, max(300, parent.screen().availableGeometry().width() - 32)))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        self.titlebar = TitleBar(self, title, True)
        layout.addWidget(self.titlebar)
        self.body_widget = QWidget()
        self.body = QVBoxLayout(self.body_widget)
        self.body.setContentsMargins(26, 24, 26, 24)
        self.body.setSpacing(14)
        self.body.addWidget(label(title, "SectionTitle"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.body_widget)
        layout.addWidget(scroll)

    def exec(self):
        self.ensurePolished()
        area = self.screen().availableGeometry()
        width = min(self.dialog_width, area.width() - 32)
        self.body_widget.resize(width, self.body_widget.height())
        height = self.body.heightForWidth(width) if self.body.hasHeightForWidth() else self.body.sizeHint().height()
        self.resize(width, min(max(220, height + 45), area.height() - 32))
        self.move(area.center() - self.rect().center())
        return super().exec()


def confirm(parent, title, text):
    dialog = Dialog(parent, title)
    dialog.body.addWidget(label(text, "Muted", True))
    actions = QDialogButtonBox(dialog)
    cancel = actions.addButton("暂不继续", QDialogButtonBox.ButtonRole.RejectRole)
    accept = actions.addButton("确认继续", QDialogButtonBox.ButtonRole.AcceptRole)
    accept.setObjectName("Primary")
    cancel.setDefault(True)
    cancel.setFocus()
    accept.setAutoDefault(False)
    actions.accepted.connect(dialog.accept)
    actions.rejected.connect(dialog.reject)
    dialog.body.addWidget(actions)
    cancel.setDefault(True)
    cancel.setFocus()
    return dialog.exec() == QDialog.DialogCode.Accepted


def notice(parent, title, text, error=False):
    dialog = Dialog(parent, title)
    if len(text) > 700 or text.count("\n") > 10:
        from PySide6.QtWidgets import QPlainTextEdit
        detail = QPlainTextEdit(str(text))
        detail.setReadOnly(True)
        detail.setMinimumHeight(220)
        dialog.body.addWidget(detail)
    else:
        dialog.body.addWidget(label(text, "Muted", True))
    close = button("知道了", dialog.accept, True)
    close.setDefault(True)
    dialog.body.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
    dialog.exec()
