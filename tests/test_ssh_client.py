import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from enge_spx import ssh_machines
from enge_spx.ssh_client import Connection, environment
from enge_spx.state import SPXError, Store


class SSHClientTests(unittest.TestCase):
    @patch("enge_spx.ssh_client.executable", return_value="system-ssh")
    def test_password_uses_open_ssh_prompt_and_checks_host_key(self, _executable):
        connection = Connection.from_fields(" [2001:db8::1] ", " operator ", 2222)
        self.assertEqual(connection.label, "operator@[2001:db8::1]:2222")
        command = connection.command()
        self.assertEqual(command[:4], ["system-ssh", "-F", "none", "-tt"])
        self.assertEqual(command[-6:], ["-l", "operator", "-p", "2222", "--", "2001:db8::1"])
        self.assertIn("StrictHostKeyChecking=ask", command)
        self.assertIn("PreferredAuthentications=password,keyboard-interactive", command)
        self.assertIn("PubkeyAuthentication=no", command)

    @patch("enge_spx.ssh_client.executable", return_value="system-ssh")
    def test_private_key_uses_selected_path_without_other_identities(self, _executable):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "测试 SSH key 100%.pem"
            path.touch()
            connection = Connection.from_fields("BÜCHER.example", "operator", 22, path)
            command = connection.command()
            option = path.as_posix().replace("%", "%%")
            self.assertEqual(connection.host, "xn--bcher-kva.example")
            self.assertIn(f'IdentityFile="{option}"', command)
            self.assertIn("IdentitiesOnly=yes", command)
            self.assertIn("IdentityAgent=none", command)
            self.assertIn("PreferredAuthentications=publickey", command)

    def test_rejects_invalid_connection_fields(self):
        for host in ("-oProxyCommand=x", "ssh://example.org", "name@example.org", "example.org:22", "fe80::1%bad zone"):
            with self.subTest(host=host), self.assertRaises(SPXError):
                Connection.from_fields(host, "operator", 22)
        for username, port, key in (("user\nname", 22, None), ("", 22, None), ("operator", 0, None),
                                    ("operator", True, None), ("operator", 22, ""), ("operator", 22, "missing-key")):
            with self.subTest(username=username, key=key, port=port), self.assertRaises(SPXError):
                Connection.from_fields("example.invalid", username, port, key)

    def test_environment_passes_system_values_and_drops_unrelated_credentials(self):
        with patch.dict(os.environ, {"PATH": "fixture", "HOME": "fixture", "PROGRAMDATA": "system-fixture",
                                     "SPX_BROWSER_TOKEN": "synthetic", "SSH_ASKPASS": "synthetic",
                                     "SSH_AUTH_SOCK": "synthetic", "HTTPS_PROXY": "synthetic"}, clear=True):
            self.assertEqual(environment(), {"PATH": "fixture", "HOME": "fixture", "PROGRAMDATA": "system-fixture",
                                             "TERM": "xterm-256color", "COLORTERM": "truecolor"})


class SavedSSHMachineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.store = Store(self.directory / "data")

    def test_saved_machine_round_trip_preserves_missing_key_path(self):
        self.assertEqual(ssh_machines.load(self.store), {})
        key = self.directory / "synthetic key.pem"
        key.write_text("synthetic-private-key-content", encoding="utf-8")
        fixed = Connection.from_fields("server.example.invalid", "operator", 2222, key)
        saved = ssh_machines.save(self.store, "  开发机  ", fixed)
        self.assertEqual(saved.title, "开发机")
        self.assertNotIn("synthetic-private-key-content", (self.store.home / ssh_machines.FILE).read_text(encoding="utf-8"))
        key.unlink()
        self.assertEqual(ssh_machines.load(Store(self.store.home))[saved.id], saved)
        with self.assertRaisesRegex(SPXError, "私钥文件"):
            saved.connection.command()

    def test_rename_and_delete_preserve_other_entries_and_reject_stale_edits(self):
        connection = Connection.from_fields("example.invalid", "operator", 22)
        first = ssh_machines.save(self.store, "一号机", connection)
        second = ssh_machines.save(self.store, "", connection)
        self.assertEqual(second.title, "operator@example.invalid:22")
        updated = ssh_machines.save(self.store, "改名", connection, first)
        with self.assertRaisesRegex(SPXError, "已变更"):
            ssh_machines.save(self.store, "旧表单", connection, first)
        with self.assertRaisesRegex(SPXError, "已变更"):
            ssh_machines.remove(self.store, first)
        ssh_machines.remove(self.store, updated)
        self.assertEqual(ssh_machines.load(self.store), {second.id: second})

    def test_saved_catalog_with_unexpected_fields_is_not_replaced(self):
        path = self.store.home / ssh_machines.FILE
        old = '{"schema":1,"machines":{},"password":"synthetic"}'
        path.write_text(old, encoding="utf-8")
        with self.assertRaisesRegex(SPXError, "原文件已保留"):
            ssh_machines.save(self.store, "新机器", Connection.from_fields("example.invalid", "operator", 22))
        self.assertEqual(path.read_text(encoding="utf-8"), old)
