"""Exercise the native OpenSSH client through the smart terminal on loopback.

Paramiko is a test-only server. Authentication, key loading, prompts and input
travel through the same system client and terminal transport as a real session.
"""
import argparse
import base64
import os
from pathlib import Path
import posixpath
import socket
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import paramiko
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QWidget

from enge_spx.smart_terminal import TerminalWindow
from enge_spx.clipboard import Snapshot
from enge_spx.ssh_askpass import PasswordSession, read_password
from enge_spx.ssh_client import Connection, environment, executable
from enge_spx.ssh_transfer import SSHTransfer
from enge_spx.terminal_pty import start
from enge_spx.ui.sftp_dialog import SFTPDialog

PASSWORD = "spx-fixture-password"
PASSPHRASE = "spx-fixture-key-passphrase"


def exercise_transcript(app, root, host_key):
    """Replay the partial scrolling region used by Codex inline mode."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(12)
    port = listener.getsockname()[1]
    server = Server(None)
    sent = threading.Event()
    finish = threading.Event()
    close_transcript = threading.Event()
    errors = []
    received = []

    def serve():
        try:
            client, _ = listener.accept()
            with paramiko.Transport(client) as transport:
                transport.add_server_key(host_key)
                transport.start_server(server=server)
                channel = transport.accept(15)
                assert channel is not None and server.shell.wait(5)
                assert sent.wait(10)
                channel.settimeout(8)

                def receive(size):
                    data = bytearray()
                    while len(data) < size:
                        part = channel.recv(size - len(data))
                        assert part
                        data.extend(part)
                    return bytes(data)

                channel.sendall(b"\x1b[2J\x1b[H\x1b[?2004hfixture@server:~$ ")
                prefix = receive(6)
                assert prefix == b"git st"
                channel.sendall(prefix)
                suffix = receive(len(b"\x1b[200~atus --short\x1b[201~"))
                assert suffix == b"\x1b[200~atus --short\x1b[201~"
                channel.sendall(b"atus --short")
                assert receive(1) == b"\r", "Only explicit Enter may run the filled-in command"
                channel.sendall(b"\x1b[?2004l")
                channel.sendall(b"\r\nfixture@server:~# ")
                prefix = receive(4)
                assert prefix == b"df -"
                channel.sendall(prefix)
                assert receive(1) == b"h"
                channel.sendall(b"h")
                assert receive(1) == b"\r", "Plain completion must leave the command in the input line"
                channel.sendall(b"\x1b[2J\x1b[10;1Hcomposer-kept\x1b[1;8r\x1b[8;1H")
                for row in range(160):
                    channel.sendall(f"\r\n\x1b[Kcodex-transcript-{row:03d}".encode())
                channel.sendall(b"\x1b[r\x1b[11;1Hinline-finished")
                channel.settimeout(8)
                assert channel.recv(4096) == b"\t"
                assert finish.wait(10)
                channel.sendall(b"\x1b[?1049h\x1b[?1000;1006h\x1b[Hfull-screen-current")
                packet = channel.recv(4096)
                while len(packet) < 32 and not packet.endswith(b"M"):
                    more = channel.recv(32)
                    if not more:
                        break
                    packet += more
                received.append(packet)
                channel.sendall(b"\x1b[2J\x1b[Hfull-screen-earlier")
                assert close_transcript.wait(10)
                channel.sendall(b"\x1b[?1000;1006l\x1b[?1049l")
                channel.send_exit_status(0)
                channel.shutdown_write()
        except Exception as error:
            errors.append(type(error).__name__)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    known = root / "known_transcript"
    known.write_text(f"[127.0.0.1]:{port} {host_key.get_name()} {host_key.get_base64()}\n", encoding="ascii")
    connection = Connection.from_fields("127.0.0.1", "fixture", port)
    command = connection.command()
    command[-2:-2] = ["-o", f'UserKnownHostsFile="{known.as_posix()}"', "-o", "GlobalKnownHostsFile=none"]
    child = start(command, {**environment(), "LC_ALL": "C"}, root, ssh=True)
    window = TerminalWindow(child, "ssh", root, session_label=connection.label)
    window.show()
    view = window.view

    def rows_text(rows):
        return "\n".join("".join(cell.data for _, cell in sorted(row.items())) for row in rows)

    def wait(predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return
            time.sleep(.01)
        raise AssertionError(f"SSH transcript fixture timed out; errors={errors}, output={rows_text(view.rows())[-700:]!r}")

    try:
        wait(lambda: "password:" in rows_text(view.rows()).casefold())
        view.sender.put("keys", PASSWORD.encode() + b"\r")
        wait(server.shell.is_set)
        window.resize(window.width() - 100, window.height() - 100)
        wait(lambda: server.size is not None and server.size == (view.screen.columns, view.screen.lines))
        sent.set()
        wait(lambda: view.ready.is_set() and "fixture@server:~$ " in rows_text(view.rows()))
        QTest.keyClicks(view, "git st")
        wait(lambda: view.inline_preview is not None)
        assert view.inline_preview[2] == "atus --short"
        assert "git status --short" not in rows_text(view.rows()), "Ghost text must stay outside the terminal buffer"
        view.grab()
        QTest.keyClick(view, Qt.Key.Key_Tab)
        wait(lambda: "git status --short" in rows_text(view.rows()))
        assert view.inline_preview is None
        QTest.keyClick(view, Qt.Key.Key_Return)
        wait(lambda: not view.ready.is_set() and "fixture@server:~# " in rows_text(view.rows()))
        QTest.keyClicks(view, "df -")
        wait(lambda: view.inline_preview is not None and view.inline_preview[2] == "h")
        view.grab()
        QTest.keyClick(view, Qt.Key.Key_Tab)
        wait(lambda: "df -h" in rows_text(view.rows()))
        QTest.keyClick(view, Qt.Key.Key_Return)
        wait(lambda: "inline-finished" in rows_text(view.rows()))
        history = rows_text(view.screen.history.top)
        assert "composer-kept" in rows_text(view.rows())
        assert "codex-transcript-159" in rows_text(view.rows())
        assert "codex-transcript-000" in history and "codex-transcript-120" in history, (
            f"SSH lost Codex's inline transcript; retained {len(view.screen.history.top)} rows"
        )
        view.scrollbar.setValue(view.scrollbar.minimum())
        assert "codex-transcript-000" in rows_text(view.rows())
        view.scrollbar.setValue(view.scrollbar.maximum())
        QTest.keyClick(view, Qt.Key.Key_Tab)
        finish.set()
        wait(lambda: "full-screen-current" in rows_text(view.rows()))
        position = QPointF(view.PAD_X + 20, view.PAD_Y + 20)
        event = QWheelEvent(position, QPointF(view.mapToGlobal(QPoint(int(position.x()), int(position.y())))),
                            QPoint(), QPoint(0, 120), Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(view, event)
        wait(lambda: "full-screen-earlier" in rows_text(view.rows()))
        assert received[0].startswith(b"\x1b[<64;"), "SSH did not pass the wheel to fullscreen Codex"
        close_transcript.set()
        wait(lambda: view.output_drained)
        assert "codex-transcript-000" in rows_text(view.screen.history.top)
        assert not errors
        print("PASS native SSH ghost text and Tab with and without bracketed paste, transcript and fullscreen wheel", flush=True)
    finally:
        finish.set()
        close_transcript.set()
        window.close()
        view.reader.join(3)
        listener.close()
        worker.join(2)


class Server(paramiko.ServerInterface):
    def __init__(self, public_key):
        self.public_key = public_key
        self.shell = threading.Event()
        self.auth = None
        self.size = None

    def get_allowed_auths(self, username):
        return "publickey" if self.public_key else "password"

    def check_auth_password(self, username, password):
        if self.public_key is None and username == "fixture" and password == PASSWORD:
            self.auth = "password"
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        if username == "fixture" and key == self.public_key:
            self.auth = "private key"
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, channel):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, *unused):
        return True

    def check_channel_window_change_request(self, channel, width, height, pixel_width, pixel_height):
        self.size = width, height
        return True

    def check_channel_shell_request(self, channel):
        self.shell.set()
        return True


def exercise(app, root, host_key, identity=None, public_key=None, *, prefilled=False):
    errors = []
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(12)
    port = listener.getsockname()[1]
    server = Server(public_key)

    def serve():
        try:
            client, _ = listener.accept()
            with paramiko.Transport(client) as transport:
                transport.add_server_key(host_key)
                transport.start_server(server=server)
                channel = transport.accept(15)
                assert channel is not None and server.shell.wait(5)
                if prefilled:
                    channel.sendall(b"".join(f"record-{row:04d}\r\n".encode() for row in range(2510)))
                channel.sendall(b"SPX-SSH-LOGIN-OK\r\n")
                channel.send_exit_status(0)
                channel.shutdown_write()
                channel.close()
        except Exception as error:
            errors.append(type(error).__name__)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    known = root / f"known_{port}"
    known.touch()
    connection = Connection.from_fields("127.0.0.1", "fixture", port, identity)
    command = connection.command(prefilled_password=prefilled)
    command[-2:-2] = ["-o", f'UserKnownHostsFile="{known.as_posix()}"', "-o", "GlobalKnownHostsFile=none"]
    window = login = None
    secret = read_password(PASSPHRASE if identity else PASSWORD)
    confirmations = []
    helper_requests = []
    try:
        env = {**environment(), "LC_ALL": "C"}
        if prefilled:
            def confirm(prompt):
                assert server.auth is None
                assert "SHA256:" in prompt
                confirmations.append(prompt)
                return True
            login = PasswordSession(connection, secret, confirm)
            env = login.start(env)
            login.server.newConnection.connect(lambda: helper_requests.append(1))
            assert all(bytes(secret).decode() not in value for value in (*command, *env.values()))
        child = start(command, env, root, ssh=True)
        window = TerminalWindow(child, "ssh", root, session_label=connection.label)
        window.show()
        view = window.view

        def content():
            blank = view.screen.default_char
            return "\n".join("".join(row.get(x, blank).data for x in range(view.screen.columns)) for row in view.rows())

        def wait(marker):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                app.processEvents()
                lines = content()
                if marker.casefold() in lines.casefold():
                    return lines
                if view.output_drained:
                    break
                time.sleep(.01)
            lines = content().replace(PASSWORD, "[fixture]").replace(PASSPHRASE, "[fixture]")
            raise AssertionError(f"Missing {marker!r}. Helper requests: {len(helper_requests)}. "
                                 f"Confirmations: {len(confirmations)}. Server errors: {errors}. Terminal: {lines.strip()[-1200:]}")

        if not prefilled:
            first = wait("Are you sure you want to continue connecting")
            assert "password:" not in first.casefold() and server.auth is None
            assert view.sender.put("keys", b"yes\r")
            prompt, credential = ("password:", PASSWORD) if identity is None else ("Enter passphrase for key", PASSPHRASE)
            wait(prompt)
            assert view.sender.put("keys", credential.encode() + b"\r")
        output = wait("SPX-SSH-LOGIN-OK")
        assert PASSWORD not in output and PASSPHRASE not in output
        assert known.read_text().strip() and not errors
        assert server.auth == ("private key" if public_key else "password")
        if prefilled:
            assert len(confirmations) == 1
            history = "\n".join("".join(cell.data for _, cell in sorted(row.items())) for row in view.screen.history.top)
            assert "record-0000" in history and "record-2100" in history, "SSH scrollback lost long output"
            assert "record-2509" in output
            deadline = time.monotonic() + 5
            while not view.output_drained and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(.01)
            assert view.output_drained, "SSH exit did not deliver the final output and EOF"
        print(f"PASS {'prefilled ' if prefilled else ''}{server.auth} through OpenSSH and the smart terminal", flush=True)
    finally:
        if window is not None:
            window.close()
            window.view.reader.join(3)
        if login is not None:
            login.close()
            assert not secret, "Session credential survived connection close"
        listener.close()
        worker.join(2)


class FixtureSFTP(paramiko.SFTPServerInterface):
    """A localhost-only SFTP root for the native client integration."""

    def __init__(self, server, root):
        super().__init__(server)
        self.root = root.resolve(strict=True)

    def canonicalize(self, path):
        if path.startswith("/"):
            return posixpath.normpath(path)
        return posixpath.normpath("/fixture home/" + path)

    def local(self, path):
        relative = "" if path == "/fixture home" else path.removeprefix("/fixture home/").lstrip("/")
        resolved = (self.root / relative).resolve()
        assert resolved.is_relative_to(self.root)
        return resolved

    def stat(self, path):
        try:
            return paramiko.SFTPAttributes.from_stat(self.local(path).stat())
        except FileNotFoundError:
            return paramiko.SFTP_NO_SUCH_FILE

    lstat = stat

    def list_folder(self, path):
        result = []
        for file in self.local(path).iterdir():
            attrs = paramiko.SFTPAttributes.from_stat(file.lstat(), filename=file.name)
            result.append(attrs)
        return result

    def mkdir(self, path, attr):
        self.local(path).mkdir()
        return paramiko.SFTP_OK

    def chattr(self, path, attr):
        if attr.st_mode is not None:
            self.local(path).chmod(attr.st_mode)
        return paramiko.SFTP_OK

    def open(self, path, flags, attr):
        descriptor = os.open(self.local(path), flags | getattr(os, "O_BINARY", 0), 0o600)
        handle = paramiko.SFTPHandle(flags)
        stream = os.fdopen(descriptor, "r+b" if flags & os.O_RDWR else "wb" if flags & os.O_WRONLY else "rb")
        if not flags & os.O_WRONLY:
            handle.readfile = stream
        if flags & (os.O_WRONLY | os.O_RDWR):
            handle.writefile = stream
        handle.stat = lambda: paramiko.SFTPAttributes.from_stat(os.fstat(stream.fileno()))
        return handle

    def rename(self, oldpath, newpath):
        if self.local(newpath).exists():
            return paramiko.SFTP_FAILURE
        self.local(oldpath).rename(self.local(newpath))
        return paramiko.SFTP_OK

    def remove(self, path):
        self.local(path).unlink()
        return paramiko.SFTP_OK


def exercise_file_browser(app, root, host_key):
    remote = root / "browser-remote"
    directory = remote / "子目录"
    directory.mkdir(parents=True)
    source = root / "测试 文件 #1.bin"
    payload = bytes(range(256)) * 2_600
    source.write_bytes(payload)
    target = root / "下载 文件.bin"
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(12)
    port = listener.getsockname()[1]
    server = Server(None)

    def serve():
        peer, _ = listener.accept()
        with paramiko.Transport(peer) as transport:
            transport.add_server_key(host_key)
            transport.set_subsystem_handler("sftp", paramiko.SFTPServer, FixtureSFTP, remote)
            transport.start_server(server=server)
            deadline = time.monotonic() + 30
            while transport.is_active() and time.monotonic() < deadline:
                time.sleep(.01)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    known = root / "browser_known_hosts"
    known.touch()
    connection = Connection.from_fields("127.0.0.1", "fixture", port)
    options = Connection.options

    def isolated_hosts(value, **kwargs):
        return options(value, **kwargs) + ["-o", f'UserKnownHostsFile="{known.as_posix()}"', "-o", "GlobalKnownHostsFile=none"]

    parent = QWidget()
    parent.show()
    browser = SFTPDialog(parent, connection)
    secret = read_password(PASSWORD)

    def wait(predicate):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return
            time.sleep(.01)
        raise AssertionError("SFTP browser did not reach expected state: " + browser.status.text())

    try:
        with patch.object(Connection, "options", isolated_hosts), \
                patch.object(browser, "confirm_fingerprint", return_value=True) as fingerprint, \
                patch.object(browser, "prompt_password", return_value=secret) as password:
            browser.open_browser()
            wait(lambda: browser.connected and not browser.busy)
        fingerprint.assert_called_once()
        assert "SHA256:" in fingerprint.call_args.args[0]
        password.assert_called_once_with(False)
        assert browser.address.text() == "/fixture home" and server.auth == "password"
        browser.table.activated.emit(browser.model.index(0, 0))
        wait(lambda: browser.address.text().endswith("/子目录") and not browser.busy)

        with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(source)], "")):
            browser.upload_button.click()
        wait(lambda: not browser.busy and browser.model.rowCount() == 1)
        assert (directory / source.name).read_bytes() == payload
        assert browser.model.data(browser.model.index(0, 0)) == source.name
        browser.table.selectRow(0)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(target), "")):
            browser.download_button.click()
        wait(lambda: not browser.busy and target.is_file())
        assert target.read_bytes() == payload

        with patch.object(QInputDialog, "getText", return_value=("新建目录", True)):
            browser.mkdir_button.click()
        wait(lambda: not browser.busy and browser.model.rowCount() == 2)
        assert (directory / "新建目录").is_dir()
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(source)], "")):
            browser.upload_button.click()
        wait(lambda: not browser.busy)
        assert "同名文件" in browser.status.text() and (directory / source.name).read_bytes() == payload

        cancelled = root / "cancel.bin"
        cancelled.write_bytes(payload)
        def cancel_on_progress(moved, total):
            if moved:
                browser.cancelled.set()
        browser.run_operation("测试上传取消", lambda: browser.client.upload(
            cancelled, browser.directory, cancel_on_progress, browser.cancelled), None, transfer=True)
        wait(lambda: not browser.busy)
        assert "取消" in browser.status.text()
        assert not (directory / cancelled.name).exists() and not list(directory.glob("*.part"))
        print("PASS native SFTP fingerprint, login, Unicode navigation, upload, download, mkdir and cancellation", flush=True)
    finally:
        client = browser.client
        browser.close()
        assert client is None or client.closed.is_set()
        assert not secret
        parent.close()
        listener.close()
        worker.join(3)


def exercise_upload(app, root, host_key):
    remote = root / "remote-files"
    remote.mkdir()
    source = root / "中文 log.txt"
    source.write_text("synthetic clipboard file 写入\n", encoding="utf-8")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(10)
    port = listener.getsockname()[1]
    server = Server(None)

    def serve():
        client, _ = listener.accept()
        with paramiko.Transport(client) as transport:
            transport.add_server_key(host_key)
            transport.set_subsystem_handler("sftp", paramiko.SFTPServer, FixtureSFTP, remote)
            transport.start_server(server=server)
            deadline = time.monotonic() + 20
            while transport.is_active() and time.monotonic() < deadline:
                time.sleep(.02)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    known = root / "sftp_known_hosts"
    known.write_text(f"[127.0.0.1]:{port} {host_key.get_name()} {host_key.get_base64()}\n", encoding="utf-8")
    connection = Connection.from_fields("127.0.0.1", "fixture", port)
    options = Connection.options

    def isolated_hosts(value, **kwargs):
        return options(value, **kwargs) + ["-o", f'UserKnownHostsFile="{known.as_posix()}"', "-o", "GlobalKnownHostsFile=none"]

    secret = read_password(PASSWORD)
    login = PasswordSession(connection, secret, lambda value: False)
    transfer = SSHTransfer(connection, login.start(environment()), prefilled=True)
    processes = []
    popen = subprocess.Popen

    def capture(*args, **kwargs):
        # Test diagnostics only. This fixture has public synthetic credentials.
        kwargs["stderr"] = subprocess.PIPE
        process = popen(*args, **kwargs)
        communicate = process.communicate

        def report(*values, **options):
            output, error = communicate(*values, **options)
            processes.append((process.returncode, (output or b"")[-1000:], (error or b"")[-1000:]))
            return output, error

        process.communicate = report
        return process

    try:
        with patch.object(Connection, "options", isolated_hosts), patch("enge_spx.ssh_transfer.subprocess.Popen", capture), \
                ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(transfer.upload, Snapshot("files", (str(source),)))
            deadline = time.monotonic() + 20
            while not pending.done() and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(.005)
            if not pending.done():
                transfer.close()
                raise AssertionError("Native SFTP did not finish")
            try:
                paths = pending.result()
            except Exception as error:
                diagnostics = repr(processes).replace(PASSWORD, "[fixture]")
                raise AssertionError(f"Native SFTP failed. Authenticated: {server.auth}. Output: {diagnostics}") from error
        uploaded, = remote.glob("*/*")
        assert uploaded.read_bytes() == source.read_bytes()
        assert paths == f"'/fixture home/{uploaded.parent.name}/{uploaded.name}'"
        assert not uploaded.parent.name.endswith(".part") and server.auth == "password"
        print("PASS authenticated native SFTP and exact remote clipboard file bytes", flush=True)
    finally:
        transfer.close()
        login.close()
        listener.close()
        worker.join(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, help="Frozen Windows spx.exe for the native askpass tests")
    parser.add_argument("--transcript-only", action="store_true", help="Run the terminal transcript regression")
    args = parser.parse_args()
    helper = args.helper.resolve(strict=True) if args.helper else None
    if os.name == "nt" and helper is not None:
        console = helper.parent / "_internal" / "ssh-conpty"
        assert all((console / name).is_file() for name in ("conpty.dll", "OpenConsole.exe")), (
            "The Windows package is missing its SSH console host"
        )
    ssh = executable()
    probe = subprocess.run([ssh, "-V"], env=environment(), capture_output=True, timeout=8)
    assert probe.returncode == 0 and b"OpenSSH" in probe.stdout + probe.stderr, (
        f"OpenSSH did not start with the session environment (exit {probe.returncode})"
    )
    print((probe.stdout + probe.stderr).decode("ascii", errors="replace").strip(), flush=True)
    app = QApplication([])
    host_key = paramiko.RSAKey.generate(2048)
    with tempfile.TemporaryDirectory(prefix="spx-ssh-loopback-") as folder:
        root = Path(folder).resolve()
        exercise_transcript(app, root, host_key)
        if args.transcript_only:
            return
        exercise(app, root, host_key)
        key = root / "selected test key 100%.ed25519"
        keygen = Path(ssh).with_name("ssh-keygen.exe" if os.name == "nt" else "ssh-keygen")
        subprocess.run([str(keygen), "-q", "-t", "ed25519", "-N", PASSPHRASE, "-f", str(key)], check=True, timeout=15)
        kind, encoded, *_ = key.with_suffix(".ed25519.pub").read_text().split()
        public_key = paramiko.PKey.from_type_string(kind, base64.b64decode(encoded))
        exercise(app, root, host_key, key, public_key)
        if helper is not None or os.name != "nt":
            with patch("enge_spx.ssh_askpass.packaged_helper", return_value=helper):
                exercise(app, root, host_key, prefilled=True)
                exercise(app, root, host_key, key, public_key, prefilled=True)
                exercise_upload(app, root, host_key)
                exercise_file_browser(app, root, host_key)


if __name__ == "__main__":
    main()
