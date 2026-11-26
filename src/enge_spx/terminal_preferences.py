"""Versioned public terminal preferences, independent of proxy credentials."""
import re
import threading

from PySide6.QtCore import QObject, QTimer, Signal

from .state import SPXError
from .terminal_render import FOREGROUND

FILE = "terminal-preferences.json"
COLOR_ROLES = {
    "background": ("终端背景", None),
    "foreground": ("终端文字", FOREGROUND),
    "cursor": ("光标", "#4f8bff"),
    "selection_background": ("选区背景", "#18386b"),
    "selection_foreground": ("选区文字", "#ffffff"),
    "title_background": ("标题栏背景", None),
    "title_foreground": ("标题栏文字", "#9898a2"),
    "session_background": ("会话栏背景", None),
    "session_foreground": ("会话栏文字", "#e4e4ea"),
    "connection_foreground": ("连接状态文字", "#649eff"),
    "footer_background": ("底栏背景", None),
    "footer_foreground": ("底栏文字", "#82828c"),
    "badge_background": ("工具标签背景", None),
    "badge_foreground": ("工具标签文字", None),
    "border": ("窗口边框与分隔线", "#1e1e22"),
    "menu_background": ("菜单背景", "#0b0b0d"),
    "menu_foreground": ("菜单文字", FOREGROUND),
    "menu_selection_background": ("菜单选中背景", "#142c57"),
    "menu_selection_foreground": ("菜单选中文字", "#ffffff"),
    "scrollbar_track": ("滚动条轨道", None),
    "scrollbar_thumb": ("滚动条滑块", "#2a2a30"),
}
COLOR_FIELDS = {role: "color_" + role for role in COLOR_ROLES}
DEFAULTS = {"font_size": 11, "font_family": "", "copy_on_select": True, "right_click_paste": True,
            "appearance": "solid", "tint": "clay", "opacity": 65,
            **dict.fromkeys(COLOR_FIELDS.values())}
TINTS = {"clay": "#000000", "purple": "#302034", "graphite": "#1d252c"}
MATERIALS = {'solid': '纯色', 'acrylic': 'Acrylic 毛玻璃', 'blur': '柔和模糊',
             'mica': 'Mica 云母', 'mica-alt': 'Mica Alt 深色云母'}
BADGES = {"clay": ("#dce8ff", "#0f1d3a", "#264b8f"),
          "purple": ("#dbc2e5", "#44304d", "#775985"),
          "graphite": ("#bed2e2", "#2f3e4b", "#587186")}
COLOR_PRESETS = {
    "默认配色": {},
    "浅色": {
        "background": "#ffffff", "foreground": "#121a15", "cursor": "#d97757",
        "selection_background": "#e3f4ea", "selection_foreground": "#121a15",
        "title_background": "#ffffff", "title_foreground": "#49584f",
        "session_background": "#f5f8f6", "session_foreground": "#121a15", "connection_foreground": "#237e49",
        "footer_background": "#f5f8f6", "footer_foreground": "#49584f", "border": "#dce6df",
        "badge_background": "#e9f6ee", "badge_foreground": "#237e49",
        "menu_background": "#ffffff", "menu_foreground": "#121a15",
        "menu_selection_background": "#e9f6ee", "menu_selection_foreground": "#237e49",
        "scrollbar_track": "#f5f8f6", "scrollbar_thumb": "#c3d1c8",
    },
    "高对比度": {
        "background": "#101010", "foreground": "#ffffff", "cursor": "#ffdf69",
        "selection_background": "#244b70", "selection_foreground": "#ffffff",
        "title_background": "#191919", "title_foreground": "#ffffff",
        "session_background": "#191919", "session_foreground": "#ffffff", "connection_foreground": "#b2f0a7",
        "footer_background": "#191919", "footer_foreground": "#ffffff", "border": "#777777",
        "badge_background": "#292929", "badge_foreground": "#ffdf69",
        "menu_background": "#202020", "menu_foreground": "#ffffff",
        "menu_selection_background": "#3a5977", "menu_selection_foreground": "#ffffff",
        "scrollbar_track": "#171717", "scrollbar_thumb": "#b6b6b6",
    },
}


def display_color(tint, material):
    from PySide6.QtGui import QColor

    base = QColor(TINTS[tint])
    # Keep the tint family and give each filter a visible signature even when
    # the compositor accepts a backdrop but replaces it with its default fill.
    overlay = {'blur': (88, 92, 100), 'mica': (52, 56, 66),
               'mica-alt': (24, 42, 78)}.get(material)
    if overlay is None:
        return base
    return QColor(*(round(channel * .55 + target * .45) for channel, target in zip(base.getRgb()[:3], overlay)))


