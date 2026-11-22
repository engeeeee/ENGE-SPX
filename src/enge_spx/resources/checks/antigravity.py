"""Install and launch Google's CLI inside the selected project container."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


MANIFEST = 'https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/'
ARCHITECTURES = {'x86_64': ('amd64', 'x64', 'x64'), 'aarch64': ('arm64', 'arm', 'arm64')}
MAX_ARCHIVE = 192 * 1024**2
MAX_BINARY = 384 * 1024**2


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def validate_manifest(raw, architecture):
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('invalid manifest')
    version, url, digest = (data.get(key) for key in ('version', 'url', 'sha512'))
    if not all(isinstance(value, str) for value in (version, url, digest)):
        raise ValueError('incomplete manifest')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version) or not re.fullmatch(r'[a-f0-9]{128}', digest):
        raise ValueError('invalid version or checksum')
    _, folder, suffix = architecture
    path = '/antigravity-public/antigravity-cli/' + re.escape(version) + rf'-[0-9]+/linux-{folder}/cli_linux_{suffix}\.tar\.gz'
    if not re.fullmatch('https://storage\\.googleapis\\.com' + path, url):
        raise ValueError('unexpected download source')
    return version, url, digest


def download(opener, url, path, digest):
    hasher, size = hashlib.sha512(), 0
    deadline = time.monotonic() + 240
    with opener.open(url, timeout=15) as source, path.open('xb') as target:
        while chunk := source.read(1024**2):
            size += len(chunk)
            if size > MAX_ARCHIVE or time.monotonic() > deadline:
                raise ValueError('download limit exceeded')
            target.write(chunk)
            hasher.update(chunk)
    if hasher.hexdigest() != digest:
        raise ValueError('checksum mismatch')


def unpack(archive, destination):
    with tarfile.open(archive, 'r|gz') as package:
        item = package.next()
        if not item or item.name != 'antigravity' or not item.isreg() or not 0 < item.size <= MAX_BINARY:
            raise ValueError('unexpected Antigravity archive')
        with package.extractfile(item) as source, destination.open('xb') as target:
            if source.read(4) != b'\x7fELF':
                raise ValueError('unexpected executable format')
            target.write(b'\x7fELF')
            shutil.copyfileobj(source, target, 1024**2)
    if destination.stat().st_size != item.size:
        raise ValueError('incomplete executable')
    destination.chmod(0o755)


def install(directory, proxy):
    source = urlsplit(proxy)
    gateway = ipaddress.IPv4Address(source.hostname)
    if source.scheme != 'http' or source.netloc != f'{gateway}:2080' or source.path or source.query or source.fragment:
        raise ValueError('invalid workspace gateway')
    architecture = ARCHITECTURES.get(platform.machine())
    if not architecture:
        raise ValueError('unsupported Linux architecture')
    opener = build_opener(NoRedirect(), ProxyHandler({'https': proxy}))
    # urllib's ProxyHandler honors NO_PROXY even with an explicit proxy.
    bypass = {key: os.environ.pop(key) for key in tuple(os.environ) if key.lower() == 'no_proxy'}
    try:
        with opener.open(MANIFEST + 'linux_' + architecture[0] + '.json', timeout=15) as response:
            raw = response.read(32 * 1024 + 1)
        if len(raw) > 32 * 1024:
            raise ValueError('manifest limit exceeded')
        version, url, digest = validate_manifest(raw, architecture)
        print(f'ENGE SPX: 正在通过工作区代理下载 Antigravity CLI {version}，首次安装约 100 MB…', flush=True)
        with tempfile.TemporaryDirectory(prefix='.spx-agy-', dir=directory) as folder:
            archive = Path(folder) / 'download.tar.gz'
            staged = Path(folder) / 'agy'
            download(opener, url, archive, digest)
            unpack(archive, staged)
            staged.replace(directory / 'agy')
        print(f'ENGE SPX: Antigravity CLI {version} 已安装，SHA-512 校验通过。', flush=True)
    finally:
        os.environ.update(bypass)


def main(arguments):
    import fcntl

    home = Path.home()
    if home != Path('/home/workspace') or os.geteuid() != 1000:
        raise ValueError('unexpected workspace user')
    directory = home / '.local' / 'bin'
    for path in (home / '.local', directory):
        if path.is_symlink():
            raise ValueError('unexpected tool directory link')
        path.mkdir(exist_ok=True)
    target = directory / 'agy'
    update = arguments == ['--spx-update']
    if update or not target.exists():
        descriptor = os.open(directory / '.spx-agy.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        with os.fdopen(descriptor, 'wb') as lock:
            if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
                raise ValueError('unexpected lock file')
            fcntl.flock(lock, fcntl.LOCK_EX)
            if update or not target.exists():
                install(directory, os.environ.get('HTTPS_PROXY', ''))
    if not update:
        os.environ['AGY_CLI_DISABLE_AUTO_UPDATE'] = 'true'
        os.execv(target, [str(target), *arguments])


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, tarfile.TarError, EOFError):
        raise SystemExit('ENGE SPX: Antigravity CLI 安装或启动失败。请确认工作区可通过代理访问 Google 下载服务、空间充足，再重试。')
