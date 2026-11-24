import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from enge_spx.ssh_client import Connection, environment
from enge_spx.state import SPXError


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
        with patch.dict(os.environ, {"PATH": "fixture", "HOME": "fixture",
                                     "SPX_BROWSER_TOKEN": "synthetic", "SSH_ASKPASS": "synthetic",
                                     "SSH_AUTH_SOCK": "synthetic", "HTTPS_PROXY": "synthetic"}, clear=True):
            self.assertEqual(environment(), {"PATH": "fixture", "HOME": "fixture",
                                             "TERM": "xterm-256color", "COLORTERM": "truecolor"})