def display_palette(values, glass=False):
    from PySide6.QtGui import QColor

    custom = {role: values.get(key) for role, key in COLOR_FIELDS.items() if values.get(key) is not None}
    background = QColor(custom["background"]) if "background" in custom else display_color(
        values["tint"], values["appearance"] if glass else "solid")
    if background.lightness() > 160:
        bar = QColor(*(max(0, channel - 8) for channel in background.getRgb()[:3])).name()
    else:
        bar = QColor(*(min(255, channel + 7) for channel in background.getRgb()[:3])).name()
    title_bar = background.name() if values["tint"] == "clay" and not glass and "background" not in custom else bar
    badge_text, badge_base, _ = BADGES[values["tint"]]
    return {
        **{role: default for role, (_, default) in COLOR_ROLES.items()},
        "background": background.name(), "title_background": title_bar, "session_background": bar,
        "footer_background": bar, "scrollbar_track": background.name(),
        "badge_background": badge_base, "badge_foreground": badge_text,
        **custom,
    }


def validate(value):
    if not isinstance(value, dict) or type(value.get("schema")) is not int or value["schema"] != 1 or set(value) - {"schema", *DEFAULTS}:
        raise SPXError("终端偏好格式无效，原文件已保留；可在右上角恢复默认设置。")
    result = {**DEFAULTS, **{key: value[key] for key in DEFAULTS if key in value}}
    if type(result["font_size"]) is not int or not 8 <= result["font_size"] <= 24 or type(result["opacity"]) is not int or not 30 <= result["opacity"] <= 100:
        raise SPXError("终端字号或背景不透明度超出范围，原设置已保留。")
    if not isinstance(result["font_family"], str) or len(result["font_family"]) > 80 or any(ord(c) < 32 for c in result["font_family"]):
        raise SPXError("终端字体设置无效，原文件已保留。")
    if any(type(result[key]) is not bool for key in ("copy_on_select", "right_click_paste")) or not isinstance(result["appearance"], str) or not isinstance(result["tint"], str) or result["appearance"] not in MATERIALS or result["tint"] not in TINTS:
        raise SPXError("终端外观或鼠标设置无效，原文件已保留。")
    for key in COLOR_FIELDS.values():
        color = result[key]
        if color is not None:
            if not isinstance(color, str) or re.fullmatch(r"#[a-fA-F0-9]{6}", color) is None:
                raise SPXError("终端配色值应使用六位十六进制颜色，原文件已保留。")
            result[key] = color.lower()
    return result


def read(store):
    if store is not None:
        from .credentials import check_path
        check_path(store.home, FILE)
        path = store.home / FILE
        if path.exists() and path.stat().st_size > 65536:
            raise SPXError("终端偏好文件异常过大，原文件已保留。")
    return validate(store.read(FILE, {"schema": 1})) if store is not None else dict(DEFAULTS)


def save(store, patch, reset=False):
    with store.lock("terminal-preferences", timeout=2):
        from .credentials import check_path
        check_path(store.home, FILE)
        current = dict(DEFAULTS) if reset else read(store)
        updated = validate({"schema": 1, **current, **patch})
        if reset and (store.home / FILE).exists():
            # Keep the original public settings for recovery, including a
            # malformed file. Never copy proxy/account configuration here.
            source = store.home / FILE
            with source.open("rb") as stream:
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise SPXError("终端偏好文件异常过大，未覆盖原文件。")
            store.write("terminal-preferences-previous.json", {"schema": 1, "raw_utf8": raw.decode("utf-8", errors="replace")})
        store.write(FILE, {"schema": 1, **updated})
        return updated


class Preferences(QObject):
    changed = Signal(object)
    error = Signal(str)

    def __init__(self, store=None, parent=None):
        super().__init__(parent)
        self.store = store
        self.load_error = None
        try:
            self.value = read(store)
        except (OSError, SPXError) as error:
            self.value, self.load_error = dict(DEFAULTS), str(error)
        self.dirty, self.waiting = {}, {}
        self.worker_lock = threading.Lock()
        self.worker = None
        self.reset_pending = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.flush)

    def set(self, key, value):
        self.update({key: value})

    def update(self, patch):
        updated = validate({"schema": 1, **self.value, **patch})
        changed = {key: updated[key] for key in patch if updated[key] != self.value[key]}
        if not changed:
            return
        self.value = updated
        self.dirty.update(changed)
        self.changed.emit(dict(self.value))
        if self.load_error:
            self.error.emit(self.load_error)
        else:
            self.timer.start()

    def reset(self):
        self.value = dict(DEFAULTS)
        self.dirty = dict(DEFAULTS)
        self.reset_pending, self.load_error = True, None
        self.changed.emit(dict(self.value))
        self.flush()

    def flush(self):
        self.timer.stop()
        if not self.dirty or self.store is None or self.load_error:
            return
        with self.worker_lock:
            self.waiting.update(self.dirty)
            self.dirty.clear()
            if self.worker is not None:
                return
            # Bounded, non-daemon saving finishes when the last window closes.
            # Only a small merged map is queued, never input or clipboard data.
            self.worker = threading.Thread(target=self._save, name="spx-terminal-preferences")
            self.worker.start()

    def _save(self):
        while True:
            with self.worker_lock:
                if not self.waiting:
                    self.worker = None
                    return
                patch, self.waiting = self.waiting, {}
                reset, self.reset_pending = self.reset_pending, False
            try:
                save(self.store, patch, reset)
            except (OSError, SPXError):
                try:
                    self.error.emit("终端偏好未保存，请检查数据目录权限后重试；当前显示设置仍保留。")
                except RuntimeError:
                    pass  # The owning window has already closed.
