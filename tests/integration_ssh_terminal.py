"""Exercise the native OpenSSH client through the smart terminal on loopback.

Paramiko is a test-only server. Authentication, key loading, prompts and input
travel through the same system client and terminal transport as a real session.
"""
import base64
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time

import paramiko
from PySide6.QtWidgets import QApplication

from enge_spx.smart_terminal import TerminalWindow
from enge_spx.ssh_client import Connection, environment, executable
from enge_spx.terminal_pty import start

PASSWORD = "spx-fixture-password"
PASSPHRASE = "spx-fixture-key-passphrase"


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


def exercise(app, root, host_key, identity=None, public_key=None):
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
    command = connection.command()
    command[-2:-2] = ["-o", f'UserKnownHostsFile="{known.as_posix()}"', "-o", "GlobalKnownHostsFile=none"]
    window = None
    try:
        child = start(command, {**environment(), "LC_ALL": "C"}, root)
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
            raise AssertionError(f"Missing {marker!r}. Server errors: {errors}. Terminal: {lines.strip()[-1200:]}")

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
        print(f"PASS {server.auth} through OpenSSH and the smart terminal", flush=True)
    finally:
        if window is not None:
            window.close()
            window.view.reader.join(3)
        listener.close()
        worker.join(2)


def main():
    ssh = executable()
    probe = subprocess.run([ssh, "-V"], env=environment(), capture_output=True, timeout=8)
    assert probe.returncode == 0 and b"OpenSSH" in probe.stdout + probe.stderr, (
        f"OpenSSH did not start with the session environment (exit {probe.returncode})"
    )
    app = QApplication([])
    host_key = paramiko.RSAKey.generate(2048)
    with tempfile.TemporaryDirectory(prefix="spx-ssh-loopback-") as folder:
        root = Path(folder)
        exercise(app, root, host_key)
        key = root / "selected test key 100%.ed25519"
        keygen = Path(ssh).with_name("ssh-keygen.exe" if os.name == "nt" else "ssh-keygen")
        subprocess.run([str(keygen), "-q", "-t", "ed25519", "-N", PASSPHRASE, "-f", str(key)], check=True, timeout=15)
        kind, encoded, *_ = key.with_suffix(".ed25519.pub").read_text().split()
        public_key = paramiko.PKey.from_type_string(kind, base64.b64decode(encoded))
        exercise(app, root, host_key, key, public_key)


if __name__ == "__main__":
    main()
