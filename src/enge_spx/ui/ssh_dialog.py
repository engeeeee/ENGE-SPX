"""Remote login fields for the owned smart terminal."""
from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QSpinBox, QWidget

from ..ssh_client import Connection
from ..state import SPXError
from .widgets import Combo, Dialog, button, label


class SSHDialog(Dialog):
    def __init__(self, parent, *, machine=None, on_save=None):
        super().__init__(parent, ("编辑 SSH 机器" if machine else "新建 SSH 机器") if on_save else "临时 SSH 连接")
        self.connection = None
        self.on_save = on_save
        self.saved_machine = None
        if on_save is None:
            self.body.addWidget(label("通过本机网络连接。首次连接请在终端核对服务器指纹。", "Muted", True))
        form = QFormLayout()
        self.body.addLayout(form)
        if on_save is not None:
            self.name = QLineEdit(machine.name if machine else "")
            self.name.setMaxLength(80)
            self.name.setPlaceholderText("留空时显示用户名和服务器")
            form.addRow("机器名称", self.name)
        self.host = QLineEdit()
        self.host.setMaxLength(254)
        self.host.setPlaceholderText("例如 server.example.com")
        self.username = QLineEdit()
        self.username.setMaxLength(255)
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(22)
        self.auth = Combo()
        self.auth.addItem("密码", "password")
        self.auth.addItem("私钥文件", "identity")
        for caption, field in (("服务器", self.host), ("端口", self.port), ("用户名", self.username), ("登录方式", self.auth)):
            form.addRow(caption, field)

        self.identity = QLineEdit()
        self.identity.setReadOnly(True)
        if machine:
            connection = machine.connection
            self.host.setText(connection.host)
            self.port.setValue(connection.port)
            self.username.setText(connection.username)
            if connection.identity is not None:
                self.auth.setCurrentIndex(self.auth.findData("identity"))
                self.identity.setText(str(connection.identity))
        key_row = QWidget()
        row = QHBoxLayout(key_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.identity, 1)
        row.addWidget(button("选择文件", self.choose_identity))
        form.addRow("私钥", key_row)
        self.hint = label("", "Caption", True)
        self.body.addWidget(self.hint)
        self.error = label("", "Muted", True)
        self.error.hide()
        self.body.addWidget(self.error)

        def auth_changed():
            key_login = self.auth.currentData() == "identity"
            form.setRowVisible(key_row, key_login)
            self.hint.setText("如果私钥有口令，请在终端提示时输入。" if key_login else "连接后请在终端提示时输入密码。")
            self.error.hide()

        self.auth.currentIndexChanged.connect(auth_changed)
        auth_changed()
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("取消", self.reject, ghost=True))
        submit = button("保存" if on_save else "连接", self.accept, primary=True)
        submit.setDefault(True)
        actions.addWidget(submit)
        self.body.addLayout(actions)
        self.host.setFocus()

    def choose_identity(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 OpenSSH 私钥文件", self.identity.text())
        if path:
            self.identity.setText(path)

    def accept(self):
        identity = self.identity.text() if self.auth.currentData() == "identity" else None
        try:
            connection = Connection.from_fields(self.host.text(), self.username.text(), self.port.value(), identity,
                                                require_key_file=self.on_save is None)
            if self.on_save is not None:
                self.saved_machine = self.on_save(self.name.text(), connection)
        except (OSError, SPXError) as error:
            self.error.setText(str(error))
            self.error.show()
            return
        self.connection = connection
        super().accept()
