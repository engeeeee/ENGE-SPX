"""SFTP v3 over the system OpenSSH subsystem, with bounded file streaming."""
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from enum import IntEnum
import os
from pathlib import Path
import posixpath
import queue
import stat
import struct
import subprocess
import tempfile
import threading
from uuid import uuid4

from .clipboard_transfer import open_source
from .state import SPXError

MAX_PACKET = 256 * 1024
BLOCK = 32 * 1024
SLOTS = 16
LIST_LIMIT = 20_000
CONNECTION_ERROR = "无法建立 SFTP 会话，请检查服务器是否启用 SFTP、登录凭据及主机指纹。"


class Op(IntEnum):
    INIT = 1
    VERSION = 2
    OPEN = 3
    CLOSE = 4
    READ = 5
    WRITE = 6
    LSTAT = 7
    FSTAT = 8
    OPENDIR = 11
    READDIR = 12
    REMOVE = 13
    MKDIR = 14
    REALPATH = 16
    STAT = 17
    RENAME = 18
    STATUS = 101
    HANDLE = 102
    DATA = 103
    NAME = 104
    ATTRS = 105


class ProtocolError(SPXError):
    def __init__(self):
        super().__init__("服务器返回了无效的 SFTP 数据，会话已关闭。")


class StatusError(SPXError):
    def __init__(self, code):
        self.code = code
        super().__init__({1: "远端文件提前结束。", 2: "服务器找不到该文件或目录。",
                          3: "服务器拒绝此文件操作，请核对目录权限。",
                          8: "服务器不支持此 SFTP 操作。"}.get(code, "服务器未能完成文件操作，请检查权限和同名文件。"))


class TransferCancelled(SPXError):
    def __init__(self):
        super().__init__("已取消文件传输。")


def _u32(value):
    return struct.pack(">I", value)


def _string(value):
    return _u32(len(value)) + value


def _path(value):
    if not 0 < len(value) <= 4096 or b"\0" in value:
        raise SPXError("远端路径为空、过长或含有无效字符。")
    return _string(value)


def child_path(directory, name):
    if name in (b"", b".", b"..") or b"/" in name or b"\\" in name or b"\0" in name:
        raise SPXError("请输入单个有效的文件或文件夹名称。")
    return posixpath.join(directory, name)


def display_path(path):
    return "".join(char if char.isprintable() else f"\\u{ord(char):04x}"
                   for char in path.decode("utf-8", errors="backslashreplace"))


@dataclass(frozen=True)
class Attributes:
    size: int | None
    mode: int
    modified: int | None


@dataclass(frozen=True)
class Entry:
    name: bytes
    attributes: Attributes


class Fields:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, size):
        end = self.offset + size
        if end > len(self.data):
            raise ProtocolError()
        result = self.data[self.offset:end]
        self.offset = end
        return result

    def u32(self):
        return int.from_bytes(self.take(4), "big")

    def string(self):
        return self.take(self.u32())

    def attributes(self):
        flags = self.u32()
        if flags & ~0x8000000f:
            raise ProtocolError()
        size = int.from_bytes(self.take(8), "big") if flags & 1 else None
        if flags & 2:
            self.take(8)  # uid, gid
        mode = self.u32() if flags & 4 else 0
        modified = None
        if flags & 8:
            self.take(4)  # access time
            modified = self.u32()
        if flags & 0x80000000:
            for _ in range(self.u32()):
                self.string()
                self.string()
        return Attributes(size, mode, modified)

    def names(self):
        result = []
        for _ in range(self.u32()):
            name = self.string()
            self.string()  # human-readable longname
            result.append(Entry(name, self.attributes()))
        return result


def _read(stream, size):
    data = bytearray()
    while len(data) < size:
        piece = stream.read(size - len(data))
        if not piece:
            raise EOFError()
        data.extend(piece)
    return bytes(data)


