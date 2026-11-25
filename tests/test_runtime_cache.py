from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from enge_spx import __version__, runtime_cache
from enge_spx.engine import Engine, RECIPE
from enge_spx.state import SPXError, Store


class RuntimeCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = Store(Path(temporary.name))
        self.folder = self.store.home / "cache"
        self.folder.mkdir()
        self.filename = f"ENGE-SPX-Runtime-linux-amd64-{__version__}.tar.gz"
        self.archive = self.folder / self.filename

    def test_cleanup_ignores_pending_archives_and_arbitrary_files(self):
        old = self.folder / "ENGE-SPX-Runtime-linux-amd64-0.0.1.tar.gz"
        part = self.folder / (self.filename + ".part")
        unrelated = self.folder / "my-file.tar.gz"
        for file in (self.archive, part, old, unrelated):
            file.write_bytes(b"fixture")
        with self.store.lock():
            items, pending = runtime_cache.inspect(self.store)
            self.assertEqual([item.name for item in items], [old.name])
            self.assertEqual(pending, 14)
            self.assertEqual(runtime_cache.remove(self.store, items[0]), 7)
        for file in (self.archive, part, unrelated):
            self.assertEqual(file.read_bytes(), b"fixture")

    def test_replaced_archive_is_not_removed(self):
        self.archive.write_bytes(b"original")
        item = runtime_cache.snapshot(self.store, self.filename)
        self.archive.write_bytes(b"replacement")
        with self.store.lock():
            self.assertEqual(runtime_cache.remove(self.store, item), 0)
        self.assertEqual(self.archive.read_bytes(), b"replacement")

    def test_import_retires_verified_archive_and_keeps_failed_download(self):
        engine = Engine(self.store)
        engine.doctor = Mock(return_value={"architecture": "x86_64"})
        engine._stop = Mock()
        meta = {"filename": self.filename, "version": __version__, "sha256": "f" * 64, "bytes": 7,
                "images": {role: role for role in engine.recipes}, "image_configs": {role: role for role in engine.recipes}}
        engine.docker.inspect = Mock(side_effect=lambda kind, role: {"Architecture": "amd64", "Id": role,
                                                                    "Config": {"Labels": {RECIPE: engine.recipes[role]}}})
        engine.docker.run = Mock(side_effect=[SPXError("fixture import failed"), "ok"])
        self.archive.write_bytes(b"fixture")
        with patch("enge_spx.downloads.manifest", return_value=meta), \
                patch("enge_spx.downloads.download", return_value=self.archive), \
                patch("enge_spx.proxy.download_proxy", return_value=(None, "fixture")):
            with self.assertRaisesRegex(SPXError, "fixture import failed"):
                engine.install_prebuilt()
            self.assertTrue(self.archive.exists())
            self.assertFalse((self.store.home / "images.json").exists())
            progress = []
            engine.install_prebuilt(progress.append)
        self.assertFalse(self.archive.exists())
        self.assertEqual(progress[-1], {"stage": "done", "cache_reclaimed": 7})
        self.assertEqual(self.store.read("images.json"), meta["images"])
        self.assertEqual(self.store.read("runtime-bundle.json")["sha256"], meta["sha256"])
