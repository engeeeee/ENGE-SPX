from pathlib import Path
import json
import subprocess
import sys
import tempfile

from enge_spx import __version__
from enge_spx.engine import Docker, Engine
from enge_spx.state import Store
from reuse_ui_hotfix_runtime import copy_runtime

SOURCE = 'a1092e5a011b472e166181156383115dc31d4d14'
BASE = '3ee0dde6c06f3ddd1e981ec99272379cca204a91'
assert __version__ == '0.16.3'
subprocess.run(['git', 'diff', '--exit-code', SOURCE, 'HEAD', '--', 'src', 'packaging', 'requirements.txt', 'requirements-build.txt', 'pyproject.toml'], check=True)
subprocess.run(['git', 'diff', '--exit-code', BASE, 'HEAD', '--', 'src/enge_spx/resources/containers', 'src/enge_spx/network_diagnostics.py'], check=True)
archive_dir, evidence = map(Path, sys.argv[1:])
with tempfile.TemporaryDirectory(prefix='spx-released-image-check-') as private:
    engine = Engine(Store(Path(private)))
    copy_runtime(archive_dir, '0.16.2', BASE, __version__, engine.recipes)
    metadata = json.loads((archive_dir / 'ENGE-SPX-Runtime-linux-amd64-0.16.3.json').read_text())
    assert metadata['reused_from'] == 'v0.16.2-windows'
    docker = Docker('default')
    docker.run('load', '--input', str(archive_dir / metadata['filename']), timeout=240)
    images = {}
    for role, reference in metadata['images'].items():
        image = docker.inspect('image', reference) or docker.inspect('image', metadata['image_configs'][role])
        assert engine.compatible_image(image, role) and image.get('Architecture') == 'amd64', role
        images[role] = image['Id']
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({'source': SOURCE, 'runtime_sha256': metadata['sha256'], 'recipes': engine.recipes, 'images': images}, indent=2) + '\n')
