import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

if os.name != 'nt':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QApplication
from enge_spx.state import Store
from enge_spx.ui.controller import Controller
from enge_spx.ui.window import Window


class UpdateUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        self.c = Controller(self.store)
        self.w = Window(self.c)
        self.w.show_page('settings')
        self.addCleanup(self.w.finish_close)

    def spin(self, condition):
        end = time.monotonic() + 4
        while not condition() and time.monotonic() < end:
            QTest.qWait(15)
            time.sleep(.005)
        self.assertTrue(condition())

    def test_manual_check_updates_page_without_starting_docker(self):
        with patch('enge_spx.app_updates.check', return_value={'version': '1.2.3'}), patch('enge_spx.engine.Engine.doctor') as doctor:
            self.c.check_updates()
            self.spin(lambda: not self.c.busy)
        self.assertTrue(self.c.update_available.get())
        self.assertIn('1.2.3', self.c.update_status.get())
        doctor.assert_not_called()
        self.assertEqual(self.c.timezone_mode.get(), 'exit')

    def test_update_waits_for_verified_workspace_stop_before_helper_and_close(self):
        order = []
        self.c.update_release = {'version': '1.2.3'}
        self.c.ask = lambda *args: True
        engine = Mock(store=self.store)
        engine.shutdown.side_effect = lambda: (order.append('stop') or {'workspace_stopped': True, 'background_stopped': True})
        closed = QSignalSpy(self.c.close_requested)
        self.c.close_requested.connect(lambda: order.append('close'))
        with patch('enge_spx.ui.controller.Engine', return_value=engine), patch('enge_spx.app_updates.application_directory', return_value=self.root), patch('enge_spx.app_updates.prepare', side_effect=lambda *args: (order.append('prepare') or self.root / 'plan.json')), patch('enge_spx.app_updates.launch_helper', side_effect=lambda *args: order.append('helper')):
            self.c.install_update()
            self.spin(lambda: closed.count() == 1)
        self.assertEqual(order, ['prepare', 'stop', 'helper', 'close'])
        self.assertTrue(self.c.exit_skip_desktop)

    def test_timezone_options_show_chinese_and_submit_valid_mode_values(self):
        box = self.w.timezone_mode_box
        self.assertEqual([(box.itemText(i), box.itemData(i)) for i in range(box.count())],
                         [('跟随落地出口', 'exit'), ('手动固定', 'manual')])
        self.assertEqual(box.currentData(), 'exit')
        box.setCurrentIndex(1)
        self.assertEqual(self.c.captured_settings()[4], 'manual')
        box.setCurrentIndex(0)
        self.assertEqual(self.c.captured_settings()[4], 'exit')

    def test_startup_accepts_new_exit_timezone_before_confirmation_without_losing_pending_edits(self):
        from enge_spx.nodes import uri_node
        node = uri_node('socks5://192.0.2.10:1080#fixture')
        settings = {**self.store.settings(), 'selected': node['id'], 'relay': {'enabled': False, 'downloads': False}}
        self.store.write('nodes.json', [node])
        self.store.write('settings.json', settings)
        self.c.refresh_nodes()
        evidence = {'ip': '203.0.113.10', 'timezone': 'Asia/Tokyo', 'country': 'Japan', 'city': 'Fixture'}
        engine = Mock(store=self.store)
        engine.policy.return_value = 'fixture-policy'
        def check():
            self.store.write('settings.json', {**self.store.settings(), 'timezone': 'Asia/Tokyo'})
            self.store.write('runtime.json', {'phase': 'review', 'checked': time.time(), 'evidence': evidence})
            return evidence
        def confirm():
            self.store.write('runtime.json', {'phase': 'ready', 'evidence': evidence, 'policy': 'fixture-policy', 'heartbeat': time.time()})
            return evidence
        engine.check.side_effect, engine.confirm.side_effect = check, confirm
        self.c.ask = Mock(return_value=True)
        with patch('enge_spx.ui.controller.Engine', return_value=engine), patch('enge_spx.startup.ensure_docker', return_value={'docker': '29.0', 'architecture': 'x86_64'}):
            self.c.prepare()
            self.spin(lambda: not self.c.busy and self.store.read('runtime.json', {}).get('phase') == 'ready')
        engine.confirm.assert_called_once()
        self.assertEqual(self.c.timezone.get(), 'Asia/Tokyo')
        self.assertIn('Asia/Tokyo', self.c.ask.call_args.args[1])
        self.assertTrue(self.c.view['ready'])
        self.c.timezone_mode.set('manual')
        self.c.timezone.set('Europe/London')
        self.c.prepared({'phase': 'prepared', 'docker': {'docker': '29', 'architecture': 'x86_64'}, 'runtime': True})
        self.assertEqual(self.c.timezone.get(), 'Europe/London')
