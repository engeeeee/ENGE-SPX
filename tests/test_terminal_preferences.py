import json
import os
import queue
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

if os.name != 'nt':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from enge_spx.state import Store, SPXError
from enge_spx.terminal_preferences import DEFAULTS, FILE, Preferences, read, save, validate


class FixturePTY:
    def __init__(self):
        self.output = queue.Queue()
    def read(self):
        return self.output.get()
    def write(self, data):
        pass
    def resize(self, *args):
        pass
    def close(self):
        self.output.put(b'')


class TerminalPreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Store(Path(temp.name) / 'data')

    def test_defaults_and_independent_partial_saves_preserve_other_windows(self):
        self.assertEqual(read(self.store), DEFAULTS)
        self.assertFalse((self.store.home / FILE).exists())
        save(self.store, {'font_size': 14, 'appearance': 'acrylic'})
        with self.store.lock():
            save(self.store, {'opacity': 70, 'tint': 'purple'})
        settings = read(Store(self.store.home))
        self.assertEqual((settings['font_size'], settings['opacity'], settings['tint'], settings['appearance']), (14, 70, 'purple', 'acrylic'))

    def test_codex_live_composer_uses_terminal_background_and_preserves_history_fill(self):
        from enge_spx.smart_terminal import TerminalView
        view = TerminalView(FixturePTY(), tool='codex')
        try:
            view.resize(840, 520)
            view._resize_grid()
            columns = view.screen.columns
            shade = '\x1b[48;2;55;53;51m'
            def tinted(line, text):
                return f'\x1b[{line};1H{shade}{text.ljust(columns)}\x1b[0m'
            view.stream.feed('\x1b[?2004h' + tinted(3, '› sent message') + tinted(12, '› 中文草稿') + tinted(13, '  continued') + '\x1b[13;6H')
            view._compose_surface()
            self.assertEqual(view.painted_composer, (11, 12, '373533'))
            self.assertEqual(view.surface_rows[11][0][0].bg, 'default')
            self.assertEqual(view.surface_rows[12][0][0].bg, 'default')
            self.assertEqual(view.surface_rows[2][0][0].bg, '373533')
            self.assertEqual(view.screen.buffer[11][0].bg, '373533')
            view.stream.feed('\x1b[?2004l\x1b[12;1Hrefreshed output')
            view._compose_surface()
            self.assertIsNone(view.painted_composer)
            self.assertEqual(view.surface_rows[12][0][0].bg, '373533')
        finally:
            view.stop()
            view.reader.join(2)

    def test_parallel_terminal_processes_merge_preferences_without_proxy_configuration(self):
        code = 'import sys,json;from pathlib import Path;from enge_spx.state import Store;from enge_spx.terminal_preferences import save;save(Store(Path(sys.argv[1])),json.loads(sys.argv[2]))'
        processes = [subprocess.Popen([sys.executable, '-c', code, str(self.store.home), json.dumps(patch)])
                     for patch in ({'font_size': 15}, {'right_click_paste': False, 'tint': 'graphite'})]
        try:
            for process in processes:
                self.assertEqual(process.wait(timeout=10), 0)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=5)
        settings = read(self.store)
        self.assertEqual(settings['font_size'], 15)
        self.assertFalse(settings['right_click_paste'])
        self.assertEqual(settings['tint'], 'graphite')

    def test_corrupt_preferences_are_preserved_until_explicit_reset(self):
        original = '{invalid settings'
        (self.store.home / FILE).write_text(original)
        preferences = Preferences(self.store)
        self.assertIsNotNone(preferences.load_error)
        preferences.set('font_size', 13)
        preferences.flush()
        self.assertEqual((self.store.home / FILE).read_text(), original)
        save(self.store, {}, reset=True)
        self.assertEqual(read(self.store), DEFAULTS)
        self.assertEqual(self.store.read('terminal-preferences-previous.json')['raw_utf8'], original)

    def test_close_flushes_latest_settings_and_reports_permission_failure(self):
        preferences = Preferences(self.store)
        preferences.set('font_size', 16)
        preferences.set('opacity', 72)
        preferences.flush()
        worker = preferences.worker
        if worker:
            worker.join(3)
        self.assertEqual(read(self.store)['font_size'], 16)
        self.assertEqual(read(self.store)['opacity'], 72)
        errors = []
        preferences.error.connect(errors.append)
        with patch.object(self.store, 'write', side_effect=PermissionError('synthetic')):
            preferences.set('font_size', 17)
            preferences.flush()
            worker = preferences.worker
            if worker:
                worker.join(3)
            self.app.processEvents()
        self.assertTrue(errors)
        self.assertEqual(read(self.store)['font_size'], 16)

    def test_unknown_versions_invalid_types_and_ranges_do_not_overwrite(self):
        for patch in ({'schema': 2}, {'font_size': True}, {'opacity': 5}, {'tint': 'unsafe'}, {'tint': []}, {'appearance': {}}, {'font_family': 'x\ncmd'}):
            with self.assertRaises(SPXError):
                validate({'schema': 1, **patch})
        self.assertFalse((self.store.home / FILE).exists())

    def test_opacity_track_click_and_drag_commit_on_release(self):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest
        from enge_spx.terminal_appearance import OpacitySlider
        slider = OpacitySlider(None)
        try:
            slider.resize(240, 32)
            slider.setValue(65)
            slider.show()
            self.app.processEvents()
            left = Qt.MouseButton.LeftButton
            QTest.mouseClick(slider, left, pos=QPoint(slider.width() - 1, 16))
            self.assertEqual(slider.value(), 100)
            QTest.mousePress(slider, left, pos=QPoint(slider.width() - 8, 16))
            QTest.mouseMove(slider, QPoint(0, 16))
            self.assertEqual(slider.sliderPosition(), 30)
            self.assertEqual(slider.value(), 100)
            QTest.mouseRelease(slider, left, pos=QPoint(0, 16))
            self.assertEqual(slider.value(), 30)
            QTest.keyClick(slider, Qt.Key.Key_Right)
            self.assertEqual(slider.value(), 31)
        finally:
            slider.close()

    def test_glass_material_colors_are_distinct_at_the_same_opacity(self):
        from enge_spx.smart_terminal import TerminalView
        view = TerminalView(FixturePTY(), tool='codex')
        try:
            for tint in ('clay', 'purple', 'graphite'):
                colors = set()
                for material in ('blur', 'mica', 'mica-alt'):
                    view.apply_display({**DEFAULTS, 'tint': tint, 'appearance': material}, glass=True)
                    self.assertEqual(view.background.alpha(), round(DEFAULTS['opacity'] * 2.55))
                    colors.add(view.background.name())
                self.assertEqual(len(colors), 3)
        finally:
            view.stop()
            view.reader.join(2)

    def test_reopening_product_window_restores_display_and_mouse_preferences(self):
        from enge_spx.smart_terminal import TerminalWindow
        first = TerminalWindow(FixturePTY(), 'codex', self.store.home, preferences_store=self.store)
        try:
            first.show()
            self.app.processEvents()
            for name, value in {'font_size': 15, 'tint': 'purple', 'appearance': 'acrylic', 'opacity': 68,
                                'copy_on_select': False, 'right_click_paste': False}.items():
                first.preferences.set(name, value)
            first.close()
            worker = first.preferences.worker
            if worker:
                worker.join(3)
            first.view.reader.join(2)
            second = TerminalWindow(FixturePTY(), 'codex', self.store.home, preferences_store=self.store)
            try:
                second.show()
                self.app.processEvents()
                self.assertEqual(second.view.font.pointSize(), 15)
                from PySide6.QtCore import Qt
                self.assertTrue(second.titlebar.testAttribute(Qt.WidgetAttribute.WA_StyledBackground))
                self.assertEqual(second.view.background.name(), '#302034')
                self.assertIn('#44304d', second.styleSheet())
                second.preferences.set('tint', 'graphite')
                self.app.processEvents()
                self.assertEqual(second.view.background.name(), '#1d252c')
                self.assertIn('#2f3e4b', second.styleSheet())
                self.assertFalse(second.view.copy_on_select)
                self.assertFalse(second.view.right_click_paste)
                self.assertEqual(second.preferences.value['opacity'], 68)
                self.assertEqual(second.translucent_surface, os.name == 'nt')
                self.assertIn(second.backdrop_backend, ('system-acrylic', 'accent-acrylic', 'solid', 'unsupported', 'system-disabled'))
                self.assertEqual(second.windowOpacity(), 1.0)
            finally:
                second.close()
                worker = second.preferences.worker
                if worker:
                    worker.join(3)
                second.view.reader.join(2)
        finally:
            first.close()
            first.view.reader.join(2)

    @unittest.skipUnless(os.name == 'nt', 'requires an owned native Windows window')
    def test_windows_backdrop_can_be_disabled_without_changing_foreground_opacity(self):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QWidget
        from enge_spx.window_effects import apply_acrylic
        window = QWidget()
        window.show()
        self.app.processEvents()
        try:
            self.assertIn(apply_acrylic(window, QColor('#302034'), True),
                          ('system-acrylic', 'accent-acrylic', 'unsupported', 'system-disabled'))
            self.assertIn(apply_acrylic(window, QColor('#302034'), False), ('solid', 'unsupported'))
            self.assertEqual(window.windowOpacity(), 1.0)
        finally:
            window.close()
