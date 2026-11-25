"""Remote login fields for the owned smart terminal."""
from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QSpinBox, QWidget

from ..ssh_client import Connection
from ..state import SPXError
from .widgets import Combo, Dialog, button, label


class SSHDialog(Dialog):
    def __init__(self, parent, *, machine=None, on_save=None):
        title = "连接 SSH 机器" if machine else "临时 SSH 连接"
        if on_save:
            title = "编辑 SSH 机器" if machine else "新建 SSH 机器"
        super().__init__(parent, title)
        self.connection = None
        self.on_save = on_save
        self.saved_machine = None
        self.secret = None
        if on_save is None:
            self.body.addWidget(label("通过本机网络连接。首次连接时请核对服务器指纹。", "Muted", True))
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

        self.password = None
        if on_save is None:
            from ..ssh_askpass import password_available
            self.password = QLineEdit()
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.password.setMaxLength(1022)
            self.password.setEnabled(password_available())
            self.password.setPlaceholderText("选填，留空可在终端输入")
            self.password.setAccessibleName("SSH 密码或私钥口令")
            self.finished.connect(lambda result: self.password.setText(""))

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
        if self.password is not None:
            self.password_label = label("密码")
            form.addRow(self.password_label, self.password)
        self.hint = label("", "Caption", True)
        self.body.addWidget(self.hint)
        self.error = label("", "Muted", True)
        self.error.hide()
        self.body.addWidget(self.error)

        def auth_changed():
            key_login = self.auth.currentData() == "identity"
            form.setRowVisible(key_row, key_login)
            if self.password is not None:
                caption = "私钥口令" if key_login else "密码"
                if self.password_label.text() != caption:
                    self.password_label.setText(caption)
                    self.password.setText("")
            if self.password is None:
                hint = "连接时可填写本次登录密码或私钥口令。"
            elif self.password.isEnabled():
                hint = "凭据仅保留到此 SSH 会话结束，用于登录和粘贴文件。需要多因素认证可留空。"
            else:
                hint = "打包版支持在此填写凭据。当前可在终端提示时输入。"
            self.hint.setText(hint)
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
        focus = self.password if machine and self.password is not None and self.password.isEnabled() else self.host
        focus.setFocus()

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
            elif self.password.isEnabled() and self.password.text():
                from ..ssh_askpass import read_password
                self.secret = read_password(self.password.text())
        except (OSError, SPXError) as error:
            self.error.setText(str(error))
            self.error.show()
            return
        self.connection = connection
        super().accept()

    def take_password(self):
        secret, self.secret = self.secret, None
        return secret
