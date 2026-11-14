"""Reuse the immutable 0.15.0 runtime only for a verified UI-only hotfix."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = '6985150d63e52bae23e80b329e2a7812544658b7'
PROJECT = 'https://github.com/engeeeee/ENGE-SPX'
PREVIOUS = '0.15.0'


def check_scope():
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD', '--', 'src', 'requirements.txt', 'requirements-build.txt', 'pyproject.toml', 'packaging'], cwd=ROOT, text=True).splitlines()
    allowed = {'src/enge_spx/__init__.py', 'src/enge_spx/ui/controller.py', 'src/enge_spx/ui/window.py',
               'packaging/windows/Installer.iss', 'packaging/windows/version-info.txt', 'packaging/windows/cli-version-info.txt'}
    assert set(files) <= allowed, 'Core, dependencies or runtime changed; UI-only reuse is forbidden'
    for filename, allowed_methods in [('src/enge_spx/ui/controller.py', {'Controller.prepared', 'Controller.check_docker'}),
                                      ('src/enge_spx/ui/window.py', {'Window.build_settings'})]:
        def methods(source):
            result = {}
            for item in ast.parse(source).body:
                if isinstance(item, ast.ClassDef):
                    for method in item.body:
                        if isinstance(method, ast.FunctionDef):
                            result[item.name + '.' + method.name] = ast.dump(method, include_attributes=False)
            return result
        before = methods(subprocess.check_output(['git', 'show', BASE + ':' + filename], cwd=ROOT, text=True))
        after = methods((ROOT / filename).read_text())
        assert all(key in allowed_methods or before.get(key) == after.get(key) for key in before.keys() | after.keys()), 'Changes exceed startup/UI scope'


class SecureRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if not newurl.startswith('https://') or request.has_header('Authorization'):
            raise ValueError('Unexpected update redirect')
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch(url, maximum, api=False):
    headers = {'User-Agent': 'ENGE-SPX-UI-Hotfix'}
    if api and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    opener = urllib.request.build_opener(SecureRedirect())
    with opener.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
        body = response.read(maximum + 1)
    assert len(body) <= maximum, 'Metadata limit exceeded'
    return body


def main(destination):
    check_scope()
    sys.path.insert(0, str(ROOT / 'src'))
    from enge_spx import __version__
    assert __version__ == '0.15.1', 'This reuse gate is limited to the reviewed 0.15.1 hotfix'
    release = json.loads(fetch('https://api.github.com/repos/engeeeee/ENGE-SPX/releases/tags/v0.15.0-windows', 256 * 1024, True))
    assert not release['draft'] and not release['prerelease'] and release['target_commitish'] == BASE
    assets = {item['name']: item for item in release['assets']}
    def asset(name, maximum):
        value = assets[name]
        assert value['browser_download_url'] == PROJECT + '/releases/download/v0.15.0-windows/' + name
        assert value['state'] == 'uploaded' and 0 < value['size'] <= maximum
        assert re.fullmatch(r'sha256:[a-f0-9]{64}', value['digest'])
        return value
    manifest_name = 'ENGE-SPX-Runtime-linux-amd64-0.15.0.json'
    information = asset(manifest_name, 65536)
    raw = fetch(information['browser_download_url'], 65536)
    assert hashlib.sha256(raw).hexdigest() == information['digest'][7:]
    meta = json.loads(raw)
    assert meta['schema'] == 1 and meta['version'] == PREVIOUS and meta['platform'] == 'linux/amd64'
    assert meta['recipes'] == {'gateway': '9aa8a7818569', 'work': '6e3fcfa5633c', 'browser': '1bca0984bc51'}
    for key in ('images', 'image_configs'):
        assert set(meta[key]) == {'gateway', 'work', 'browser'} and all(re.fullmatch(r'sha256:[a-f0-9]{64}', item) for item in meta[key].values())
    name = 'ENGE-SPX-Runtime-linux-amd64-0.15.0.tar.gz'
    archive = asset(name, 2 * 1024**3)
    assert archive['digest'] == 'sha256:' + meta['sha256'] and archive['size'] == meta['bytes'] and meta['filename'] == name
    checksum = asset(name + '.sha256', 512)
    assert fetch(checksum['browser_download_url'], 512).decode().strip() == meta['sha256'] + '  ' + name
    destination.mkdir(parents=True, exist_ok=True)
    output_name = name.replace(PREVIOUS, __version__)
    output = destination / output_name
    count, sha = 0, hashlib.sha256()
    with urllib.request.build_opener(SecureRedirect()).open(archive['browser_download_url'], timeout=90) as response, output.open('wb') as stream:
        while data := response.read(1024 * 1024):
            count += len(data)
            assert count <= meta['bytes']
            stream.write(data)
            sha.update(data)
    assert count == meta['bytes'] and sha.hexdigest() == meta['sha256'], 'Published runtime digest differs'
    meta.update(version=__version__, filename=output_name, reused_from='v0.15.0-windows')
    (destination / output_name.replace('.tar.gz', '.json')).write_text(json.dumps(meta, indent=2) + '\n')
    (destination / (output_name + '.sha256')).write_text(meta['sha256'] + '  ' + output_name + '\n')
    print(json.dumps({'ui_scope_verified': True, 'runtime_reused_from': PREVIOUS, 'bytes': count, 'sha256': sha.hexdigest()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.output)
