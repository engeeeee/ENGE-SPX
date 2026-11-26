import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from enge_spx import ssh_machines
from enge_spx.credentials import CredentialCodec
from enge_spx.ssh_client import Connection, environment, retryable_disconnect
from enge_spx.state import SPXError, Store
from test_credentials import MemoryProtector


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
    def test_reconnect_requires_known_host_and_uses_shorter_keepalive(self, _executable):
        connection = Connection.from_fields("localhost", "operator", 22)
        command = connection.command(reconnect=True, prefilled_password=True)
        self.assertIn("StrictHostKeyChecking=yes", command)
        self.assertIn("ServerAliveInterval=10", command)
        self.assertIn("ServerAliveCountMax=2", command)
        self.assertIn("NumberOfPasswordPrompts=1", command)
        self.assertNotIn("StrictHostKeyChecking=ask", command)

    def test_only_transport_errors_are_retried(self):
        errors = (
            b"client_loop: send disconnect: Broken pipe",
            b"Timeout, server 127.0.0.1 not responding.",
            b"fixture@server:~$ Connection closed by 127.0.0.1 port 22",
            b"current-draftConnection to 127.0.0.1 closed by remote host.\r\n",
            b"\x1b[31mssh: connect to host localhost port 22: Connection refused\x1b[0m\r\n",
            b"ssh: Could not resolve hostname localhost: Temporary failure in name resolution",
            b"kex_exchange_identification: read: Unknown error",
        )
        for error in errors:
            self.assertTrue(retryable_disconnect(255, error), error)
        self.assertTrue(retryable_disconnect(0xFFFFFFFF, errors[-2]))
        self.assertFalse(retryable_disconnect(0, b"Connection to 127.0.0.1 closed."))
        self.assertFalse(retryable_disconnect(255, b"Host key verification failed."))
        self.assertFalse(retryable_disconnect(255, b"fixture@localhost: Permission denied (password)."))
        self.assertFalse(retryable_disconnect(255, b"ssh: Bad configuration option: connect"))

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

    def test_upgrade_catalog_and_bind_saved_secret_to_the_machine_and_destination(self):
        legacy = Connection.from_fields("example.invalid", "operator", 22)
        first = ssh_machines.save(self.store, "旧机器", legacy)
        protector = CredentialCodec(self.store.instance, MemoryProtector())
        self.store.credentials = protector
        saved = ssh_machines.save(self.store, first.name, legacy, first, password=bytearray(b"fixture-secret"))
        self.assertEqual(saved.id, first.id)
        raw = (self.store.home / ssh_machines.FILE).read_text(encoding="utf-8")
        self.assertNotIn("fixture-secret", raw)
        self.assertNotIn(saved.protected_password, repr(saved))
        reopened = Store(self.store.home)
        reopened.credentials = protector
        listed = ssh_machines.load(reopened)[saved.id]
        self.assertEqual(ssh_machines.load_password(reopened, listed), bytearray(b"fixture-secret"))
        renamed = ssh_machines.save(self.store, "新版名称", legacy, saved)
        self.assertEqual(renamed.protected_password, saved.protected_password)

        catalog = self.store.read(ssh_machines.FILE)
        catalog["machines"][saved.id]["username"] = "changed"
        self.store.write(ssh_machines.FILE, catalog)
        changed = ssh_machines.load(self.store)[saved.id]
        with self.assertRaisesRegex(SPXError, "无法读取已保存"):
            ssh_machines.load_password(self.store, changed)
        updated = ssh_machines.save(self.store, "新地址", legacy, changed)
        self.assertIsNone(ssh_machines.load_password(self.store, updated))
        self.assertEqual(self.store.read(ssh_machines.FILE)["schema"], 1)

    def test_denied_protection_preserves_the_existing_catalog_and_clear_removes_ciphertext(self):
        self.store.credentials = CredentialCodec(self.store.instance, MemoryProtector())
        connection = Connection.from_fields("example.invalid", "operator", 22)
        saved = ssh_machines.save(self.store, "开发机", connection, password=bytearray(b"fixture-secret"))
        path = self.store.home / ssh_machines.FILE
        before = path.read_bytes()
        with patch.object(self.store.credentials.protector, "protect", side_effect=PermissionError):
            with self.assertRaisesRegex(SPXError, "原连接已保留"):
                ssh_machines.save(self.store, saved.name, connection, saved, password=bytearray(b"replacement"))
        self.assertEqual(path.read_bytes(), before)
        cleared = ssh_machines.save(self.store, saved.name, connection, saved, clear_password=True)
        self.assertFalse(cleared.has_password)
        self.assertNotIn(saved.protected_password, path.read_text(encoding="utf-8"))

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI required")
    def test_real_dpapi_persists_secret_for_current_windows_user(self):
        connection = Connection.from_fields("example.invalid", "operator", 22)
        secret = bytearray("模拟口令", "utf-8")
        saved = ssh_machines.save(self.store, "开发机", connection, password=secret)
        reopened = Store(self.store.home)
        machine = ssh_machines.load(reopened)[saved.id]
        self.assertEqual(ssh_machines.load_password(reopened, machine), secret)
        self.assertNotIn(secret, (self.store.home / ssh_machines.FILE).read_bytes())
