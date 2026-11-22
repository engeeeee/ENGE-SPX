"""Disposable owned HWND frame/Acrylic transition probe; no global input injection."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import queue
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--legacy-accent', action='store_true')
parser.add_argument('--material', choices=('acrylic', 'blur', 'mica', 'mica-alt'), default='acrylic')
args = parser.parse_args()
if os.name != 'nt':
    parser.error('requires a disposable Windows desktop')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from enge_spx.brand import APP_ID, TERMINAL_APP_ID
from enge_spx.smart_terminal import TerminalWindow, terminal_application
from enge_spx.state import Store
from enge_spx.terminal_preferences import save


class FixturePTY:
    def __init__(self): self.queue, self.writes = queue.Queue(), []
    def read(self): return self.queue.get()
    def write(self, data): self.writes.append(data)
    def resize(self, *args): pass
    def close(self): self.queue.put(b'')


app = terminal_application()
shell = ctypes.WinDLL('shell32')
get_app_id = shell.GetCurrentProcessExplicitAppUserModelID
get_app_id.argtypes, get_app_id.restype = [ctypes.POINTER(ctypes.c_wchar_p)], ctypes.c_long
app_id = ctypes.c_wchar_p()
assert get_app_id(ctypes.byref(app_id)) == 0, 'Terminal has no process taskbar identity'
try:
    assert app_id.value == TERMINAL_APP_ID and app_id.value != APP_ID
finally:
    ole = ctypes.WinDLL('ole32')
    ole.CoTaskMemFree.argtypes, ole.CoTaskMemFree.restype = [ctypes.c_void_p], None
    ole.CoTaskMemFree(app_id)
user = ctypes.WinDLL('user32', use_last_error=True)
user.GetWindow.argtypes, user.GetWindow.restype = [wintypes.HWND, wintypes.UINT], wintypes.HWND
user.GetClientRect.argtypes, user.GetClientRect.restype = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL
user.ClientToScreen.argtypes, user.ClientToScreen.restype = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)], wintypes.BOOL
user.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM, wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
user.SendMessageTimeoutW.restype = ctypes.c_ssize_t
user.WindowFromPoint.argtypes, user.WindowFromPoint.restype = [wintypes.POINT], wintypes.HWND


def pump(seconds=.02):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(.001)


def send(hwnd, message, wparam=0, lparam=0):
    result = ctypes.c_size_t()
    assert user.SendMessageTimeoutW(hwnd, message, wparam, lparam, 2, 2000, ctypes.byref(result)), 'owned HWND did not respond'
    return result.value


real_build = sys.getwindowsversion().build
context = patch('enge_spx.window_effects.sys.getwindowsversion', return_value=SimpleNamespace(build=19045)) if args.legacy_accent else __import__('contextlib').nullcontext()
with tempfile.TemporaryDirectory(prefix='spx-owned-window-') as folder, context:
    store = Store(Path(folder) / 'data')
    save(store, {'appearance': args.material, 'tint': 'purple', 'opacity': 65})
    pty = FixturePTY()
    window = TerminalWindow(pty, 'codex', Path(folder), preferences_store=store)
    try:
        window.show()
        pump()
        assert window._frame_configured
        hwnd = wintypes.HWND(int(window.winId()))
        original_hwnd = int(window.winId())
        assert not user.GetWindow(hwnd, 4), 'Terminal taskbar window has an owner'
        backend = window.backdrop_backend
        alpha = window.view.background.alpha()
        def hit(point):
            bounds = wintypes.RECT()
            assert user.GetClientRect(hwnd, ctypes.byref(bounds))
            native = wintypes.POINT(round(point.x() * bounds.right / window.width()), round(point.y() * bounds.bottom / window.height()))
            assert user.ClientToScreen(hwnd, ctypes.byref(native))
            return send(hwnd, 0x84, lparam=((native.y & 0xffff) << 16) | (native.x & 0xffff))
        title = window.titlebar.mapTo(window, window.titlebar.caption.geometry().center())
        assert hit(title) == 2, 'caption is not draggable'
        assert hit(QPoint(1, 1)) == 13, 'corner is not resizable'
        for button in window.titlebar.controls.values():
            assert hit(window.titlebar.mapTo(window, button.geometry().center())) != 2
        assert hit(window.view.mapTo(window, window.view.rect().center())) != 2
        # Dispatch only messages to this fixture HWND. The test verifies state
        # transitions, not a physical mouse drag or Windows 10 visual quality.
        send(hwnd, 0x231)
        assert window.interaction_active and window.view.background.alpha() == alpha
        durations = []
        for index in range(24):
            started = time.perf_counter()
            window.move(30 + index % 8, 30 + index % 6)
            window.resize(880 + index % 5 * 8, 580 + index % 4 * 8)
            window.view.stream.feed(f'\x1b[?2026h\x1b[HMove/resize fixture {index:03d} 中文\x1b[?2026l')
            pump(.002)
            assert window.view.background.alpha() == alpha
            durations.append((time.perf_counter() - started) * 1000)
        QTest.keyClicks(window.view, 'owned-input')
        pump()
        assert b''.join(pty.writes) == b'owned-input'
        send(hwnd, 0x232)
        pump()
        assert not window.interaction_active and int(window.winId()) == original_hwnd
        # A caption click may send SC_MOVE without entering a modal move loop.
        # Use only this owned Qt widget; no global mouse/keyboard injection.
        QTest.mouseClick(window.titlebar, Qt.MouseButton.LeftButton, pos=QPoint(window.titlebar.width() // 2, 20))
        pump(.35)
        assert not window.interaction_active, 'Caption click left material suspended'
        assert window.backdrop_backend == backend, 'Caption click did not restore material'
        assert window.preferences.value['appearance'] == args.material
        assert window.backdrop_backend == backend
        assert window.windowOpacity() == 1.0
        window.showMaximized()
        pump()
        assert window.isMaximized()
        assert hit(window.titlebar.mapTo(window, window.titlebar.caption.geometry().center())) == 2
        assert hit(QPoint(1, 1)) != 13
        window.showNormal()
        pump()
        assert hit(QPoint(1, 1)) == 13
        window.view.stream.feed('\x1b[?2026h\x1b[2J\x1b[H\x1b[38;2;229;177;148mOwned terminal rendering fixture\x1b[0m\r\n\r\nNative caption / resize / synchronized frames\r\n\x1b[32mUnicode: 中文  e\u0301  🙂\x1b[0m\x1b[?2026l')
        pump()
        # Actual owned-window pixels, synthetic content; never user clipboard.
        image = window.grab()
        caption = window.titlebar.mapTo(window, QPoint(window.titlebar.width() // 2, window.titlebar.height() // 2))
        assert image.toImage().pixelColor(round(caption.x() * image.devicePixelRatio()), round(caption.y() * image.devicePixelRatio())).alpha() > 0, 'caption pixels are click-through'
        window.raise_()
        window.activateWindow()
        pump()
        bounds = wintypes.RECT()
        assert user.GetClientRect(hwnd, ctypes.byref(bounds))
        native_caption = wintypes.POINT(round(caption.x() * bounds.right / window.width()), round(caption.y() * bounds.bottom / window.height()))
        assert user.ClientToScreen(hwnd, ctypes.byref(native_caption))
        assert int(user.WindowFromPoint(native_caption) or 0) == original_hwnd, 'caption input passes to another window'
        # Switch effects and edit opacity in the same already visible window.
        materials = {}
        for material in ('blur', 'mica', 'mica-alt'):
            window.preferences.set('appearance', material)
            materials[material] = {'backend': window.backdrop_backend, 'color': window.view.background.name()}
        assert len({result['color'] for result in materials.values()}) == 3
        if args.legacy_accent:
            assert materials['mica']['backend'] == 'mica-tint'
            assert materials['mica-alt']['backend'] == 'mica-alt-tint'
        window.show_appearance()
        pump()
        panel = window.appearance_dialog
        slider = panel.opacity
        assert slider.isEnabled()
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(1, slider.height() // 2))
        assert window.preferences.value['opacity'] == panel.percent.value() == 30
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=QPoint(1, slider.height() // 2))
        QTest.mouseMove(slider, QPoint(slider.width() - 1, slider.height() // 2))
        assert panel.percent.value() == 100 and window.preferences.value['opacity'] == 30
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(slider.width() - 1, slider.height() // 2))
        assert window.preferences.value['opacity'] == panel.percent.value() == 100
        panel.close()
        window.preferences.set('appearance', 'solid')
        assert window.view.background.alpha() == 255 and int(window.winId()) == original_hwnd
        window.preferences.set('appearance', args.material)
        window.preferences.set('opacity', 65)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        assert image.save(str(args.output.with_suffix('.png')))
        report = {'schema': 1, 'scope': 'Owned Windows HWND hit-testing, resize/maximize and move-loop messages; no physical mouse or visual acceptance',
                  'windows_build': real_build, 'requested_legacy_accent_api': args.legacy_accent, 'backend': backend, 'material': args.material,
                  'dpr': window.devicePixelRatioF(), 'caption_hit': True, 'buttons_remain_interactive': True,
                  'caption_alpha_and_window_pick': True,
                  'resize_corners': True, 'maximized_client_visible': True, 'move_loop_preserves_background_alpha': True,
                  'same_hwnd_and_input': True, 'preferences_preserved': True, 'foreground_opacity': window.windowOpacity(),
                  'process_taskbar_id': TERMINAL_APP_ID, 'top_level_hwnd_without_owner': True,
                  'material_render_colors': materials, 'opacity_track_and_drag': True,
                  'move_resize_dispatch_median_ms': round(statistics.median(durations), 3),
                  'move_resize_dispatch_p95_ms': round(sorted(durations)[int(len(durations)*.95)-1], 3),
                  'physical_windows10_drag': 'not_tested'}
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    finally:
        window.close()
        window.view.reader.join(2)
