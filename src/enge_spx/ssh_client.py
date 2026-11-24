"""Interactive remote login with the system OpenSSH client."""
from dataclasses import dataclass
import ipaddress
import os
from pathlib import Path
import re
import shutil

from .state import SPXError

_DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.IGNORECASE | re.ASCII)
_HOST_ERROR = "请输入服务器域名、IPv4 或 IPv6 地址，端口请单独填写。"
# Windows OpenSSH reads ProgramData during startup, including for -F none.
_ENVIRONMENT = {
    "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "PROGRAMDATA", "PATH", "HOME", "USERPROFILE", "USERNAME",
    "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "TMPDIR",
    "LANG", "LC_ALL", "LC_CTYPE",
}


def normalize_host(host):
    host = host.strip()
    if not host or len(host) > 254 or not host.isprintable() or any(c.isspace() for c in host):
        raise SPXError(_HOST_ERROR)
    literal = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    try:
        address = ipaddress.ip_address(literal)
        if "%" not in literal or re.fullmatch(r"[a-zA-Z0-9_.-]+", literal.rsplit("%", 1)[1]):
            return str(address)
    except ValueError:
        pass
    try:
        host = host.encode("idna").decode("ascii").lower()
    except UnicodeError:
        host = ""
    if len(host) > 254 or not all(_DNS_LABEL.fullmatch(label) for label in host.removesuffix(".").split(".")):
        raise SPXError(_HOST_ERROR)
    return host


def executable():
    if os.name == "nt":
        system = Path(os.environ.get("SystemRoot", "C:/Windows"))
        executable_path = system / "System32" / "OpenSSH" / "ssh.exe"
        if executable_path.is_absolute() and executable_path.is_file():
            return str(executable_path)
        raise SPXError("未找到 OpenSSH 客户端。请在 Windows 设置的「可选功能」中安装 OpenSSH 客户端。")
    executable_path = shutil.which("ssh")
    if executable_path and Path(executable_path).is_absolute():
        return executable_path
    raise SPXError("未找到系统 OpenSSH 客户端，请先安装 ssh。")


def environment():
    env = {key: value for key, value in os.environ.items() if key.upper() in _ENVIRONMENT}
    env.update(TERM="xterm-256color", COLORTERM="truecolor")
    return env


@dataclass(frozen=True)
class Connection:
    host: str
    username: str
    port: int
    identity: Path | None

    @classmethod
    def from_fields(cls, host, username, port, identity=None):
        host = normalize_host(host)
        username = username.strip()
        if not username or len(username) > 255 or not username.isprintable() or any(c.isspace() for c in username):
            raise SPXError("请输入有效的 SSH 用户名。")
        if type(port) is not int or not 1 <= port <= 65535:
            raise SPXError("SSH 端口须在 1–65535 之间。")
        if identity is not None:
            try:
                identity = Path(identity).expanduser()
                if not identity.is_absolute() or not str(identity).isprintable() or not identity.is_file():
                    raise ValueError
            except (OSError, RuntimeError, ValueError) as error:
                raise SPXError("请选择可读取的 OpenSSH 私钥文件。") from error
        return cls(host, username, port, identity)

    @property
    def label(self):
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{self.username}@{host}:{self.port}"

    def command(self):
        args = [executable(), "-F", "none", "-tt", "-o", "StrictHostKeyChecking=ask",
                "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
                "-o", "IdentityAgent=none"]
        if self.identity is None:
            args += ["-o", "PreferredAuthentications=password,keyboard-interactive", "-o", "PubkeyAuthentication=no"]
        else:
            path = self.identity.as_posix().replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
            args += ["-o", f'IdentityFile="{path}"', "-o", "IdentitiesOnly=yes",
                     "-o", "PreferredAuthentications=publickey"]
        return [*args, "-l", self.username, "-p", str(self.port), "--", self.host]
