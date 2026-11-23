import asyncio
import ctypes
from contextlib import ExitStack, nullcontext, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

from enge_spx import forward
from enge_spx.brand import PACKAGE_RESOURCES
from enge_spx.engine import Engine
from enge_spx.lease import write_lease
from enge_spx.state import Store, atomic_json


def windows_denied():
    error = PermissionError(13, "sharing conflict")
    error.winerror = 5
    return error


class MonitorReliabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = Store(Path(temporary.name) / "data")

    def test_atomic_write_retries_windows_denial_without_truncating_old_lease(self):
        path = self.store.home / "lease.json"
        atomic_json(path, {"expires": 1})
        replace = os.replace
        attempts = []
        def busy_then_release(source, target):
            attempts.append(1)
            self.assertEqual(json.loads(path.read_text()), {"expires": 1})
            if len(attempts) < 3:
                raise windows_denied()
            replace(source, target)
        with patch("enge_spx.state.os.replace", side_effect=busy_then_release), patch("enge_spx.state.time.sleep"):
            atomic_json(path, {"expires": 2})
        self.assertEqual(len(attempts), 3)
        self.assertEqual(self.store.read("lease.json"), {"expires": 2})
        self.assertFalse(list(self.store.home.glob(".next-*")))

    def test_persistent_denial_has_deadline_and_preserves_last_lease(self):
        path = self.store.home / "lease.json"
        atomic_json(path, {"expires": 1})
        clock = [0]
        def sleep(delay):
            clock[0] += delay
        with patch("enge_spx.state.os.replace", side_effect=windows_denied()), patch("enge_spx.state.time.monotonic", side_effect=lambda: clock[0]), patch("enge_spx.state.time.sleep", side_effect=sleep):
            with self.assertRaises(PermissionError):
                atomic_json(path, {"expires": 2})
        self.assertLessEqual(clock[0], 3.01)
        self.assertEqual(self.store.read("lease.json"), {"expires": 1})
        self.assertFalse(list(self.store.home.glob(".next-*")))

    def test_guard_recovers_from_io_error_without_shell_activity_or_early_stop(self):
        old = {"phase": "ready", "heartbeat": time.time(), "evidence": {"ip": "8.8.8.8"}}
        self.store.write("runtime.json", old)
        engine = Engine(self.store, Mock())
        engine.audit_topology = Mock()
        engine.probe_chain = Mock(return_value={"ip": "8.8.8.8", "timezone": "America/Los_Angeles"})
        engine._stop = Mock()
        original = self.store.write
        failed = []
        def write(name, value):
            if name == "gateway/lease.json" and not failed:
                failed.append(True)
                raise windows_denied()
            original(name, value)
        idle_ticks = []
        def tick(delay):
            if delay == 3:
                self.assertEqual(self.store.read("runtime.json"), old)
            else:
                self.assertEqual(delay, 1)
                idle_ticks.append(delay)
                if len(idle_ticks) == 30:
                    original("runtime.json", {"phase": "stopped"})
        with patch.object(self.store, "write", side_effect=write), patch("enge_spx.engine.time.sleep", side_effect=tick) as sleep:
            engine.guard()
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [3] + [1] * 30)
        self.assertEqual(engine.probe_chain.call_count, 2)
        engine._stop.assert_not_called()
        self.assertGreater(self.store.read("gateway/lease.json")["expires"], time.time())
        engine.log.assert_called_once()

    def test_stop_signal_interrupts_guard_sleep_without_another_network_check(self):
        self.store.write("runtime.json", {"phase": "ready"})
        engine = Engine(self.store)
        engine.ready = Mock()
        def stop_during_sleep(delay):
            self.assertEqual(delay, 1)
            self.store.write("guard-stop.json", {"schema": 1, "requested": True})
        with patch("enge_spx.engine.time.sleep", side_effect=stop_during_sleep) as sleep:
            engine.guard()
        engine.ready.assert_called_once_with()
        sleep.assert_called_once_with(1)
        # Releasing the old monitor lock precedes clearing the stop signal.
        with self.store.lock("guard"):
            self.assertTrue((self.store.home / "guard-stop.json").is_file())
        self.store.write("runtime.json", {"phase": "stopped"})
        engine.take_over_legacy_guard()
        self.assertFalse((self.store.home / "guard-stop.json").exists())

    def test_guard_retries_a_busy_operation_lock_before_the_next_normal_interval(self):
        self.store.write("runtime.json", {"phase": "ready"})
        engine = Engine(self.store)
        engine.ready = Mock(side_effect=lambda: self.store.write("guard-stop.json", {"requested": True}))
        with ExitStack() as foreground:
            foreground.enter_context(self.store.lock())
            with patch("enge_spx.engine.time.sleep", side_effect=lambda _: foreground.close()) as sleep:
                engine.guard()
        engine.ready.assert_called_once_with()
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 1, 1])

    def test_stop_signal_write_denial_does_not_prevent_container_shutdown(self):
        self.store.write("images.json", {"gateway": "image"})
        engine = Engine(self.store)
        engine.docker = Mock(executable="docker.exe")
        engine.managed = Mock(return_value=["gateway-container"])
        obj = {"Id": "gateway-container", "Config": {"Labels": {engine.role: "gateway"}}, "State": {"Running": True}}
        engine.docker.inspect.return_value = obj
        engine.owned = Mock(return_value=obj)
        original = self.store.write
        def write(name, value):
            if name == "guard-stop.json":
                raise windows_denied()
            original(name, value)
        with patch.object(self.store, "write", side_effect=write):
            with self.assertRaises(PermissionError):
                engine.stop()
        engine.docker.run.assert_called_once_with("stop", "--time", "8", "gateway-container", timeout=25)
        self.assertEqual(self.store.read("runtime.json")["phase"], "stopped")
        self.assertEqual(self.store.read("gateway/lease.json")["expires"], 0)

    def test_network_migration_stop_signal_cannot_cancel_the_new_monitor(self):
        engine = Engine(self.store)
        engine.docker = Mock(executable=None)
        engine.doctor = Mock()
        engine._retire_stopped_browser = Mock()
        def migrate_and_setup():
            engine._stop("正在升级内部网络隔离策略")
            return {}
        engine.setup = Mock(side_effect=migrate_and_setup)
        engine.policy = Mock(return_value="policy")
        engine.ensure_forward = Mock()
        engine.wait_proxy_listeners = Mock()
        engine.audit_topology = Mock()
        engine.probe_chain = Mock(return_value={"ip": "8.8.8.8", "timezone": "America/Los_Angeles"})
        engine.start_guard = Mock()
        engine.check()
        engine.confirm()
        self.assertEqual(self.store.read("runtime.json")["phase"], "ready")
        self.assertFalse((self.store.home / "guard-stop.json").exists())
        # Run the actual loop: a stale migration marker would skip ready().
        engine.ready = Mock()
        def finish(delay):
            self.store.write("guard-stop.json", {"schema": 1, "requested": True})
        with patch("enge_spx.engine.time.sleep", side_effect=finish):
            engine.guard()
        engine.ready.assert_called_once_with()

    def test_stop_still_shuts_down_gateway_when_lease_write_is_denied(self):
        self.store.write("images.json", {"gateway": "image"})
        engine = Engine(self.store)
        engine.docker = Mock(executable="docker.exe")
        engine.managed = Mock(return_value=["gateway-container"])
        obj = {"Id": "gateway-container", "Config": {"Labels": {engine.role: "gateway"}}, "State": {"Running": True}}
        engine.docker.inspect.return_value = obj
        engine.owned = Mock(return_value=obj)
        engine.set_lease = Mock(side_effect=windows_denied())
        with self.assertRaises(PermissionError):
            engine.stop()
        engine.docker.run.assert_called_once_with("stop", "--time", "8", "gateway-container", timeout=25)
        self.assertEqual(self.store.read("runtime.json")["phase"], "stopped")

    def test_stop_retries_the_legacy_lease_after_the_gateway_releases_it(self):
        self.store.write("runtime.json", {"phase": "ready"})
        self.store.write("images.json", {"gateway": "image"})
        engine = Engine(self.store)
        engine.docker = Mock(executable="docker.exe")
        engine.managed = Mock(return_value=["gateway-container"])
        engine.docker.inspect.return_value = {
            "Id": "gateway-container", "State": {"Running": True},
            "Config": {"Labels": {engine.owner: self.store.instance, engine.role: "gateway"}},
        }
        write = self.store.write

        def deny_before_stop(name, value):
            if name == "gateway/lease.json" and not engine.docker.run.called:
                raise windows_denied()
            write(name, value)

        with patch.object(self.store, "write", side_effect=deny_before_stop):
            engine.stop()
        engine.docker.run.assert_called_once_with("stop", "--time", "8", "gateway-container", timeout=25)
        self.assertEqual(self.store.read("runtime.json")["phase"], "stopped")
        self.assertEqual(self.store.read("gateway/lease.json"), {"expires": 0})

    def test_repeated_stop_preserves_the_append_only_lease_format(self):
        self.store.write("runtime.json", {"phase": "ready", "lease_journal": True})
        engine = Engine(self.store)
        engine.stop()
        engine.stop()
        self.assertTrue(self.store.read("runtime.json")["lease_journal"])
        self.assertFalse((self.store.home / "gateway/lease.json").exists())
        records = (self.store.home / "gateway/lease.jsonl").read_text().splitlines()
        self.assertEqual([json.loads(line) for line in records if line], [{"expires": 0}, {"expires": 0}])

    def test_forward_start_waits_for_old_lock_and_keeps_one_pending_worker(self):
        engine = Engine(self.store)
        engine.docker = Mock()
        engine.background = Mock(return_value=Mock(poll=Mock(return_value=None)))
        state = {"gateway": "gateway", "forward_id": "new", "forward_target": {"host": "127.0.0.1", "port": 1080}}
        ticks = []
        with ExitStack() as old_worker:
            old_worker.enter_context(self.store.lock("forward"))

            def tick(delay):
                ticks.append(delay)
                if len(ticks) == 4:
                    old_worker.close()
                if len(ticks) == 12:
                    self.store.write("forward.json", {**forward.binding(state), "heartbeat": time.time()})

            with patch("enge_spx.engine.time.sleep", side_effect=tick):
                engine.ensure_forward(state)
        engine.background.assert_called_once_with("forward")
        engine.docker.run.assert_called_once()

    def test_duplicate_forward_process_exits_when_another_worker_holds_the_lock(self):
        with self.store.lock("forward"), patch.object(forward, "run") as run:
            forward.main(self.store)
        run.assert_not_called()

    def test_forward_heartbeat_recovers_from_windows_file_sharing_conflict(self):
        state = {"phase": "ready", "gateway": "gateway", "forward_target": {"host": "127.0.0.1", "port": 1080}}
        store = Mock(home=self.store.home)
        store.read.return_value = state
        store.write.side_effect = [windows_denied(), None]
        engine = Mock()
        engine.inspect.return_value = {"Id": "gateway", "State": {"Running": True}}
        engine._image_abis = {"gateway": "spx"}
        engine.docker.command.return_value = ["docker", "exec"]
        process = Mock(returncode=0)
        sleep = asyncio.sleep

        async def relay_until_closed():
            await asyncio.Event().wait()

        async def tick(delay):
            if store.write.call_count == 2:
                state["phase"] = "stopped"
            await sleep(0)

        tunnel = Mock(run=AsyncMock(side_effect=relay_until_closed))
        with (
            patch.object(forward, "Engine", return_value=engine),
            patch.object(forward.socket, "create_connection", return_value=nullcontext()) as probe,
            patch.object(forward.asyncio, "create_subprocess_exec", new=AsyncMock(return_value=process)),
            patch.object(forward, "tunnel_type", return_value=Mock(return_value=tunnel)),
            patch.object(forward.asyncio, "sleep", side_effect=tick),
            redirect_stderr(io.StringIO()),
        ):
            asyncio.run(forward.run(store))
        probe.assert_called_once_with(("127.0.0.1", 1080), timeout=5)
        tunnel.run.assert_awaited_once()
        self.assertEqual([call.args[0] for call in store.write.call_args_list], ["forward.json", "forward.json"])

    def test_journal_partial_tail_and_revocation_keep_original_expiry(self):
        spec = importlib.util.spec_from_file_location("spx_gateway", PACKAGE_RESOURCES / "containers/gateway.py")
        gateway = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gateway)
        path = self.store.home / "gateway/lease.jsonl"
        write_lease(self.store, time.time() + 100, reset=True)
        with patch.object(gateway, "Path", return_value=path):
            self.assertTrue(gateway.lease_valid())
            with path.open("ab") as stream:
                stream.write(b'{"expires":')
            self.assertTrue(gateway.lease_valid())
            write_lease(self.store, time.time() + 100)
            self.assertTrue(gateway.lease_valid())
            write_lease(self.store, 0)
            self.assertFalse(gateway.lease_valid())

    @unittest.skipUnless(os.name == "nt", "Windows Docker-style reader denies replacement but allows append")
    def test_journal_renews_while_windows_reader_disallows_delete(self):
        write_lease(self.store, 1, reset=True)
        path = self.store.home / "gateway/lease.jsonl"
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.CreateFileW(str(path), 0x80000000, 1 | 2, None, 3, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        try:
            replacement = path.with_suffix(".next")
            replacement.write_text("replacement")
            with self.assertRaises(PermissionError):
                os.replace(replacement, path)
            write_lease(self.store, 2)
        finally:
            kernel.CloseHandle(handle)
        self.assertEqual(json.loads(path.read_text().splitlines()[-1])["expires"], 2)

    @unittest.skipUnless(os.name == "nt", "Real Windows handle without FILE_SHARE_DELETE")
    def test_real_windows_reader_allows_retry_after_handle_is_closed(self):
        path = self.store.home / "lease.json"
        atomic_json(path, {"expires": 1})
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.CreateFileW(str(path), 0x80000000, 1 | 2, None, 3, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        def close():
            time.sleep(.2)
            kernel.CloseHandle(handle)
        thread = threading.Thread(target=close)
        thread.start()
        try:
            atomic_json(path, {"expires": 2})
        finally:
            thread.join(2)
        self.assertEqual(self.store.read("lease.json"), {"expires": 2})


class ExitProbeTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("spx_exit_probe", PACKAGE_RESOURCES / "checks/exit_probe.py")
        self.probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.probe)

    def test_health_proof_queries_exits_concurrently_without_geography(self):
        barrier = threading.Barrier(2)
        urls = []
        def fetch(url, timeout):
            urls.append(url)
            barrier.wait(2)
            return io.BytesIO(b'{"ip":"8.8.8.8"}' if "ipify" in url else b"8.8.8.8\n")
        opener = Mock(open=fetch)
        with patch.object(self.probe.urllib.request, "build_opener", return_value=opener), patch.object(self.probe.socket, "create_connection", side_effect=OSError("blocked")), patch.dict(os.environ, {"NO_PROXY": "*"}):
            evidence = self.probe.probe("http://127.0.0.1:2080")
            self.assertNotIn("NO_PROXY", os.environ)
        self.assertEqual(evidence["ip"], "8.8.8.8")
        self.assertTrue(evidence["direct_blocked"])
        self.assertEqual(len(urls), 2)
        self.assertNotIn("country", evidence)

    def test_healthy_proxy_never_overrides_a_successful_direct_connection(self):
        def fetch(url, timeout):
            return io.BytesIO(b'{"ip":"8.8.8.8"}' if "ipify" in url else b"8.8.8.8\n")
        with patch.object(self.probe.urllib.request, "build_opener", return_value=Mock(open=fetch)), patch.object(self.probe.socket, "create_connection", return_value=Mock(__enter__=Mock(), __exit__=Mock())):
            with self.assertRaisesRegex(ValueError, "Direct outbound"):
                self.probe.probe("http://127.0.0.1:2080")


if __name__ == "__main__":
    unittest.main()
