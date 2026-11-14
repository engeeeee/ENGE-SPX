"""Focused real glibc/Chromium locale check; no accounts or public network."""
import argparse
import json
from pathlib import Path
import secrets
import tempfile
import time

from enge_spx.browser_security import arguments, validate_container, validate_status
from enge_spx.engine import Engine
from enge_spx.network_diagnostics import _exec_json, browser_evidence
from enge_spx.state import Store
from enge_spx.workspace_language import environment, prepare_project, selection
from enge_spx.workspace_timezone import browser_image


def run(report, output):
    images = json.loads(report.read_text())['images']
    containers, derived, checks = [], [], []
    with tempfile.TemporaryDirectory(prefix='spx-language-') as folder:
        store = Store(Path(folder) / 'data')
        store.write('settings.json', {**store.settings(), 'context': 'default'})
        engine = Engine(store, print)
        home = engine.prefix + '-locale-browser-home'
        try:
            project = engine.docker.run('run', '-d', '--network', 'none', '--user', '1000:1000',
                                        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                                        '--label', engine.owner + '=' + store.instance, '--label', engine.role + '=project',
                                        images['work'], 'sleep', 'infinity')
            containers.append(project)
            before = engine.inspect('project', project)
            engine.docker.run('exec', project, 'python3', '-c', "from pathlib import Path;Path('/tmp/keep-language-layer').write_text('keep')")
            for country in ('JP', 'US'):
                selected = {**selection(country), 'mode': 'line', 'source_ip': '1.1.1.1'}
                store.write('settings.json', {**store.settings(), 'language_mode': 'line', 'environment_language': selected})
                prepare_project(engine, before)
                script = "import locale;from pathlib import Path;locale.setlocale(locale.LC_ALL,'');assert 'UTF' in locale.nl_langinfo(locale.CODESET).upper();assert '中文输入'.encode('utf-8').decode('utf-8')=='中文输入';assert Path('/tmp/keep-language-layer').read_text()=='keep';print(locale.setlocale(locale.LC_CTYPE))"
                actual = engine.docker.run('exec', *environment(store.settings()), project, 'python3', '-c', script)
                assert actual == selected['locale'], actual
                after = engine.inspect('project', project)
                assert after['Id'] == before['Id'] and after['HostConfig'] == before['HostConfig']
                derived_image = browser_image(engine, images['browser'])
                derived.append(derived_image)
                obj = engine.ensure_container('browser', derived_image, ['--network', 'none', '--shm-size', '512m',
                    *arguments(), '--volume', home + ':/home/workspace', *environment(store.settings(), browser=True)])
                containers.append(obj['Id'])
                validate_container(obj)
                token = secrets.token_hex(32)
                engine.deliver_secret(obj['Id'], 'browser', {'token': token, 'proxy': 'http://127.0.0.1:9', 'legacy': False})
                for attempt in range(60):
                    try:
                        evidence = json.loads(engine.docker.run('exec', obj['Id'], 'python3', '-c', "print(open('/tmp/spx-sandbox-status.json').read())", timeout=3))
                        validate_status(evidence)
                        break
                    except Exception:
                        current = engine.docker.inspect('container', obj['Id'])
                        if current and not current['State'].get('Running'):
                            raise AssertionError('Browser stopped during locale startup: ' + engine.docker.run('logs', obj['Id'])[-2000:])
                        if attempt == 59:
                            raise
                        time.sleep(.25)
                observed = browser_evidence(_exec_json(engine, obj['Id'], 'browser_probe.py', authorization={'token': token}))
                assert observed['status'] == 'observed', observed
                assert observed['language'].split('-')[0] == selected['tag'].split('-')[0], observed
                assert observed['request_languages'][0].split('-')[0] == selected['tag'].split('-')[0], observed
                assert not obj['HostConfig'].get('PortBindings')
                marker = "from pathlib import Path;p=Path('/home/workspace/.spx-language-proof');"
                marker += "assert p.read_text()=='preserved'" if country == 'US' else "p.write_text('preserved')"
                engine.docker.run('exec', obj['Id'], 'python3', '-c', marker)
                checks.append({'country': country, 'locale': actual, 'navigator_language': observed['language'],
                               'request_languages': observed['request_languages'], 'sandbox': 'verified',
                               'project_layer_preserved': True, 'chinese_utf8': True, 'host_ports': 0})
                # Match the product's image switch: SIGTERM lets Chromium
                # remove the persistent Profile's SingletonLock before reuse.
                # A forced delete simulates a crash on another hostname.
                engine.docker.run('stop', obj['Id'], timeout=20)
                engine.docker.run('rm', obj['Id'])
                containers.remove(obj['Id'])
                print('PASS real locale, Chinese UTF-8 and sandboxed Chromium language:', country, flush=True)
            store.write('settings.json', {**store.settings(), 'language_mode': 'unchanged'})
            prepare_project(engine, before)
            assert engine.docker.run('exec', *environment(store.settings()), project, 'locale', 'charmap') == 'UTF-8'
            output.write_text(json.dumps({'schema': 1, 'checks': checks, 'disabled_restores_default': True}, indent=2))
        finally:
            for identifier in reversed(containers):
                engine.docker.run('rm', '-f', identifier)
            for image in dict.fromkeys(derived):
                engine.docker.run('image', 'rm', '-f', image)
            if engine.docker.inspect('volume', home):
                engine.docker.run('volume', 'rm', home)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.runtime_report, args.output)
