"""User-managed, single-line terminal inputs. No command history is collected."""
from dataclasses import asdict, dataclass

from .state import SPXError

FILE = "terminal-shortcuts.json"
LOCK = "terminal-shortcuts"
GROUPS = ("shell", "assistant")
MAX_CUSTOM = 64


@dataclass(frozen=True)
class Shortcut:
    group: str
    name: str
    text: str

    @property
    def key(self):
        return self.group, self.name.casefold()


def shortcut(group, name, text):
    if not isinstance(name, str) or not isinstance(text, str) or group not in GROUPS:
        raise SPXError("快捷输入的格式无效。")
    name = name.strip()
    if not name or len(name) > 80 or not name.isprintable():
        raise SPXError("请输入 1 至 80 个可显示字符作为名称。")
    if not text.strip() or len(text) > 4096 or not text.isprintable():
        raise SPXError("输入内容须为单行文字，最多 4096 个可显示字符。")
    return Shortcut(group, name, text)


BUILTINS = (
    Shortcut("shell", "Git 状态", "git status --short"),
    Shortcut("shell", "查看改动", "git diff"),
    Shortcut("shell", "最近提交", "git log --oneline -10"),
    Shortcut("shell", "当前目录", "pwd"),
    Shortcut("shell", "列出文件", "ls -la"),
    Shortcut("shell", "磁盘用量", "df -h"),
    Shortcut("shell", "内存用量", "free -h"),
    Shortcut("shell", "Docker 容器", "docker ps"),
    Shortcut("shell", "Compose 服务", "docker compose ps"),
    Shortcut("assistant", "总结当前改动", "请总结当前改动、受影响的功能和验证结果。"),
    Shortcut("assistant", "定位报错", "请先定位当前报错的原因，再给出最小修复方案。"),
    Shortcut("assistant", "检查测试覆盖", "请检查这次改动的测试覆盖，指出尚未覆盖的回归路径。"),
)


def load(store):
    if store is None:
        return {}
    value = store.read(FILE, {"schema": 1, "shortcuts": []})
    if (not isinstance(value, dict) or set(value) != {"schema", "shortcuts"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or not isinstance(value["shortcuts"], list) or len(value["shortcuts"]) > MAX_CUSTOM):
        raise SPXError("快捷输入文件格式无效，原文件已保留。")
    result = {}
    for row in value["shortcuts"]:
        if not isinstance(row, dict) or set(row) != {"group", "name", "text"}:
            raise SPXError("快捷输入文件格式无效，原文件已保留。")
        item = shortcut(**row)
        if item.key in result:
            raise SPXError("快捷输入存在重名，原文件已保留。")
        result[item.key] = item
    return result


def save(store, replacement, previous=None):
    """Update only the specified shortcut while other terminals may be open."""
    with store.lock(LOCK, timeout=.25):
        current = load(store)
        if previous is not None:
            if current.get(previous.key) != previous:
                raise SPXError("这条快捷输入已变更，请重新打开列表。")
            del current[previous.key]
        if replacement is not None:
            replacement = shortcut(replacement.group, replacement.name, replacement.text)
            if replacement.key in current:
                raise SPXError("已有同名快捷输入，请更换名称。")
            if len(current) >= MAX_CUSTOM:
                raise SPXError("已达到 64 条自定义快捷输入。")
            current[replacement.key] = replacement
        store.write(FILE, {"schema": 1, "shortcuts": [asdict(item) for item in current.values()]})
        return current
