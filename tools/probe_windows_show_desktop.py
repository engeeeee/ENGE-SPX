"""Exercise Show Desktop and restore one native window on a disposable Windows desktop."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import time

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from enge_spx.state import Store
from enge_spx.ui.controller import Controller
from enge_spx.ui.window import Window


class IdlePTY:
    def __init__(self):
        self.output = queue.Queue()

    def read(self):
        return self.output.get()

    def write(self, data):
        pass

    def resize(self, *size):
        pass

    def close(self):
        self.output.put(b"")


def wait_for(condition, error):
    end = time.monotonic() + 8
    while not condition():
        assert time.monotonic() < end, error
        QTest.qWait(30)


def main():
    if os.name != "nt":
        raise SystemExit("This probe requires an interactive Windows Explorer desktop.")
    user = ctypes.WinDLL("user32")
    user.GetShellWindow.restype = wintypes.HWND
    user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user.GetWindowLongW.restype = ctypes.c_long
    user.IsIconic.argtypes = [wintypes.HWND]
    user.IsIconic.restype = wintypes.BOOL
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    assert user.GetShellWindow(), "Explorer desktop is unavailable"

    app = QApplication([])
    with tempfile.TemporaryDirectory(prefix="spx-show-desktop-") as path:
        controller = Controller(Store(Path(path) / "data"))
        workbench = Window(controller)
        workbench.show()
        session = workbench.terminal_sessions().open(IdlePTY(), "shell", Path(path))
        terminal = session.window()
        assert terminal.taskbar_group_set, "Terminal taskbar grouping was not configured"
        QTest.qWait(200)
        main_hwnd, term_hwnd = int(workbench.winId()), int(terminal.winId())
        toggle = None
        try:
            # WS_MINIMIZEBOX lets Explorer actually minimize the main window.
            assert user.GetWindowLongW(main_hwnd, -16) & 0x20000
            assert not user.GetWindowLongW(main_hwnd, -16) & 0xC00000
            assert not user.IsIconic(main_hwnd) and not user.IsIconic(term_hwnd)
            toggle = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 "$ErrorActionPreference = 'Stop'; (New-Object -ComObject Shell.Application).ToggleDesktop()"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            wait_for(lambda: toggle.poll() is not None, "Show Desktop command did not finish")
            assert toggle.returncode == 0, "Explorer rejected Show Desktop"
            wait_for(lambda: user.IsIconic(main_hwnd) and user.IsIconic(term_hwnd),
                     "Show Desktop left either window in normal state")
            # Selectively restore the terminal HWND, as a single taskbar entry does.
            user.ShowWindow(term_hwnd, 9)  # SW_RESTORE
            wait_for(lambda: not user.IsIconic(term_hwnd), "Terminal did not restore")
            controller.update_stage({"stage": "docker_start"})
            controller.update_stage({"stage": "docker_ready"})
            QTest.qWait(300)
            assert user.IsIconic(main_hwnd) and workbench.isMinimized(), "Workbench restored with the terminal"
            workbench.reveal()
            wait_for(lambda: not user.IsIconic(main_hwnd), "Direct workbench restore failed")
            print("PASS Explorer Show Desktop, selective terminal restore, and independent workbench restore")
        finally:
            if toggle is not None and toggle.poll() is None:
                toggle.terminate()
                toggle.wait(timeout=5)
            terminal.close()
            terminal.view.reader.join(2)
            workbench.finish_close()


if __name__ == "__main__":
    main()
