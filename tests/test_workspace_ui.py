import os
from pathlib import Path
import queue
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

if os.name != "nt":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton
from enge_spx import ssh_machines
from enge_spx.engine import Engine
from enge_spx.state import Store
from enge_spx.ui.controller import Controller
from enge_spx.ui.window import Window
from enge_spx.workspace_profiles import FILE


class WorkspaceUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "data")
        self.project = self.root / "project"
        self.project.mkdir()
        self.identity = Engine(self.store).create_workspace_profile("独立身份")["profile"]
        self.controller = Controller(self.store)
        self.controller.project.set(str(self.project))
        self.window = Window(self.controller)
        self.window.show()
        self.window.show_page("workspace")
        self.addCleanup(self.window.finish_close)

    def wait(self):
        for _ in range(100):
            QTest.qWait(20)
            time.sleep(.005)
            if not self.controller.busy:
                return
        self.fail("Workspace operation did not finish")

    def test_antigravity_launch_has_no_download_caption(self):
        labels = [item.text() for item in self.window.findChildren(QLabel)]
        buttons = [item.text() for item in self.window.findChildren(QPushButton) if item.isVisible()]
        self.assertNotIn("Antigravity 首次打开时通过工作区代理下载安装。", labels)
        self.assertTrue(any(text.startswith("Antigravity CLI") for text in buttons))

    def test_runtime_download_progress_survives_restart_and_preserves_pause_status(self):
        c = self.controller
        c.events.put(("app_update_progress", {"message": "软件更新", "progress": 12}))
        c.preparation_progress({"stage": "manifest"})
        c.drain()
        self.assertEqual(c.download_title.get(), "获取运行环境信息")
        self.assertEqual(c.download_progress.get(), -1)
        self.assertEqual(c.update_progress.get(), 12)

        c.preparation_progress({"stage": "download", "bytes": 750, "total": 1000, "speed": 500, "eta": .5})
        c.events.put(("paused", "下载已暂停，可继续。"))
        c.drain()
        self.assertEqual(c.download_progress.get(), 75)
        self.assertEqual(c.download_title.get(), "已暂停，可继续")
        self.assertEqual(c.download_detail.get(), "下载已暂停，可继续。")
        self.assertEqual(c.update_progress.get(), 12)

        for stage in ("manifest", "verify", "import", "done"):
            c.preparation_progress({"stage": stage})
        c.drain()
        self.assertEqual(c.download_progress.get(), 100)
        self.assertEqual(c.download_title.get(), "运行环境已安装")

    def test_ssh_launcher_opens_own_terminal_without_workspace_and_closes_it(self):
        output = queue.Queue()
        pty = Mock()
        pty.read.side_effect = output.get
        pty.close.side_effect = lambda: output.put(b"")

        def accept(dialog):
            dialog.host.setText("example.invalid")
            dialog.username.setText("operator")
            dialog.accept()
            return dialog.result()

        self.assertFalse(self.controller.docker_ready)
        self.window.nav["ssh"].click()
        page = self.window.pages["ssh"]
        with patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", accept), \
                patch("enge_spx.ssh_client.executable", return_value="system-ssh"), \
                patch("enge_spx.terminal_pty.start", return_value=pty) as start, \
                patch.object(self.controller, "run") as run:
            page.quick_connect.click()
        run.assert_not_called()
        self.assertEqual(start.call_args.args[0][-6:], ["-l", "operator", "-p", "22", "--", "example.invalid"])
        session, = self.window.terminal_workspace.sessions
        self.assertTrue(session.isVisible())
        self.assertEqual(session.findChild(QLabel, "ProjectName").text(), "operator@example.invalid:22")
        reader = session.view.reader
        self.window.finish_close()
        reader.join(2)
        self.assertFalse(reader.is_alive())
        pty.close.assert_called_once()
        self.assertFalse((self.store.home / ssh_machines.FILE).exists())

    def test_prepared_workspace_terminal_joins_the_current_terminal_group(self):
        from test_terminal_rendering import FixturePTY

        remote = self.window.terminal_sessions().open(FixturePTY(), "ssh", self.project, session_label="远端测试")
        launch = Mock(project=self.project, tool="antigravity", transfer=None, browser_url=None)
        launch.start.return_value = FixturePTY()
        self.controller.terminal_prepared.emit(launch)
        launch.start.assert_called_once_with()
        group = self.window.terminal_workspace.group
        self.assertIs(remote.window(), group)
        self.assertEqual([session.view.tool for session in group.sessions], ["ssh", "antigravity"])
        self.assertIs(group.view.pty, launch.start.return_value)

    def test_dedicated_ssh_page_saves_edits_connects_and_removes_machine(self):
        from enge_spx.credentials import CredentialCodec
        from test_credentials import MemoryProtector

        self.store.credentials = CredentialCodec(self.store.instance, MemoryProtector())
        self.window.nav["ssh"].click()
        page = self.window.pages["ssh"]
        self.assertEqual(self.window.current_page, "ssh")
        self.assertTrue(page.empty.isVisible())

        def create(dialog):
            dialog.name.setText("开发机")
            dialog.host.setText("ssh.example.invalid")
            dialog.username.setText("operator")
            dialog.port.setValue(2200)
            self.assertTrue(dialog.password.isEnabled())
            self.assertEqual(dialog.password.echoMode(), dialog.password.EchoMode.Password)
            dialog.password.setText("fixture-only")
            dialog.accept()
            self.assertEqual(dialog.password.text(), "")
            return dialog.result()

        with patch("enge_spx.ui.ssh_dialog.password_available", return_value=True), \
                patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", create):
            page.add_machine.click()
        saved = page.selected()
        self.assertEqual(saved.title, "开发机")
        self.assertEqual(page.address.text(), "operator@ssh.example.invalid:2200")
        self.assertEqual(ssh_machines.load(Store(self.store.home))[saved.id], saved)
        self.window.show_page("overview")
        self.window.nav["ssh"].click()
        with patch.object(self.window, "launch_ssh") as launch, \
                patch("enge_spx.ssh_askpass.password_available", return_value=True), \
                patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", side_effect=AssertionError("unexpected edit form")):
            page.list.itemActivated.emit(page.list.currentItem())
            launch.assert_called_once_with(saved.connection, "开发机 · operator@ssh.example.invalid:2200",
                                           password=bytearray(b"fixture-only"))
        self.assertNotIn("fixture-only", (self.store.home / ssh_machines.FILE).read_text(encoding="utf-8"))
        with patch.object(self.window, "launch_sftp") as files, \
                patch("enge_spx.ssh_askpass.password_available", return_value=True), \
                patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", side_effect=AssertionError("unexpected edit form")):
            page.files_selected()
            files.assert_called_once_with(saved.connection, password=bytearray(b"fixture-only"))

        def edit(dialog):
            self.assertEqual(dialog.host.text(), "ssh.example.invalid")
            self.assertEqual(dialog.auth.currentData(), "password")
            dialog.name.setText("测试机")
            self.assertEqual(dialog.password.text(), "")
            dialog.clear_password.setChecked(True)
            dialog.accept()
            return dialog.result()

        with patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", edit):
            page.edit_selected()
        self.assertEqual(page.selected().id, saved.id)
        self.assertEqual(page.selected().name, "测试机")
        self.assertFalse(page.selected().has_password)
        with patch.object(self.window, "launch_ssh") as launch, \
                patch("enge_spx.ui.ssh_dialog.SSHDialog.exec", side_effect=AssertionError("unexpected edit form")):
            page.connect_selected()
            launch.assert_called_once_with(saved.connection, "测试机 · operator@ssh.example.invalid:2200", password=None)
        with patch.object(self.controller, "ask", return_value=True):
            page.remove_selected()
        self.assertTrue(page.empty.isVisible())
        self.assertEqual(ssh_machines.load(self.store), {})

    def test_selection_does_not_mutate_or_launch_and_apply_captures_identity(self):
        c = self.controller
        box = self.window.workspace_profile_box
        box.setCurrentIndex(box.findData(self.identity))
        c.workspace_access.set("ro")
        self.assertEqual(self.store.read(FILE)["selected"], "shared")
        self.assertFalse(c.workspace_selection_matches())
        with patch.object(c, "notify") as notice, patch.object(c, "run") as run:
            c.open_terminal("codex")
            notice.assert_called_once()
            run.assert_not_called()
        c.apply_workspace()
        self.wait()
        self.assertEqual(self.store.read(FILE)["selected"], self.identity)
        self.assertTrue(c.workspace_selection_matches())
        c.settings_match = Mock(return_value=True)
        with patch.object(c, "run") as run:
            c.open_terminal("codex")
            engine = Mock()
            run.call_args.args[0](engine)
        engine.terminal.assert_called_once_with(str(self.project.resolve()), "codex", expected_workspace=(self.identity, "ro"),
                                                desktop_session=True)

    def test_expired_review_offers_a_fresh_connection_check(self):
        c = self.controller
        c.runtime_ok = c.docker_ready = True
        c.nodes = [{"id": "landing", "outbound": {"type": "socks", "server": "192.0.2.1", "server_port": 1080}}]
        c.selected.set("landing")
        c.settings_match = Mock(return_value=True)
        c.ask = Mock(return_value=True)
        self.store.write("runtime.json", {"phase": "review", "checked": time.time() - 301})
        c.refresh()
        self.assertFalse(c.view["can_confirm"])
        self.assertEqual(c.view["next_text"], "启动并检查连接")
        with patch.object(c, "prepare") as prepare, patch.object(c, "run") as run:
            c.next_step()
            c.confirm()
        prepare.assert_called_once_with()
        c.ask.assert_not_called()
        run.assert_not_called()

    def test_review_expiring_while_the_confirmation_dialog_is_open_is_not_submitted(self):
        c = self.controller
        c.settings_match = Mock(return_value=True)
        self.store.write("runtime.json", {"phase": "review", "checked": time.time()})

        def expire_while_open(title, text):
            self.store.write("runtime.json", {"phase": "review", "checked": time.time() - 301})
            return True

        c.ask = Mock(side_effect=expire_while_open)
        with patch.object(c, "run") as run:
            c.confirm()
        c.ask.assert_called_once()
        run.assert_not_called()

    def test_another_project_requires_explicit_binding_and_never_inherits_accounts(self):
        c = self.controller
        c.workspace_profile.set(self.identity)
        c.workspace_access.set("ro")
        c.apply_workspace()
        self.wait()
        other = self.root / "second"
        other.mkdir()
        c.project.set(str(other))
        self.assertEqual(c.workspace_profile.get(), self.identity)
        self.assertFalse(c.workspace_selection_matches())
        self.assertIn("待应用", c.workspace_status.get())

    def test_readwrite_requires_explicit_apply_and_create_stays_pending(self):
        c = self.controller
        c.workspace_profile.set(self.identity)
        c.workspace_access.set("ro")
        c.apply_workspace()
        self.wait()
        c.workspace_access.set("rw")
        self.assertFalse(c.workspace_selection_matches())
        self.assertEqual(next(iter(self.store.read(FILE)["projects"].values()))["access"], "ro")
        c.create_workspace("另一身份")
        self.wait()
        self.assertNotEqual(c.workspace_profile.get(), self.identity)
        self.assertEqual(self.store.read(FILE)["selected"], self.identity)
        self.assertEqual(c.workspace_access.get(), "ro")

    def test_unavailable_config_has_no_shared_fallback_in_gui(self):
        self.store.write(FILE, None)
        controller = Controller(self.store)
        window = Window(controller)
        self.addCleanup(window.finish_close)
        window.show_page("workspace")
        self.assertIsNone(controller.workspace_config)
        self.assertEqual(window.workspace_profile_box.currentData(), "")
        self.assertFalse(controller.workspace_selection_matches())

    def test_editing_project_path_does_not_resolve_or_probe_network_share(self):
        with patch.object(self.store, "project", side_effect=AssertionError("GUI keystroke resolved a path")):
            self.controller.project.set("\\\\server\\share\\project")
            self.controller.project.set("D:\\new project")

    def test_browser_uses_captured_profile_and_never_an_unapplied_choice(self):
        c = self.controller
        c.workspace_profile.set(self.identity)
        with patch.object(c, "notify"), patch.object(c, "run") as run:
            self.assertFalse(c.open_workspace_browser())
            run.assert_not_called()
        c.workspace_profile.set("shared")
        with patch.object(c, "run") as run:
            c.open_workspace_browser()
            c.workspace_profile.set(self.identity)
            engine = Mock()
            run.call_args.args[0](engine)
        engine.browser.assert_called_once_with(expected_profile="shared")

    def test_create_dialog_reaches_real_worker_without_automatically_switching(self):
        def submit():
            dialog = self.app.activeModalWidget()
            dialog.findChild(QLineEdit).setText("从窗口创建")
            next(item for item in dialog.findChildren(QPushButton) if item.text() == "仅创建").click()
        QTimer.singleShot(30, submit)
        self.window.new_workspace_profile()
        self.wait()
        self.assertIn("从窗口创建", self.controller.workspace_config["profiles"].values())
        self.assertEqual(self.store.read(FILE)["selected"], "shared")
        self.assertFalse(self.controller.workspace_selection_matches())

    def test_create_and_switch_clears_other_projects_and_switch_back_restores_grant(self):
        c = self.controller
        engine = Engine(self.store)
        engine.configure_workspace('shared', str(self.project), 'rw')
        engine.remember_project(self.project.resolve())
        self.assertTrue(c.create_workspace('空白工作区', activate=True))
        self.wait()
        new = self.store.read(FILE)['selected']
        self.assertNotEqual(new, 'shared')
        self.assertEqual(c.project.get(), '')
        self.assertEqual(self.window.workspace_recent_box.count(), 1)
        self.assertFalse(c.workspace_selection_matches())
        c.project.set(str(self.project))
        self.assertEqual(c.workspace_profile.get(), new)
        self.assertFalse(c.workspace_selection_matches(), 'An old project does not apply an old identity')
        c.workspace_profile.set('shared')
        self.assertTrue(c.switch_workspace())
        self.wait()
        self.assertEqual(c.project.get(), str(self.project.resolve()))
        self.assertTrue(c.workspace_selection_matches())

    def test_network_page_is_lazy_readonly_and_exports_the_observed_report(self):
        c = self.controller
        with patch("enge_spx.engine.Docker.run", side_effect=AssertionError("Opening a page queried Docker")):
            self.window.show_page("network")
            QTest.qWait(30)
        self.assertIsNone(c.network_report)
        report = {"schema": 1, "status": "partial", "objects": {"browser": {"status": "not_running"}}}
        with patch("enge_spx.engine.Engine.network_diagnostics", return_value=report):
            c.check_network()
            self.wait()
        self.assertEqual(c.network_report, report)
        self.assertIn("部分检查", c.network_summary.get())
        target = self.root / "network-report.json"
        c.export_network_report(target)
        self.wait()
        import json
        self.assertEqual(json.loads(target.read_text()), report)


if __name__ == "__main__":
    unittest.main()
