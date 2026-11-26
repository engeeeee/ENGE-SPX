"""Windows shell integration, kept separate from the portable control plane."""
import ctypes
import hashlib
import os
from pathlib import Path
import time

from .brand import APP_ID, ICONS as ASSETS, LEGACY_APP_ID, TERMINAL_APP_ID


def restore_message():
    """A show-only request handled by Qt in the owning GUI process."""
    if os.name != "nt":
        return 0
    user = ctypes.windll.user32
    user.RegisterWindowMessageW.argtypes = [ctypes.c_wchar_p]
    user.RegisterWindowMessageW.restype = ctypes.c_uint
    return user.RegisterWindowMessageW(APP_ID + ".RestoreWindow")


def prepare_windows(dpi=True, *, app_id=APP_ID):
    if os.name != "nt":
        return
    try:
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        set_app_id(app_id)
    except (AttributeError, OSError):
        pass
    if not dpi:
        return  # Qt manages per-monitor DPI for the native desktop interface.
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


def set_terminal_window_app_id(hwnd, *, enabled=True):
    """Set or clear a terminal's Explorer taskbar group on its own HWND."""
    if os.name != "nt":
        return False
    from ctypes import wintypes
    from uuid import UUID

    class GUID(ctypes.Structure):
        _fields_ = [("data", ctypes.c_ubyte * 16)]

    class PropertyKey(ctypes.Structure):
        _fields_ = [("guid", GUID), ("pid", wintypes.DWORD)]

    class Value(ctypes.Union):
        _fields_ = [("text", ctypes.c_wchar_p), ("storage", ctypes.c_void_p * 2)]

    class PropVariant(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ushort), ("reserved", ctypes.c_ushort * 3), ("value", Value)]

    iid = GUID.from_buffer_copy(UUID("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99").bytes_le)
    app_id_key = PropertyKey(GUID.from_buffer_copy(UUID("9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3").bytes_le), 5)
    store = ctypes.c_void_p()
    try:
        get_store = ctypes.windll.shell32.SHGetPropertyStoreForWindow
        get_store.argtypes = [wintypes.HWND, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
        get_store.restype = ctypes.c_long
        if get_store(hwnd, ctypes.byref(iid), ctypes.byref(store)) < 0 or not store.value:
            return False
        methods = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        release = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(methods[2])
        try:
            set_value = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PropertyKey),
                                          ctypes.POINTER(PropVariant))(methods[6])
            value = PropVariant()
            if enabled:
                value.type = 31  # VT_LPWSTR; zero-initialized VT_EMPTY clears the property.
                value.value.text = TERMINAL_APP_ID
            return set_value(store, ctypes.byref(app_id_key), ctypes.byref(value)) >= 0
        finally:
            release(store)
    except (AttributeError, OSError):
        return False


class WindowInstance:
    def __init__(self, home, legacy=False):
        self.handle = None
        self.hwnd = None
        identity = LEGACY_APP_ID if legacy else APP_ID
        self.key = identity + "." + hashlib.sha256(os.path.normcase(str(home)).encode()).hexdigest()[:16]

    def acquire(self):
        if os.name != "nt":
            return True
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        ctypes.set_last_error(0)
        self.handle = kernel.CreateMutexW(None, False, "Local\\" + self.key)
        if not self.handle:
            return True
        if ctypes.get_last_error() != 183:
            return True
        user = ctypes.windll.user32
        user.GetPropW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        user.GetPropW.restype = ctypes.c_void_p
        user.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user.SetForegroundWindow.argtypes = [ctypes.c_void_p]
        user.SendMessageTimeoutW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_size_t)]
        user.SendMessageTimeoutW.restype = ctypes.c_void_p
        message = restore_message()
        callback = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found = []
        def visit(hwnd, _):
            if user.GetPropW(hwnd, self.key):
                found.append(hwnd)
                result = ctypes.c_size_t()
                acknowledged = message and user.SendMessageTimeoutW(hwnd, message, 0, 0, 2, 1000, ctypes.byref(result)) and result.value == 1
                if not acknowledged:
                    # Compatibility with an already running pre-0.10 GUI. New
                    # versions restore through QWidget, including its internal
                    # visibility state and resource/shortcut event handling.
                    user.ShowWindow(hwnd, 9)
                user.SetForegroundWindow(hwnd)
                return False
            return True
        for _ in range(15):
            user.EnumWindows(callback(visit), 0)
            if found:
                break
            time.sleep(.1)
        self.close()
        return False

    def register_hwnd(self, hwnd):
        if os.name == "nt":
            user = ctypes.windll.user32
            user.SetPropW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_void_p]
            if user.SetPropW(hwnd, self.key, ctypes.c_void_p(1)):
                self.hwnd = hwnd

    def close(self):
        if self.hwnd:
            remove = ctypes.windll.user32.RemovePropW
            remove.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
            remove.restype = ctypes.c_void_p
            remove(self.hwnd, self.key)
            self.hwnd = None
        if self.handle:
            kernel = ctypes.windll.kernel32
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle(self.handle)
            self.handle = None
