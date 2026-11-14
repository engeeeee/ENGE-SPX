"""Capture the real product terminal running a supplied official Codex binary.

Linux presentation capture, not a Windows/Docker acceptance test. Reuses the
existing loopback-only CLI fixture, with no account, real model or user data.
The draft is never submitted; no terminal output or UI is fabricated.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", default="2")
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("This capture fixture is Linux-only; do not label it Windows.")
    os.environ["QT_SCALE_FACTOR"] = args.scale
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("clipboard_fixture", root / "tests/integration_cli_clipboard.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    args.output.mkdir(parents=True, exist_ok=True)
    api = fixture.FixtureAPI()
    threading.Thread(target=api.serve_forever, daemon=True).start()
    attachments = Path("/tmp") / ("enge-spx-clipboard-" + secrets.token_hex(8))
    attachment_dir = attachments / secrets.token_hex(16)
    attachment_dir.mkdir(parents=True)
    tui = None
    try:
        with tempfile.TemporaryDirectory(prefix="enge-spx-terminal-capture-") as temp:
            base = Path(temp)
            home, project = base / "home", base / "example-project"
            (home / ".codex").mkdir(parents=True)
            project.mkdir()
            note = attachment_dir / (secrets.token_hex(16) + ".md")
            note.write_text("# Example project\nDocumentation-only terminal capture.\n", encoding="utf-8")
            images = []
            for source in (root / "src/enge_spx/resources/icons/logo-256.png", root / "docs/images/0.13.2/overview.png"):
                target = attachment_dir / (secrets.token_hex(16) + ".png")
                shutil.copyfile(source, target)
                images.append(target)
            endpoint = "http://127.0.0.1:" + str(api.server_port)
            environment = {k: v for k, v in os.environ.items() if k in ("PATH", "QT_QPA_PLATFORM", "QT_SCALE_FACTOR", "FONTCONFIG_PATH")}
            environment.update(HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / ".codex"),
                               LANG="C.UTF-8", TERM="xterm-256color", COLORTERM="truecolor", TERM_PROGRAM="ENGE-SPX",
                               NO_PROXY="127.0.0.1,localhost", HTTP_PROXY=endpoint, HTTPS_PROXY=endpoint,
                               DO_NOT_TRACK="1", SPX_CLIPBOARD_TEST_KEY="synthetic-fixture-not-real")
            executable = str(args.codex.resolve())
            version = subprocess.check_output([executable, "--version"], env=environment, text=True, timeout=20).strip()
            command = [executable, "--no-daemon", "-m", "gpt-6-sol", "-c", 'model_provider="clipboard_fixture"',
                       "-c", 'model_providers.clipboard_fixture.name="Clipboard Fixture"',
                       "-c", 'model_providers.clipboard_fixture.base_url="' + endpoint + '/v1"',
                       "-c", 'model_providers.clipboard_fixture.wire_api="responses"',
                       "-c", 'model_providers.clipboard_fixture.requires_openai_auth=false',
                       "-c", 'model_providers.clipboard_fixture.supports_websockets=false',
                       "-c", 'model_providers.clipboard_fixture.env_key="SPX_CLIPBOARD_TEST_KEY"',
                       "-c", 'check_for_update_on_startup=false']
            tui = fixture.QtTUI(command, environment, project, "codex", tuple(map(int, version.split()[-1].split("."))))
            tui.window.resize(1100, 680)
            tui.window.preferences.set("font_size", 13)
            tui.wait(lambda value: "To get started" in value)
            tui.wait(lambda value: tui.window.view.ready.is_set())
            tui.paste(fixture.Snapshot("text", "请查看这两张图片，帮我检查界面中的问题。\n"))
            tui.wait(lambda value: "检查界面" in value)
            for index, path in enumerate(images, 1):
                tui.paste(fixture.Snapshot("files", (str(path),)))
                tui.wait(lambda value: "[Image #" + str(index) + "]" in value)
                tui.wait(lambda value: "已交给" in tui.window.message.text())
            tui.paste(fixture.Snapshot("text", "\n再结合这份文件说明原因：" + str(note)))
            tui.wait(lambda value: "说明原因" in value and note.name in value)
            for _ in range(20):
                tui.app.processEvents()
                time.sleep(.025)
            assert not api.requests, "Presentation capture must leave the draft unsent"
            filename = "terminal-codex@2x.png"
            tui.capture(args.output / filename)
            from enge_spx import __version__
            import PySide6
            image = fixture.QImage(str(args.output / filename))
            manifest = {"schema": 1, "captured_at": datetime.now(timezone.utc).isoformat(),
                        "app_version": __version__, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                        "platform": sys.platform, "qt_platform": os.environ["QT_QPA_PLATFORM"], "pyside6": PySide6.__version__,
                        "cli": version, "cli_sha256": hashlib.sha256(args.codex.read_bytes()).hexdigest(),
                        "logical_size": [tui.window.width(), tui.window.height()], "device_pixel_ratio": tui.window.devicePixelRatioF(),
                        "pixel_size": [image.width(), image.height()], "qt_scale_factor": args.scale,
                        "file": filename, "sha256": hashlib.sha256((args.output / filename).read_bytes()).hexdigest(),
                        "real_product_window": True, "real_cli": True, "native_image_markers": 2, "draft_submitted": False,
                        "docker_transport": "not_used", "windows_clipboard": "not_tested", "model_response": "none"}
            (args.output / "terminal-capture.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(manifest, ensure_ascii=False))
    finally:
        if tui:
            tui.close()
        api.shutdown()
        api.server_close()
        shutil.rmtree(attachments)


if __name__ == "__main__":
    main()
