import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from enge_spx.brand import PACKAGE_RESOURCES
from enge_spx.tool_session import command


spec = importlib.util.spec_from_file_location('agy_fixture', PACKAGE_RESOURCES / 'checks/antigravity.py')
agy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agy)


class AntigravityTests(unittest.TestCase):
    def test_interactive_agy_uses_session_only_native_rendering(self):
        args = command(['agy'], antigravity_fullscreen=True, keep_open=True)
        self.assertEqual(args[-2], '--settings')
        self.assertEqual(json.loads(args[-1]), {'altScreenMode': 'always'})
        self.assertNotIn('--settings', command(['agy'], keep_open=True))
        self.assertEqual(command(['agy', '--spx-update'], antigravity_fullscreen=True)[-1], '--spx-update')

    def test_verified_source_and_literal_arguments(self):
        url = 'https://storage.googleapis.com/antigravity-public/antigravity-cli/1.5.14-5302690847260672/linux-x64/cli_linux_x64.tar.gz'
        raw = {'version': '1.5.14', 'url': url, 'sha512': 'a' * 128}
        self.assertEqual(agy.validate_manifest(json.dumps(raw), agy.ARCHITECTURES['x86_64'])[1], url)
        for untrusted in (url.replace('storage.googleapis.com', 'downloads.example'), url + '?ignored', url.replace('linux-x64', 'linux-arm')):
            with self.assertRaises(ValueError):
                agy.validate_manifest(json.dumps({**raw, 'url': untrusted}), agy.ARCHITECTURES['x86_64'])
        args = command(['agy', '--version'])
        self.assertEqual(args[-5:-2], ['python3', '-I', '-c'])
        self.assertEqual(args[-1], '--version')

    def test_archive_writes_only_the_expected_regular_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, output = Path(folder) / 'archive.tgz', Path(folder) / 'agy'
            with tarfile.open(archive, 'w:gz') as package:
                item = tarfile.TarInfo('antigravity')
                item.type = tarfile.SYMTYPE
                item.linkname = '/etc/passwd'
                package.addfile(item)
            with self.assertRaises(ValueError):
                agy.unpack(archive, output)
            self.assertFalse(output.exists())
            data = b'\x7fELFtest'
            with tarfile.open(archive, 'w:gz') as package:
                item = tarfile.TarInfo('antigravity')
                item.size = len(data)
                package.addfile(item, io.BytesIO(data))
            agy.unpack(archive, output)
            self.assertEqual(output.read_bytes(), data)
