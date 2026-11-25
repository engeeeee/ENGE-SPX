"""Keyboard-driven input templates for the owned terminal."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem

from .. import terminal_shortcuts as shortcuts
from ..state import SPXError
from .widgets import Dialog, button, label


class QuickInput(Dialog):
    def __init__(self, parent, store, tool):
        super().__init__(parent, "快捷输入", 560)
        self.store = store
        self.group = "shell" if tool in ("ssh", "shell") else "assistant"
        self.text = None
        self.search = QLineEdit()
        self.search.setAccessibleName("搜索快捷输入")
        self.search.setPlaceholderText("搜索名称或内容，例如 Git")
        self.search.installEventFilter(self)
        self.body.addWidget(self.search)
        self.items = QListWidget()
        self.items.setMinimumHeight(140)
        self.items.setAccessibleName("快捷输入列表")
        self.body.addWidget(self.items)
        self.preview = label("", "Muted", True)
        self.body.addWidget(self.preview)
        self.body.addWidget(label("↑ ↓ 选择 · Tab 补全 · Enter 插入输入区", "Caption", True))
        self.error = label("", "Muted", True)
        self.error.hide()
        self.body.addWidget(self.error)
        row = QHBoxLayout()
        self.add = button("添加", lambda: self.edit(), ghost=True)
        self.modify = button("编辑", lambda: self.edit(self.selected()), ghost=True)
        self.remove = button("删除", self.remove_selected, ghost=True)
        self.insert = button("插入", self.accept, primary=True)
        self.insert.setDefault(True)
        for control in (self.add, self.modify, self.remove):
            row.addWidget(control)
        row.addStretch()
        row.addWidget(self.insert)
        self.body.addLayout(row)
        try:
            self.custom = shortcuts.load(store)
            self.can_edit = store is not None
        except (OSError, SPXError) as error:
            self.custom, self.can_edit = {}, False
            self.show_error(error)
        self.add.setEnabled(self.can_edit)
        self.search.textChanged.connect(self.filter)
        self.items.currentItemChanged.connect(self.update_selection)
        self.items.itemDoubleClicked.connect(self.accept)
        self.filter()
        self.search.setFocus()

    def eventFilter(self, watched, event):
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down) and self.items.count():
                row = self.items.currentRow() + (1 if key == Qt.Key.Key_Down else -1)
                self.items.setCurrentRow(row % self.items.count())
                return True
            if key == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.NoModifier:
                selected = self.selected()
                if selected is not None:
                    self.search.setText(selected.text)
                    self.search.selectAll()
                return True
        return super().eventFilter(watched, event)

    def filter(self):
        query = self.search.text().strip().casefold()
        choices = {item.key: item for item in shortcuts.BUILTINS if item.group == self.group}
        choices.update({key: item for key, item in self.custom.items() if item.group == self.group})
        self.items.clear()
        for item in choices.values():
            if query not in item.name.casefold() and query not in item.text.casefold():
                continue
            row = QListWidgetItem(item.name)
            row.setData(Qt.ItemDataRole.UserRole, item)
            self.items.addItem(row)
        self.items.setCurrentRow(0)
        self.update_selection()

    def selected(self):
        item = self.items.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def update_selection(self):
        item = self.selected()
        self.preview.setText(item.text if item else "无匹配项")
        self.insert.setEnabled(item is not None)
        custom = bool(self.can_edit and item and item.key in self.custom)
        self.modify.setEnabled(custom)
        self.remove.setEnabled(custom)

    def show_error(self, error):
        self.error.setText(str(error))
        self.error.show()

    def edit(self, previous=None):
        dialog = Dialog(self, "编辑快捷输入" if previous else "添加快捷输入")
        fields = QFormLayout()
        name = QLineEdit(previous.name if previous else "")
        value = QLineEdit(previous.text if previous else "")
        name.setMaxLength(80)
        value.setMaxLength(4096)
        fields.addRow("名称", name)
        fields.addRow("内容", value)
        dialog.body.addLayout(fields)
        dialog.body.addWidget(label("适用于当前类型的终端。输入会留在命令行，等你确认发送。", "Caption", True))
        error = label("", "Muted", True)
        error.hide()
        dialog.body.addWidget(error)

        def save():
            try:
                item = shortcuts.shortcut(self.group, name.text(), value.text())
                self.custom = shortcuts.save(self.store, item, previous)
            except (OSError, SPXError) as problem:
                error.setText(str(problem))
                error.show()
                return
            self.search.setText(item.name)
            self.filter()
            dialog.accept()

        submit = button("保存", save, primary=True)
        submit.setDefault(True)
        dialog.body.addWidget(submit, alignment=Qt.AlignmentFlag.AlignRight)
        name.setFocus()
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def remove_selected(self):
        item = self.selected()
        if item is None or item.key not in self.custom:
            return
        try:
            self.custom = shortcuts.save(self.store, None, item)
        except (OSError, SPXError) as error:
            self.show_error(error)
            return
        self.search.clear()
        self.filter()

    def accept(self):
        item = self.selected()
        if item is not None:
            self.text = item.text
            super().accept()
