"""Exercise the native OpenSSH client through the smart terminal on loopback.

Paramiko is a test-only server. Authentication, key loading, prompts and input
travel through the same system client and terminal transport as a real session.
"""
import argparse
import base64
import os
from pathlib import Path
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
from PySide6.QtWidgets import QApplication

from enge_spx.smart_terminal import TerminalWindow
from enge_spx.clipboard import Snapshot
from enge_spx.ssh_askpass import PasswordSession, read_password
from enge_spx.ssh_client import Connection, environment, executable
from enge_spx.ssh_transfer import SSHTransfer
from enge_spx.terminal_pty import start

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
                channel.sendall(b"\x1b[2J\x1b[10;1Hcomposer-kept\x1b[1;8r\x1b[8;1H")
                for row in range(160):
                    channel.sendall(f"\r\n\x1b[Kcodex-transcript-{row:03d}".encode())
                channel.sendall(b"\x1b[r\x1b[11;1Hinline-finished")
                assert finish.wait(10)
                channel.sendall(b"\x1b[?1049h\x1b[?1000;1006h\x1b[Hfull-screen-current")
                channel.settimeout(8)
                received.append(channel.recv(4096))
                channel.sendall(b"\x1b[2J\x1b[Hfull-screen-earlier\x1b[?1000;1006l\x1b[?1049l")
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
    child = start(command, {**environment(), "LC_ALL": "C"}, root)
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
        sent.set()
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
        finish.set()
        wait(lambda: "full-screen-current" in rows_text(view.rows()))
        position = QPointF(view.PAD_X + 20, view.PAD_Y + 20)
        event = QWheelEvent(position, QPointF(view.mapToGlobal(QPoint(int(position.x()), int(position.y())))),
                            QPoint(), QPoint(0, 120), Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(view, event)
        wait(lambda: bool(received))
        assert received[0].startswith(b"\x1b[<64;"), "SSH did not pass the wheel to fullscreen Codex"
        wait(lambda: view.output_drained)
        assert "codex-transcript-000" in rows_text(view.screen.history.top)
        assert not errors
        print("PASS SSH keeps Codex inline transcript and forwards fullscreen mouse wheel", flush=True)
    finally:
        finish.set()
        window.close()
        view.reader.join(3)
        listener.close()
        worker.join(2)


class Server(paramiko.ServerInterface):
    def __init__(self, public_key):
        self.public_key = public_key
        self.shell = threading.Event()
        self.auth = None

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
        child = start(command, env, root)
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
        return "/fixture home"

    def local(self, path):
        relative = path.removeprefix("/fixture home/") if path.startswith("/fixture home/") else path.lstrip("/")
        resolved = (self.root / relative).resolve()
        assert resolved.is_relative_to(self.root)
        return resolved

    def stat(self, path):
        try:
            return paramiko.SFTPAttributes.from_stat(self.local(path).stat())
        except FileNotFoundError:
            return paramiko.SFTP_NO_SUCH_FILE

    lstat = stat

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
        handle.writefile = os.fdopen(descriptor, "wb")
        return handle

    def rename(self, oldpath, newpath):
        self.local(oldpath).rename(self.local(newpath))
        return paramiko.SFTP_OK


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
        if args.helper is not None or os.name != "nt":
            with patch("enge_spx.ssh_askpass.packaged_helper", return_value=args.helper.resolve(strict=True) if args.helper else None):
                exercise(app, root, host_key, prefilled=True)
                exercise(app, root, host_key, key, public_key, prefilled=True)
                exercise_upload(app, root, host_key)


if __name__ == "__main__":
    main()
