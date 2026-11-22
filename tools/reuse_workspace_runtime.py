"""Verify and load the unchanged 0.15.2 images for the 0.15.3 release."""
import argparse
from pathlib import Path
import subprocess
import tempfile

from enge_spx import __version__
from enge_spx.engine import Docker, Engine
from enge_spx.state import Store
from reuse_ui_hotfix_runtime import copy_runtime


BASE = '1f4cc1df87b07fc9fb16129a3c5d0cd6db90b30a'


def main(destination):
    assert __version__ == '0.15.3'
    subprocess.run(['git', 'diff', '--exit-code', BASE, 'HEAD', '--', 'src/enge_spx/resources/containers'], check=True)
    with tempfile.TemporaryDirectory(prefix='spx-runtime-recipes-') as path:
        recipes = Engine(Store(Path(path))).recipes
    copy_runtime(destination, '0.15.2', BASE, __version__, recipes)
    archive = destination / f'ENGE-SPX-Runtime-linux-amd64-{__version__}.tar.gz'
    Docker('default').run('load', '--input', str(archive), timeout=240)
    print('Loaded SHA-256 verified images for the workspace integration checks.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