class SFTPClient:
    """One operation at a time; cancellation may close the child from the UI."""
    def __init__(self, connection, environment, *, askpass=False, confirm_host=False):
        self.connection = connection
        self.environment = environment
        self.askpass = askpass
        self.confirm_host = confirm_host
        self.process = None
        self.closed = threading.Event()
        self.lock = threading.Lock()
        self.inbox = queue.Queue(maxsize=SLOTS + 2)
        self.sequence = 0

    def connect(self):
        command = self.connection.sftp_subsystem(askpass=self.askpass, confirm_host=self.confirm_host)
        with self.lock:
            if self.closed.is_set():
                raise TransferCancelled()
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, env=self.environment, bufsize=0,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            threading.Thread(target=self._read_packets, args=(self.process,), name="spx-sftp-read", daemon=True).start()
        self._send(Op.INIT, _u32(3))
        try:
            kind, body = self._receive(245 if self.askpass else 25, connecting=True)
            if kind != Op.VERSION or body.u32() != 3:
                raise SPXError("服务器需要支持 SFTP 第 3 版。")
        except (OSError, SPXError):
            self.close()
            raise

    @staticmethod
    def _terminate(process):
        if process is not None and process.poll() is None:
            with suppress(OSError):
                process.terminate()

    def close(self):
        self.closed.set()
        with self.lock:
            self._terminate(self.process)
        with suppress(queue.Full):
            self.inbox.put_nowait(None)

    def _read_packets(self, process):
        try:
            while not self.closed.is_set():
                size = int.from_bytes(_read(process.stdout, 4), "big")
                if not 1 <= size <= MAX_PACKET:
                    raise ProtocolError()
                data = _read(process.stdout, size)
                while not self.closed.is_set():
                    try:
                        self.inbox.put(data, timeout=.2)
                        break
                    except queue.Full:
                        pass
        except (EOFError, OSError, ProtocolError) as error:
            with suppress(queue.Full):
                self.inbox.put_nowait(error)
        finally:
            self._terminate(process)
            with suppress(OSError, subprocess.TimeoutExpired):
                process.wait(timeout=2)
            process.stdout.close()
            process.stdin.close()

    def _send(self, kind, data):
        if self.closed.is_set():
            raise TransferCancelled()
        packet = memoryview(_u32(1 + len(data)) + bytes((kind,)) + data)
        try:
            while packet:
                written = self.process.stdin.write(packet)
                if not written:
                    raise OSError()
                packet = packet[written:]
        except (OSError, ValueError):
            self.close()
            raise SPXError(CONNECTION_ERROR if not self.sequence else "SFTP 连接已断开。") from None

    def _receive(self, timeout=30, *, connecting=False):
        if self.closed.is_set():
            raise TransferCancelled()
        try:
            packet = self.inbox.get(timeout=timeout)
        except queue.Empty:
            self.close()
            raise SPXError("SFTP 响应超时，请重新连接。") from None
        if isinstance(packet, bytes):
            return packet[0], Fields(packet[1:])
        self.close()
        if isinstance(packet, ProtocolError):
            raise packet
        raise SPXError(CONNECTION_ERROR if connecting else "SFTP 连接已断开。")

    def _queue(self, kind, args):
        self.sequence = (self.sequence + 1) & 0xffffffff
        self._send(kind, _u32(self.sequence) + args)
        return self.sequence

    def _replies(self, pending, expected):
        waiting = set(pending)
        result, problem = {}, None
        while waiting:
            kind, reply = self._receive()
            identifier = reply.u32()
            if identifier not in waiting:
                self.close()
                raise ProtocolError()
            waiting.remove(identifier)
            if kind == Op.STATUS:
                code = reply.u32()
                if code:
                    problem = problem or StatusError(code)
                    continue
            if kind != expected:
                self.close()
                raise ProtocolError()
            result[identifier] = reply
        if problem is not None:
            raise problem
        return result

    def _request(self, kind, data, expected=Op.STATUS):
        identifier = self._queue(kind, data)
        return self._replies((identifier,), expected)[identifier]

    @contextmanager
    def _handle(self, kind, data):
        handle = self._request(kind, data, Op.HANDLE).string()
        if not 0 < len(handle) <= 256:
            self.close()
            raise ProtocolError()
        wire = _string(handle)
        try:
            yield wire
        except BaseException:
            if not self.closed.is_set():
                with suppress(SPXError):
                    self._request(Op.CLOSE, wire)
            raise
        else:
            self._request(Op.CLOSE, wire)

    def list_directory(self, path):
        names = self._request(Op.REALPATH, _path(path), Op.NAME).names()
        if len(names) != 1 or not names[0].name.startswith(b"/"):
            raise SPXError("服务器未返回可浏览的绝对目录路径。")
        directory = names[0].name
        entries, scanned = [], 0
        with self._handle(Op.OPENDIR, _path(directory)) as handle:
            while scanned < LIST_LIMIT:
                try:
                    batch = self._request(Op.READDIR, handle, Op.NAME).names()
                except StatusError as error:
                    if error.code != 1:
                        raise
                    break
                if not batch:
                    break
                scanned += len(batch)
                entries.extend(item for item in batch if item.name not in (b".", b"..") and item.name
                               and not any(piece in item.name for piece in (b"/", b"\\", b"\0")))
        entries.sort(key=lambda item: (not stat.S_ISDIR(item.attributes.mode), display_path(item.name).casefold()))
        return directory, entries[:LIST_LIMIT], scanned >= LIST_LIMIT

    def attributes(self, path):
        return self._request(Op.STAT, _path(path), Op.ATTRS).attributes()

    def mkdir(self, path):
        self._request(Op.MKDIR, _path(path) + _u32(0))

    @staticmethod
    def _check_cancel(cancelled):
        if cancelled.is_set():
            raise TransferCancelled()

    def download(self, remote, destination, progress, cancelled):
        if destination.exists() or destination.is_symlink():
            raise SPXError("保存位置已有同名文件，请选择其他文件名。")
        info = self.attributes(remote)
        if not stat.S_ISREG(info.mode) or info.size is None:
            raise SPXError("请选择服务器上的普通文件。")
        with tempfile.TemporaryDirectory(prefix=".enge-spx-download-", dir=destination.parent) as folder:
            temporary = Path(folder) / "file.part"
            with temporary.open("xb") as output, self._handle(Op.OPEN, _path(remote) + _u32(1) + _u32(0)) as handle:
                offset = 0
                progress(0, info.size)
                while offset < info.size:
                    self._check_cancel(cancelled)
                    pending = {}
                    for start in range(offset, min(info.size, offset + BLOCK * SLOTS), BLOCK):
                        size = min(BLOCK, info.size - start)
                        identifier = self._queue(Op.READ, handle + struct.pack(">QI", start, size))
                        pending[identifier] = size
                    replies = self._replies(pending, Op.DATA)
                    for identifier, size in pending.items():
                        block = replies[identifier].string()
                        if len(block) != size:
                            raise SPXError("远端文件在下载期间发生变化。")
                        output.write(block)
                        offset += size
                    progress(offset, info.size)
                current = self._request(Op.FSTAT, handle, Op.ATTRS).attributes()
                if (current.size, current.modified) != (info.size, info.modified):
                    raise SPXError("远端文件在下载期间发生变化。")
            self._check_cancel(cancelled)
            if os.name == "nt":
                temporary.rename(destination)  # Windows rename refuses an existing name.
            else:
                os.link(temporary, destination)

    def upload(self, source, directory, progress, cancelled):
        target = _path(child_path(directory, source.name.encode("utf-8")))
        try:
            self._request(Op.LSTAT, target, Op.ATTRS)
        except StatusError as error:
            if error.code != 2:
                raise
        else:
            raise SPXError("远端目录已有同名文件，请选择其他目录或改名后上传。")
        temporary = _path(child_path(directory, b".enge-spx-upload-" + uuid4().hex.encode("ascii") + b".part"))
        staged = False
        try:
            with open_source(source, limit=None) as (stream, size):
                progress(0, size)
                flags = 2 | 8 | 32  # WRITE, CREATE, EXCLUSIVE
                with self._handle(Op.OPEN, temporary + _u32(flags) + _u32(4) + _u32(0o600)) as handle:
                    staged = True
                    offset = 0
                    while offset < size:
                        self._check_cancel(cancelled)
                        length = min(BLOCK * SLOTS, size - offset)
                        data = stream.read(length)
                        if len(data) != length:
                            raise SPXError("本机文件在上传期间发生变化。")
                        pending = []
                        for start in range(0, length, BLOCK):
                            block = data[start:start + BLOCK]
                            pending.append(self._queue(Op.WRITE, handle + struct.pack(">Q", offset) + _string(block)))
                            offset += len(block)
                        self._replies(pending, Op.STATUS)
                        progress(offset, size)
                    if stream.read(1):
                        raise SPXError("本机文件在上传期间发生变化。")
            self._check_cancel(cancelled)
            self._request(Op.RENAME, temporary + target)
            staged = False
        finally:
            if staged and not self.closed.is_set():
                with suppress(SPXError):
                    self._request(Op.REMOVE, temporary)
