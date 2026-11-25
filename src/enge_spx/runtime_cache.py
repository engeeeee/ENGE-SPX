"""Bounded cleanup of app-managed prebuilt Docker download files."""
from dataclasses import dataclass
import itertools
import re
import stat

from . import __version__
from .state import SPXError

ARCHIVE = re.compile(r"ENGE-SPX-Runtime-linux-amd64-([0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4})\.tar\.gz(\.part)?")


@dataclass(frozen=True)
class DownloadFile:
    name: str
    size: int
    device: int
    inode: int
    updated: int


def _is_local(info):
    return not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT


def _folder(store):
    path = store.home / "cache"
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(info.st_mode) or not _is_local(info):
        raise SPXError("运行环境缓存目录使用了链接，无法安全清理。")
    return path


def _snapshot(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or not _is_local(info) or info.st_nlink != 1:
        return None
    return DownloadFile(path.name, info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns)


def snapshot(store, name):
    if not ARCHIVE.fullmatch(name) or name.endswith(".part"):
        return None
    folder = _folder(store)
    return _snapshot(folder / name) if folder else None


def inspect(store):
    """Return removable archives and the bytes needed for retry or resume."""
    folder = _folder(store)
    if folder is None:
        return [], 0
    receipt = store.read("runtime-bundle.json", {})
    if not isinstance(receipt, dict):
        receipt = {}
    removable, pending = [], 0
    for index, path in enumerate(itertools.islice(folder.iterdir(), 2049)):
        if index == 2048:
            raise SPXError("下载缓存目录文件过多，请在应用数据目录中检查。")
        match = ARCHIVE.fullmatch(path.name)
        if not match:
            continue
        item = _snapshot(path)
        if item is None:
            continue
        archive_version, partial = match.groups()
        imported = receipt.get("version") == archive_version and receipt.get("bytes") == item.size
        if not partial and (archive_version != __version__ or imported):
            removable.append(item)
        else:
            pending += item.size
    return removable, pending


def remove(store, item):
    """Remove only the same regular archive inspected under the operation lock."""
    store.check_location()
    if item is None or snapshot(store, item.name) != item:
        return 0
    try:
        (store.home / "cache" / item.name).unlink()
    except FileNotFoundError:
        return 0
    return item.size
