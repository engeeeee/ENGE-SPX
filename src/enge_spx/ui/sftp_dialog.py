"""Modeless file browser for one explicitly selected SSH destination."""
from datetime import datetime
from pathlib import Path
import posixpath
import re
import stat
import threading
import time

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QStandardPaths, Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QInputDialog,
                               QLineEdit, QProgressBar, QTableView)

from ..sftp_client import ProtocolError, SFTPClient, child_path, display_path
from ..ssh_askpass import PasswordSession, erase, password_available, read_password
from ..ssh_client import environment
from ..state import SPXError
from .widgets import Dialog, button, confirm, label


def file_size(size):
    if size is None:
        return "—"
    if size < 1024:
        return f"{size} B"
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        size /= 1024
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"


def file_type(mode):
    if stat.S_ISDIR(mode):
        return "文件夹"
    if stat.S_ISLNK(mode):
        return "符号链接"
    return "文件" if stat.S_ISREG(mode) else "其他"


def local_name(remote):
    name = re.sub(r'[<>:"/\\|?*]', "_", display_path(remote)).rstrip(" .")
    if not name or re.match(r"(?i)(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", name):
        return "download"
    return name[:180]


class DirectoryModel(QAbstractTableModel):
    HEADERS = ("名称", "类型", "大小", "修改时间")

    def __init__(self, parent):
        super().__init__(parent)
        self.entries = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.entries)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return None
        item = self.entries[index.row()]
        match index.column():
            case 0:
                return display_path(item.name)
            case 1:
                return file_type(item.attributes.mode)
            case 2:
                return file_size(item.attributes.size) if not stat.S_ISDIR(item.attributes.mode) else "—"
            case 3:
                stamp = item.attributes.modified
                return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M") if stamp is not None else "—"
        return None

    def replace(self, entries):
        self.beginResetModel()
        self.entries = entries
        self.endResetModel()


