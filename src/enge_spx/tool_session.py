"""Rootless updates in the existing Profile home; no image/data migration."""

from .brand import PACKAGE_RESOURCES

# The root-owned image installation remains the offline fallback. Explicit
# updates install under the selected identity's existing home volume. Never
# grant root, change system ownership or share a new global tools volume.
PREPARE = '''set -e
spx_prefix="${HOME:?}/.local"
mkdir -p -- "$spx_prefix/bin"
export NPM_CONFIG_PREFIX="$spx_prefix"
export npm_config_prefix="$spx_prefix"
export PATH="$spx_prefix/bin:$PATH"
'''

KEEP_OPEN = '''set +e
"$@"
spx_result=$?
printf '\\nENGE SPX: 工具已结束（退出码 %s）。在这里可重新运行工具；输入 exit 关闭此终端。\\n' "$spx_result"
exec bash --noprofile -i
'''


def command(arguments, *, keep_open=False):
    # All tool arguments remain separate argv elements, including arbitrary
    # user-supplied CLI arguments. No interpolation into executable shell text.
    if arguments and arguments[0] == 'agy':
        bootstrap = (PACKAGE_RESOURCES / 'checks/antigravity.py').read_text(encoding='utf-8')
        arguments = ['python3', '-I', '-c', bootstrap, *arguments[1:]]
    flags = ["-i"] if keep_open else []
    return ["bash", "--noprofile", "--norc", *flags, "-c",
            PREPARE + (KEEP_OPEN if keep_open else 'exec "$@"\n'),
            "enge-spx-tool", *arguments]
