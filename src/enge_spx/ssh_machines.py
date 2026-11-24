"""Saved SSH destinations scoped to the app data directory."""
from dataclasses import dataclass
import re
from uuid import uuid4

from .ssh_client import Connection
from .state import SPXError

FILE = "ssh-machines.json"
LOCK = "ssh-machines"
_INVALID = "SSH 机器信息格式无效，原文件已保留。"
_CHANGED = "这条 SSH 机器信息已变更，请重新选择后再试。"


@dataclass(frozen=True)
class Machine:
    id: str
    name: str
    connection: Connection

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
    if not isinstance(value, dict) or set(value) != {"schema", "machines"} or type(value["schema"]) is not int or value["schema"] != 1 or not isinstance(value["machines"], dict):
        raise SPXError(_INVALID)
    result = {}
    for identifier, row in value["machines"].items():
        if (not re.fullmatch(r"[a-f0-9]{32}", identifier) or not isinstance(row, dict)
                or set(row) != {"name", "host", "username", "port", "identity"}
                or not isinstance(row["host"], str) or not isinstance(row["username"], str)
                or row["identity"] is not None and not isinstance(row["identity"], str)):
            raise SPXError(_INVALID)
        try:
            connection = Connection.from_fields(row["host"], row["username"], row["port"], row["identity"],
                                                require_key_file=False)
            result[identifier] = Machine(identifier, machine_name(row["name"]), connection)
        except SPXError as error:
            raise SPXError(_INVALID) from error
    return result


def _write(store, machines):
    rows = {}
    for identifier, machine in machines.items():
        connection = machine.connection
        rows[identifier] = {"name": machine.name, "host": connection.host, "username": connection.username,
                            "port": connection.port, "identity": str(connection.identity) if connection.identity else None}
    store.write(FILE, {"schema": 1, "machines": rows})


def save(store, name, connection, previous=None):
    machine = Machine(previous.id if previous else uuid4().hex, machine_name(name), connection)
    with store.lock(LOCK, timeout=.25):
        current = load(store)
        if previous and current.get(previous.id) != previous:
            raise SPXError(_CHANGED)
        current[machine.id] = machine
        _write(store, current)
    return machine


def remove(store, machine):
    with store.lock(LOCK, timeout=.25):
        current = load(store)
        if current.get(machine.id) != machine:
            raise SPXError(_CHANGED)
        del current[machine.id]
        _write(store, current)