class SFTPDialog(Dialog):
    completed = Signal(object, object)
    progress_changed = Signal(object)

    def __init__(self, parent, connection, *, password=None, session_environment=None, confirm_host=True):
        super().__init__(parent, "SFTP 文件", 900)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.connection = connection
        self.secret = password if password is not None else bytearray()
        self.session_environment = session_environment
        self.confirm_host = confirm_host
        self.login = self.client = None
        self.home = self.directory = None
        self.connected = self.busy = False
        self.closing = threading.Event()
        self.cancelled = threading.Event()
        self.success = None
        self.transfer_name = ""
        self.last_progress = 0
        self.body.addWidget(label(connection.label, "Muted", True))

        nav = QHBoxLayout()
        self.home_button = button("主目录", lambda: self.navigate(self.home), ghost=True)
        self.up_button = button("上一级", lambda: self.navigate(posixpath.dirname(self.directory)), ghost=True)
        self.refresh_button = button("刷新", lambda: self.navigate(self.directory), ghost=True)
        for control in (self.home_button, self.up_button, self.refresh_button):
            nav.addWidget(control)
        self.address = QLineEdit()
        self.address.setPlaceholderText("远端目录")
        self.address.setAccessibleName("远端目录")
        self.address.returnPressed.connect(self.navigate_address)
        nav.addWidget(self.address, 1)
        self.go_button = button("前往", self.navigate_address, ghost=True)
        nav.addWidget(self.go_button)
        self.body.addLayout(nav)

        self.model = DirectoryModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAccessibleName("远端文件和文件夹")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 88)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setMinimumHeight(220)
        self.table.activated.connect(self.activate_entry)
        self.table.selectionModel().selectionChanged.connect(self.update_controls)
        self.body.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.upload_button = button("上传文件", self.choose_upload, primary=True)
        self.download_button = button("下载文件", self.choose_download)
        self.mkdir_button = button("新建文件夹", self.new_folder, ghost=True)
        self.reconnect_button = button("重新连接", self.connect_remote)
        self.cancel_button = button("取消传输", self.cancel_transfer, ghost=True)
        for control in (self.upload_button, self.download_button, self.mkdir_button, self.reconnect_button):
            actions.addWidget(control)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        self.body.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setAccessibleName("文件传输进度")
        self.progress.hide()
        self.body.addWidget(self.progress)
        self.status = label("正在连接 SFTP…", "Muted", True)
        self.body.addWidget(self.status)
        self.completed.connect(self.operation_done, Qt.ConnectionType.QueuedConnection)
        self.progress_changed.connect(self.show_progress, Qt.ConnectionType.QueuedConnection)
        self.finished.connect(self.shutdown)
        self.update_controls()

    def open_browser(self):
        area = self.screen().availableGeometry()
        self.resize(min(900, area.width() - 32), min(620, area.height() - 32))
        self.move(area.center() - self.rect().center())
        self.show()
        self.connect_remote()

    def prompt_password(self, key_login):
        caption = "私钥口令" if key_login else "SSH 密码"
        text, accepted = QInputDialog.getText(self, caption, f"为 {self.connection.label} 输入{caption}",
                                               QLineEdit.EchoMode.Password)
        if not accepted:
            return None
        try:
            return read_password(text)
        except SPXError as error:
            self.status.setText(str(error))
            return None

    def connect_remote(self):
        if self.busy or self.closing.is_set():
            return
        self.connected = False
        if self.client is not None:
            self.client.close()
        env = self.session_environment
        try:
            if env is None:
                env = environment()
                if password_available():
                    if self.login is not None:
                        self.login.close()
                    self.login = PasswordSession(
                        self.connection, self.secret, self.confirm_fingerprint, self, request_secret=self.prompt_password)
                    self.secret = bytearray()
                    env = self.login.start(env)
            self.client = SFTPClient(self.connection, env, askpass=self.login is not None or self.session_environment is not None,
                                     confirm_host=self.confirm_host and self.login is not None)
        except (OSError, SPXError) as error:
            self.status.setText(str(error) if isinstance(error, SPXError) else "无法准备此连接的 SSH 登录。")
            self.update_controls()
            return

        def connect():
            self.client.connect()
            return self.client.list_directory(b".")

        def show_home(result):
            self.connected = True
            self.home = result[0]
            self.show_directory(result)

        self.run_operation("正在连接 SFTP…", connect, show_home)

    def confirm_fingerprint(self, prompt):
        return confirm(self, "核对 SSH 主机指纹", prompt)

    def selected(self):
        rows = self.table.selectionModel().selectedRows()
        return self.model.entries[rows[0].row()] if rows else None

    def update_controls(self):
        browse = self.connected and not self.busy
        for control in (self.home_button, self.up_button, self.refresh_button, self.address, self.go_button,
                        self.table, self.upload_button, self.mkdir_button):
            control.setEnabled(browse)
        item = self.selected()
        self.download_button.setEnabled(browse and item is not None and not stat.S_ISDIR(item.attributes.mode))
        self.reconnect_button.setVisible(not self.connected)
        self.reconnect_button.setEnabled(not self.busy)
        self.cancel_button.setVisible(self.busy and bool(self.transfer_name))

    def run_operation(self, message, operation, on_success, *, transfer=False):
        if self.busy or self.closing.is_set():
            return
        self.busy = True
        self.success = on_success
        self.cancelled.clear()
        self.transfer_name = message if transfer else ""
        self.last_progress = 0
        self.progress.setValue(0)
        self.progress.setVisible(transfer)
        self.cancel_button.setEnabled(True)
        self.status.setText(message)
        self.update_controls()

        def run():
            value = error = None
            try:
                value = operation()
            except ProtocolError as problem:
                self.client.close()
                error = str(problem)
            except SPXError as problem:
                error = str(problem)
            except (OSError, ValueError):
                error = "无法完成文件操作，请检查文件权限、空间和连接状态。"
            if not self.closing.is_set():
                try:
                    self.completed.emit(value, error)
                except RuntimeError:
                    pass  # The window closed while this result was queued.

        threading.Thread(target=run, name="spx-sftp-operation", daemon=True).start()

    def operation_done(self, value, error):
        if self.closing.is_set():
            return
        self.busy = False
        self.transfer_name = ""
        self.progress.hide()
        if error is not None:
            if self.client.closed.is_set():
                self.connected = False
            self.status.setText(error)
        elif self.success is not None:
            self.success(value)
        self.update_controls()

    def report_progress(self, moved, total):
        now = time.monotonic()
        if not self.closing.is_set() and (now - self.last_progress > .08 or moved == total):
            self.last_progress = now
            try:
                self.progress_changed.emit((moved, total))
            except RuntimeError:
                pass

    def show_progress(self, values):
        if self.busy and self.transfer_name and not self.closing.is_set() and not self.cancelled.is_set():
            moved, total = values
            self.progress.setValue(int(moved * 100 / total) if total else 100)
            self.status.setText(f"{self.transfer_name}  {file_size(moved)} / {file_size(total)}")

    def cancel_transfer(self):
        self.cancelled.set()
        self.cancel_button.setEnabled(False)
        self.status.setText("正在取消传输…")

    def navigate_address(self):
        if not self.connected:
            return
        text = self.address.text().encode("utf-8")
        self.navigate(posixpath.join(self.directory, text))

    def navigate(self, path, message=""):
        if path is not None:
            self.run_operation("正在读取目录…", lambda: self.client.list_directory(path),
                               lambda result: self.show_directory(result, message))

    def show_directory(self, result, message=""):
        self.directory, entries, truncated = result
        self.address.setText(display_path(self.directory))
        self.model.replace(entries)
        count = f"显示 {len(entries):,} 项" if truncated else f"{len(entries):,} 项"
        self.status.setText(f"{message} · {count}" if message else count)

    def activate_entry(self, index):
        item = self.model.entries[index.row()]
        path = child_path(self.directory, item.name)
        mode = item.attributes.mode
        if stat.S_ISDIR(mode):
            self.navigate(path)
        elif stat.S_ISREG(mode):
            self.choose_download(item)
        else:
            def open_link(attributes):
                if stat.S_ISDIR(attributes.mode):
                    self.navigate(path)
                elif stat.S_ISREG(attributes.mode):
                    self.choose_download(item)
                else:
                    self.status.setText("请选择普通文件或文件夹。")
            self.run_operation("正在读取文件信息…", lambda: self.client.attributes(path), open_link)

    def choose_download(self, item=None):
        item = item or self.selected()
        if item is None or self.busy:
            return
        downloads = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        suggested = Path(downloads or Path.home()) / local_name(item.name)
        filename, _ = QFileDialog.getSaveFileName(self, "下载到本机", str(suggested),
                                                  options=QFileDialog.Option.DontConfirmOverwrite)
        if not filename:
            return
        remote = child_path(self.directory, item.name)
        self.run_operation("正在下载", lambda: self.client.download(remote, Path(filename), self.report_progress, self.cancelled),
                           lambda _: self.status.setText("下载完成。"), transfer=True)

    def choose_upload(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择要上传的文件")
        if not paths:
            return
        directory = self.directory

        def upload():
            for count, name in enumerate(paths):
                try:
                    self.client.upload(Path(name), directory, self.report_progress, self.cancelled)
                except (OSError, SPXError) as error:
                    if not count:
                        raise
                    detail = str(error) if isinstance(error, SPXError) else "无法读取后续本机文件。"
                    raise SPXError(f"已上传 {count} 个文件。{detail}") from None
            return len(paths)

        self.run_operation("正在上传", upload, lambda count: self.navigate(directory, f"已上传 {count} 个文件"), transfer=True)

    def new_folder(self):
        name, accepted = QInputDialog.getText(self, "新建文件夹", "文件夹名称")
        if not accepted:
            return
        directory = self.directory
        try:
            path = child_path(directory, name.encode("utf-8"))
        except SPXError as error:
            self.status.setText(str(error))
            return
        self.run_operation("正在新建文件夹…", lambda: self.client.mkdir(path),
                           lambda _: self.navigate(directory, "已新建文件夹"))

    def shutdown(self):
        self.closing.set()
        self.cancelled.set()
        if self.client is not None:
            self.client.close()
        if self.login is not None:
            self.login.close()
        erase(self.secret)
