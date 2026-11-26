"""Give the owned SSH and SFTP clients a session credential over local IPC."""
import os
from pathlib import Path
import re
import secrets
import shlex
import sys
import tempfile

from PySide6.QtCore import QCoreApplication, QElapsedTimer, QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from .state import SPXError

CHANNEL = "SPX_SSH_ASKPASS_CHANNEL"
REQUEST_LIMIT = 8192
PASSWORD_LIMIT = 1022  # OpenSSH's askpass buffer also needs a newline and NUL.
AUTH_TIMEOUT = 120_000
HOST_FINGERPRINT = re.compile(r"\bkey fingerprint is:?\s+SHA256:[A-Za-z0-9+/]{43}(?:[.=\s]|$)")


def packaged_helper():
    if getattr(sys, "frozen", False):
        path = Path(sys.executable).resolve().with_name("spx.exe")
        if path.is_file():
            return path
    return None


def password_available():
    return os.name != "nt" or packaged_helper() is not None


def read_password(text):
    try:
        value = bytearray(text, "utf-8")
    except UnicodeError:
        raise SPXError("SSH 密码包含无效字符。") from None
    if len(value) > PASSWORD_LIMIT or any(character in text for character in "\0\r\n"):
        erase(value)
        raise SPXError("SSH 密码不能含换行或空字符，UTF-8 长度最多 1022 字节。")
    return value


def erase(secret):
    secret[:] = bytes(len(secret))


class PasswordSession(QObject):
    def __init__(self, connection, secret, confirm, parent=None, *, request_secret=None):
        super().__init__(parent)
        self.secret = secret
        self.confirm = confirm
        self.request_secret = request_secret
        self.key_login = connection.identity is not None
        self.prompts = {f"{connection.username}@{connection.host}'s password:",
                        f"{connection.username[:30]}@{connection.host[:128]}'s password:"}
        self.channel = "enge-spx-ssh-" + secrets.token_hex(24)
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.setMaxPendingConnections(2)
        self.server.newConnection.connect(self.accept)
        self.helper_folder = None
        self.closed = False

    def start(self, environment):
        helper = packaged_helper()
        if helper is None:
            if os.name == "nt":
                raise SPXError("当前 Windows 源码运行缺少 spx.exe。请使用打包版，或留空密码后按终端提示输入。")
            self.helper_folder = tempfile.TemporaryDirectory(prefix="spx-askpass-")
            helper = Path(self.helper_folder.name) / "askpass"
            command = shlex.join([sys.executable, "-m", "enge_spx.ssh_askpass"])
            helper.write_text('#!/bin/sh\nexec ' + command + ' "$@"\n', encoding="utf-8")
            helper.chmod(0o700)
            environment = {**environment, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
        if not self.server.listen(self.channel):
            raise SPXError("无法建立本机 SSH 密码通道，请重新连接。")
        return {**environment, "SSH_ASKPASS": str(helper), "SSH_ASKPASS_REQUIRE": "force", CHANNEL: self.channel}

    def accept(self):
        while self.server.hasPendingConnections():
            peer = self.server.nextPendingConnection()
            peer.setReadBufferSize(REQUEST_LIMIT + 1)
            peer.disconnected.connect(peer.deleteLater)
            peer.readyRead.connect(lambda peer=peer: self.reply(peer))
            QTimer.singleShot(5_000, peer, lambda peer=peer: peer.abort() if not peer.property("received") else None)
            self.reply(peer)

    def reply(self, peer):
        if peer.property("received") or self.closed:
            return
        if peer.bytesAvailable() > REQUEST_LIMIT:
            peer.abort()
            return
        if not peer.canReadLine():
            return
        peer.setProperty("received", True)
        # The helper hex-encodes the native prompt so its line breaks are not
        # confused with the framing. Server banners never invoke this helper.
        try:
            prompt = bytes.fromhex(bytes(peer.readLine(REQUEST_LIMIT + 1)).decode("ascii")).decode("utf-8")
        except (UnicodeError, ValueError):
            peer.abort()
            return
        disconnected = False

        def note_disconnect():
            nonlocal disconnected
            disconnected = True

        peer.disconnected.connect(note_disconnect)
        answer = None
        key_prompt = self.key_login and prompt.startswith("Enter passphrase for key ")
        password_prompt = not self.key_login and prompt.strip() in self.prompts
        if key_prompt or password_prompt:
            if not self.secret and self.request_secret is not None:
                supplied = self.request_secret(self.key_login)
                if supplied is not None:
                    if self.closed or disconnected:
                        erase(supplied)
                    else:
                        self.secret = supplied
            if self.secret:
                answer = bytes(self.secret)
        elif self.confirm is not None and "Are you sure you want to continue connecting" in prompt and HOST_FINGERPRINT.search(prompt):
            answer = b"yes" if self.confirm(prompt.strip()) else b"no"
        if disconnected or self.closed:
            return
        if answer is not None:
            peer.write(answer + b"\n")
        peer.disconnectFromServer()

    def close(self):
        if self.closed:
            return
        self.closed = True
        erase(self.secret)
        self.secret.clear()
        self.server.close()
        if self.helper_folder is not None:
            self.helper_folder.cleanup()
            self.helper_folder = None
        self.deleteLater()


def helper_main(argv):
    """Entry point used by OpenSSH. stdout is OpenSSH's private answer pipe."""
    channel = os.environ.get(CHANNEL, "")
    if len(argv) != 1 or not re.fullmatch(r"enge-spx-ssh-[a-f0-9]{48}", channel) or os.environ.get("SSH_ASKPASS_PROMPT") == "none":
        return 1
    request = argv[0].encode("utf-8").hex().encode("ascii") + b"\n"
    if len(request) > REQUEST_LIMIT:
        return 1
    app = QCoreApplication.instance() or QCoreApplication(["spx-ssh-askpass"])
    pipe = QLocalSocket(app)
    pipe.setReadBufferSize(PASSWORD_LIMIT + 2)
    pipe.connectToServer(channel)
    if not pipe.waitForConnected(3_000):
        return 1
    pipe.write(request)
    if not pipe.flush() and pipe.bytesToWrite() and not pipe.waitForBytesWritten(3_000):
        return 1
    elapsed = QElapsedTimer()
    elapsed.start()
    while not pipe.canReadLine():
        remaining = AUTH_TIMEOUT - elapsed.elapsed()
        if remaining <= 0 or not pipe.waitForReadyRead(remaining):
            return 1
    answer = bytes(pipe.readLine(PASSWORD_LIMIT + 2))
    if not answer.endswith(b"\n") or len(answer) > PASSWORD_LIMIT + 1:
        return 1
    sys.stdout.buffer.write(answer)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(helper_main(sys.argv[1:]))
