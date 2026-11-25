"""Saved SSH destinations and optional Windows-protected credentials."""
import base64
from dataclasses import dataclass, field
import json
import re
from uuid import uuid4

from .ssh_client import Connection
from .state import SPXError

FILE = "ssh-machines.json"
LOCK = "ssh-machines"
_INVALID = "SSH 机器信息格式无效，原文件已保留。"
_CHANGED = "这条 SSH 机器信息已变更，请重新选择后再试。"
_FIELDS = {"name", "host", "username", "port", "identity"}
_PROTECTED_LIMIT = 8192


@dataclass(frozen=True)
class Machine:
    id: str
    name: str
    connection: Connection
    protected_password: str | None = field(default=None, repr=False)

    @property
    def has_password(self):
        return self.protected_password is not None

    @property
    def title(self):
        return self.name or self.connection.label


def machine_name(value):
    name = value.strip() if isinstance(value, str) else None
    if name is None or len(name) > 80 or (name and not name.isprintable()):
        raise SPXError("机器名称最多 80 个可显示字符。")
    return name


def load(store):
    value = store.read(FILE, {"schema": 1, "machines": {}})
    if (not isinstance(value, dict) or set(value) != {"schema", "machines"}
            or type(value["schema"]) is not int or value["schema"] not in (1, 2)
            or not isinstance(value["machines"], dict)):
        raise SPXError(_INVALID)
    result = {}
    for identifier, row in value["machines"].items():
        fields = set(row) if isinstance(row, dict) else set()
        allowed = fields == _FIELDS or (value["schema"] == 2 and fields == _FIELDS | {"dpapi"})
        if (not re.fullmatch(r"[a-f0-9]{32}", identifier) or not isinstance(row, dict)
                or not allowed
                or not isinstance(row["host"], str) or not isinstance(row["username"], str)
                or "dpapi" in row and (not isinstance(row["dpapi"], str) or not 0 < len(row["dpapi"]) <= _PROTECTED_LIMIT)
                or row["identity"] is not None and not isinstance(row["identity"], str)):
            raise SPXError(_INVALID)
        try:
            connection = Connection.from_fields(row["host"], row["username"], row["port"], row["identity"],
                                                require_key_file=False)
            result[identifier] = Machine(identifier, machine_name(row["name"]), connection, row.get("dpapi"))
        except SPXError as error:
            raise SPXError(_INVALID) from error
    return result


def _write(store, machines):
    rows = {}
    for identifier, machine in machines.items():
        connection = machine.connection
        rows[identifier] = {"name": machine.name, "host": connection.host, "username": connection.username,
                            "port": connection.port, "identity": str(connection.identity) if connection.identity else None}
        if machine.has_password:
            rows[identifier]["dpapi"] = machine.protected_password
    schema = 2 if any(machine.has_password for machine in machines.values()) else 1
    store.write(FILE, {"schema": schema, "machines": rows})


def _entropy(store, identifier, connection):
    target = (identifier, connection.host, connection.username, connection.port,
              str(connection.identity) if connection.identity else None)
    return store.credentials.entropy("ssh-password-v1:" + json.dumps(target, ensure_ascii=False))


def load_password(store, machine):
    if load(store).get(machine.id) != machine:
        raise SPXError(_CHANGED)
    if not machine.has_password:
        return None
    protector = store.credentials.protector
    if protector is None:
        raise SPXError("请在保存凭据的 Windows 用户下连接此机器，或在编辑中清除已保存的凭据。")
    try:
        data = base64.b64decode(machine.protected_password, validate=True)
        return bytearray(protector.unprotect(data, _entropy(store, machine.id, machine.connection)))
    except (ValueError, OSError, SPXError):
        raise SPXError("无法读取已保存的 SSH 凭据。请在编辑中重新填写或清除后连接。") from None


def save(store, name, connection, previous=None, *, password=None, clear_password=False):
    identifier = previous.id if previous else uuid4().hex
    name = machine_name(name)
    with store.lock(LOCK, timeout=.25):
        current = load(store)
        if previous and current.get(previous.id) != previous:
            raise SPXError(_CHANGED)
        protected = None
        if password:
            protector = store.credentials.protector
            if protector is None:
                raise SPXError("此环境无法安全保存 SSH 凭据，请留空后保存。")
            try:
                data = protector.protect(bytes(password), _entropy(store, identifier, connection))
            except (OSError, SPXError):
                raise SPXError("无法加密 SSH 凭据，原连接已保留。") from None
            protected = base64.b64encode(data).decode("ascii")
            if not 0 < len(protected) <= _PROTECTED_LIMIT:
                raise SPXError("SSH 凭据加密结果无效，原连接已保留。")
        elif previous and previous.connection == connection and not clear_password:
            protected = previous.protected_password
        machine = Machine(identifier, name, connection, protected)
        current[identifier] = machine
        _write(store, current)
    return machine


def remove(store, machine):
    with store.lock(LOCK, timeout=.25):
        current = load(store)
        if current.get(machine.id) != machine:
            raise SPXError(_CHANGED)
        del current[machine.id]
        _write(store, current)
