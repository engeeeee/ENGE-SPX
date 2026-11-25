"""Stage only Microsoft's pinned x64 ConPTY binaries for the Windows build."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile


VERSION = "1.25.261109001"
PACKAGE = "microsoft.windows.console.conpty"
URL = f"https://api.nuget.org/v3-flatcontainer/{PACKAGE}/{VERSION}/{PACKAGE}.{VERSION}.nupkg"
SHA256 = "3d77f535df848e44225c2a8912ac844fecb23f3057732b639f3034b587496f09"
FILES = (
    ("runtimes/win-x64/native/conpty.dll", "conpty.dll"),
    ("build/native/runtimes/x64/OpenConsole.exe", "OpenConsole.exe"),
)
DESTINATION = Path(__file__).resolve().parents[1] / "build" / "ssh-conpty"


def main():
    with urllib.request.urlopen(URL, timeout=45) as response:
        payload = response.read(4 * 1024 * 1024)
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise SystemExit("Microsoft ConPTY package checksum differs")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for source, filename in FILES:
            (DESTINATION / filename).write_bytes(archive.read(source))
    print(f"Staged Microsoft ConPTY {VERSION} for Windows x64")


if __name__ == "__main__":
    main()
