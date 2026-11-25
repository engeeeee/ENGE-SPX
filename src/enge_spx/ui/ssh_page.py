"""Saved remote connections and the separate SSH entry point."""
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QListWidgetItem

from .. import ssh_machines
from ..state import SPXError
from .ssh_dialog import SSHDialog
from .widgets import Page, Panel, button, label


class SSHPage(Page):
    def __init__(self, window):
        super().__init__("远程 SSH", "使用本机网络连接服务器。首次连接请核对主机指纹。")
        self.window_owner = window
        self.machines = {}
        actions = QHBoxLayout()
        self.add_machine = button("新建机器", self.edit, primary=True)
        self.quick_connect = button("临时连接", window.open_ssh, ghost=True)
        actions.addWidget(self.add_machine)
        actions.addWidget(self.quick_connect)
        actions.addStretch()
        self.layout.addLayout(actions)

        saved = Panel("已保存的机器", surface="LaunchPanel")
        self.list = QListWidget()
        self.list.setObjectName("SSHMachineList")
        self.list.setAccessibleName("已保存的 SSH 机器")
        self.list.setMinimumHeight(190)
        self.list.currentItemChanged.connect(self.update_selection)
        self.list.itemDoubleClicked.connect(self.connect_selected)
        saved.layout.addWidget(self.list)
        self.empty = label("还没有保存的机器。", "Muted", True)
        saved.layout.addWidget(self.empty)

        self.details = Panel("机器信息", surface="RoutePanel")
        self.title = label(kind="SectionTitle", wrap=True)
        self.address = label(kind="Muted", wrap=True)
        self.authentication = label(kind="Muted", wrap=True)
        self.identity = label(kind="Caption", wrap=True)
        for item in (self.title, self.address, self.authentication, self.identity):
            self.details.layout.addWidget(item)
        commands = self.details.row()
        commands.addWidget(button("连接", self.connect_selected, primary=True))
        commands.addWidget(button("编辑", self.edit_selected, ghost=True))
        commands.addWidget(button("删除", self.remove_selected, ghost=True))
        commands.addStretch()
        self.pair(saved, self.details, breakpoint=850, weights=(5, 6))
        self.finish()

    def selected(self):
        item = self.list.currentItem()
        return self.machines.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def reload(self, identifier=None):
        current = self.selected()
        identifier = identifier or (current.id if current else None)
        try:
            self.machines = ssh_machines.load(self.window_owner.c.store)
            message = "还没有保存的机器。"
            self.add_machine.setEnabled(True)
        except (OSError, SPXError) as error:
            self.machines = {}
            message = str(error)
            self.add_machine.setEnabled(False)
        with QSignalBlocker(self.list):
            self.list.clear()
            selected_row = 0
            for row, machine in enumerate(self.machines.values()):
                item = QListWidgetItem(machine.title)
                item.setData(Qt.ItemDataRole.UserRole, machine.id)
                self.list.addItem(item)
                if machine.id == identifier:
                    selected_row = row
            self.list.setCurrentRow(selected_row if self.machines else -1)
        self.list.setVisible(bool(self.machines))
        self.empty.setVisible(not self.machines)
        self.empty.setText(message)
        self.update_selection()

    def update_selection(self):
        machine = self.selected()
        self.details.setVisible(machine is not None)
        if machine is None:
            return
        connection = machine.connection
        self.title.setText(machine.title)
        self.address.setText(connection.label)
        self.address.setVisible(bool(machine.name))
        self.authentication.setText("私钥文件登录" if connection.identity else "密码登录")
        self.identity.setText(str(connection.identity) if connection.identity else "")
        self.identity.setVisible(connection.identity is not None)

    def edit(self, machine=None):
        owner = self.window_owner
        if owner.c.exit_mode is not None:
            return

        def save(name, connection):
            return ssh_machines.save(owner.c.store, name, connection, machine)

        dialog = SSHDialog(owner, machine=machine, on_save=save)
        try:
            accepted = dialog.exec() == QDialog.DialogCode.Accepted
            self.reload(dialog.saved_machine.id if accepted else None)
        finally:
            dialog.deleteLater()

    def edit_selected(self):
        machine = self.selected()
        if machine is not None:
            self.edit(machine)

    def connect_selected(self):
        machine = self.selected()
        if machine is not None:
            self.window_owner.open_ssh(machine=machine)

    def remove_selected(self):
        machine = self.selected()
        controller = self.window_owner.c
        if machine is None or controller.exit_mode is not None or not controller.ask(
                "删除 SSH 机器", f"删除保存的连接配置「{machine.title}」？"):
            return
        try:
            ssh_machines.remove(controller.store, machine)
        except (OSError, SPXError) as error:
            controller.notify("无法删除 SSH 机器", error, True)
        self.reload()
