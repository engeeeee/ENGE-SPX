"""Explicit clipboard imports to the verified SSH destination via system SFTP."""
import io
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import tempfile
import threading
from uuid import uuid4

from .clipboard import MAX_FILES, MAX_IMAGE
from .clipboard_transfer import MAX_BATCH, open_source
from .state import SPXError

PREFIX = b"Remote working directory: "


def file_name(number, source):
    path = Path(source)
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", path.stem).strip(".-")[:48] or "file"
    extension = path.suffix if re.fullmatch(r"\.[a-zA-Z0-9]{1,12}", path.suffix) else ""
    return f"{number:02d}-{stem}{extension.lower()}"


class SSHTransfer:
    tool = "ssh"

    def __init__(self, connection, environment, *, prefilled):
        self.connection = connection
        self.environment = environment
        self.prefilled = prefilled
        self.closed = threading.Event()
        self.lock = threading.Lock()
        self.process = None

    def _send(self, batch, directory, timeout=150):
        command = self.connection.sftp_command(prefilled_password=self.prefilled)
        with self.lock:
            if self.closed.is_set():
                raise SPXError("SSH 会话已关闭，已取消文件传输。")
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, cwd=directory, env=self.environment,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.process = process
        try:
            output, _ = process.communicate(("\n".join(batch) + "\n").encode("ascii"), timeout=timeout)
            return process.returncode, output
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                pass
            raise SPXError("SFTP 传输超时，路径未插入。请检查服务器和网络后重试。") from None
        finally:
            with self.lock:
                self.process = None

    def _copy(self, source, size, destination):
        copied = 0
        with destination.open("xb") as file:
            while block := source.read(256 * 1024):
                if self.closed.is_set():
                    raise SPXError("SSH 会话已关闭，已取消文件传输。")
                copied += len(block)
                if copied > size:
                    raise SPXError("文件大小在读取时发生变化，请重新复制后粘贴。")
                file.write(block)
        if copied != size:
            raise SPXError("文件大小在读取时发生变化，请重新复制后粘贴。")

    def _stage_files(self, snapshot, directory):
        if snapshot.kind == "image" and isinstance(snapshot.value, bytes) and 0 < len(snapshot.value) <= MAX_IMAGE:
            name = "01-screenshot.png"
            self._copy(io.BytesIO(snapshot.value), len(snapshot.value), directory / name)
            return [name]
        if snapshot.kind != "files" or not isinstance(snapshot.value, (tuple, list)) or not 0 < len(snapshot.value) <= MAX_FILES:
            raise SPXError("剪贴板没有可上传的文件。")
        names, total = [], 0
        for number, source in enumerate(snapshot.value, 1):
            name = file_name(number, source)
            with open_source(source) as (stream, size):
                total += size
                if total > MAX_BATCH:
                    raise SPXError("一次粘贴的文件总大小不能超过 256 MiB。")
                self._copy(stream, size, directory / name)
            names.append(name)
        return names

    def upload(self, snapshot):
        if self.connection.identity is None and not self.prefilled:
            raise SPXError("要粘贴文件，请在连接表单填写 SSH 密码后重连，以便认证 SFTP。")
        if self.closed.is_set():
            raise SPXError("SSH 会话已结束，未上传文件。")
        try:
            with tempfile.TemporaryDirectory(prefix="spx-sftp-") as temporary:
                directory = Path(temporary)
                names = self._stage_files(snapshot, directory)
                target = ".enge-spx-paste-" + uuid4().hex
                staged = target + ".part"
                batch = ["pwd", "mkdir " + staged, "chmod 700 " + staged]
                for name in names:
                    remote = staged + "/" + name
                    batch.extend((f"put {name} {remote}", "chmod 600 " + remote))
                batch.extend((f"rename {staged} {target}", "quit"))
                result, output = self._send(batch, directory)
                if result:
                    # The batch only reaches chmod after creating this unique staging directory.
                    if ("sftp> chmod 700 " + staged).encode("ascii") in output and not self.closed.is_set():
                        cleanup = [f"-rm {staged}/{name}" for name in names] + ["-rmdir " + staged, "quit"]
                        try:
                            self._send(cleanup, directory, timeout=20)
                        except (OSError, SPXError):
                            pass
                    raise SPXError("SFTP 上传失败。请检查远端 SFTP、凭据和目录权限；加密私钥可在连接表单填写口令。")
                homes = [line[len(PREFIX):].decode("utf-8") for line in output.splitlines() if line.startswith(PREFIX)]
                if len(homes) != 1 or not homes[0].startswith("/") or not homes[0].isprintable() or len(homes[0]) > 1024:
                    raise SPXError("SFTP 已上传文件，但无法识别远端的绝对路径。请检查远端主目录中的 " + target + "。")
                parent = PurePosixPath(homes[0]) / target
                return " ".join(shlex.quote(str(parent / name)) for name in names)
        except UnicodeError:
            raise SPXError("SFTP 返回了无法识别的远端路径编码。") from None
        except OSError:
            raise SPXError("无法读取剪贴板文件或启动 SFTP，请检查本机文件权限和 OpenSSH 客户端。") from None

    def close(self):
        self.closed.set()
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                try:
                    self.process.terminate()
                except OSError:
                    pass
