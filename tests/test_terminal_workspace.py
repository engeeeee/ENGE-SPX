import os
from pathlib import Path
import tempfile
import unittest

if os.name != "nt":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from enge_spx.state import Store
from enge_spx.terminal_workspace import TerminalWorkspace
from test_terminal_rendering import FixturePTY


class TerminalWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.workspace = TerminalWorkspace(Store(self.root / "data"))
        self.readers = []

    def tearDown(self):
        self.workspace.close()
        for reader in self.readers:
            reader.join(2)
            self.assertFalse(reader.is_alive())
        self.app.processEvents()

    def open(self, tool, name):
        session = self.workspace.open(FixturePTY(), tool, self.root / name, session_label=name)
        self.readers.append(session.view.reader)
        self.app.processEvents()
        return session

    def test_sidebar_selection_uses_the_terminal_palette(self):
        self.open("ssh", "构建服务器")
        sidebar = self.workspace.group.sidebar

        def selection_color():
            return sidebar.palette().color(QPalette.ColorRole.Highlight)

        default = selection_color()
        self.workspace.preferences.set("tint", "purple")
        self.assertNotEqual(selection_color(), default)
        self.workspace.preferences.set("color_selection_background", "#702e3a")
        self.assertEqual(selection_color(), QColor("#702e3a"))
        item = sidebar.visualItemRect(sidebar.currentItem())
        image = sidebar.viewport().grab()
        point = item.topLeft() + QPoint(5, item.height() // 2)
        self.assertEqual(image.toImage().pixelColor(point * image.devicePixelRatio()), selection_color())

    def test_ssh_and_workspace_switch_detach_and_rejoin_the_same_views(self):
        local = self.open("antigravity", "开发项目")
        remote = self.open("ssh", "构建服务器")
        group = self.workspace.group
        self.assertIs(local.window(), group)
        self.assertIs(remote.window(), group)
        self.assertEqual(group.sidebar.count(), 2)
        self.assertTrue(group.sidebar.isVisible())
        self.assertIs(group.view, remote.view)
        if os.name == "nt":
            self.assertTrue(group.taskbar_group_set)

        first_button = group.sidebar.visualItemRect(group.sidebar.item(0)).center()
        QTest.mouseClick(group.sidebar.viewport(), Qt.MouseButton.LeftButton, pos=first_button)
        self.assertIs(group.view, local.view)
        local.view.stream.feed("local draft")
        remote.view.stream.feed("remote transcript")

        group.sidebar_button.click()
        self.assertFalse(group.sidebar.isVisible())
        self.assertIs(group.view, local.view)
        group.sidebar_button.click()
        self.assertTrue(group.sidebar.isVisible())

        local.detach_button.click()
        detached = local.window()
        self.assertIsNot(detached, group)
        self.assertTrue(detached.isVisible() and group.isVisible())
        if os.name == "nt":
            self.assertTrue(detached.taskbar_group_set)
        self.assertIs(group.view, remote.view)
        self.assertIn("local draft", local.view.screen.display[0])
        self.assertIn("remote transcript", remote.view.screen.display[0])
        self.assertFalse(local.view.stopping.is_set())
        self.assertFalse(remote.view.stopping.is_set())

        local.detach_button.click()
        self.assertIs(local.window(), group)
        self.assertIs(group.view, local.view)
        self.assertEqual(self.workspace.windows, {group})
        self.assertEqual(group.sidebar.count(), 2)

    def test_detaching_only_session_can_create_a_group_again(self):
        session = self.open("ssh", "测试主机")
        previous_group = self.workspace.group
        emptied = QSignalSpy(self.workspace.emptied)
        session.detach_button.click()
        detached = session.window()
        self.assertIsNone(self.workspace.group)
        self.assertEqual(self.workspace.windows, {detached})
        self.assertFalse(previous_group.isVisible())
        self.assertEqual(emptied.count(), 0)

        session.detach_button.click()
        self.assertIs(session.window(), self.workspace.group)
        self.assertTrue(session.isVisible())
        self.assertEqual(emptied.count(), 0)

    def test_keeping_workspace_closes_only_ssh_and_finishes_after_local_closes(self):
        local = self.open("codex", "项目")
        remote = self.open("ssh", "主机")
        emptied = QSignalSpy(self.workspace.emptied)
        self.workspace.close(keep_workspace=True)
        self.assertEqual(self.workspace.sessions, (local,))
        self.assertFalse(local.view.stopping.is_set())
        self.assertTrue(remote.view.stopping.is_set())
        self.assertEqual(emptied.count(), 0)
        self.workspace.close_session(local)
        self.assertEqual(emptied.count(), 1)
