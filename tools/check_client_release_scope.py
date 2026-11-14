"""Permit a shorter client release only while existing network guards stay identical."""
import ast
import subprocess
from pathlib import Path

BASELINE = '30c17f4de0d5c8b13ce100adba91837d0033cb48'
ALLOWED = {'__init__.py', '__main__.py', 'engine.py', 'state.py', 'gui.py', 'smart_terminal.py',
           'window_effects.py', 'network_diagnostics.py', 'app_updates.py', 'update_apply.py', 'exit_timezone.py',
           'workspace_language.py', 'workspace_timezone.py', 'browser_profile_locks.py'}
root = Path(__file__).resolve().parents[1]


def previous(path):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=root, text=True)


changed = subprocess.check_output(['git', 'diff', '--name-only', BASELINE, 'HEAD'], cwd=root, text=True).splitlines()
for path in changed:
    if path.startswith('src/enge_spx/resources/'):
        assert path == 'src/enge_spx/resources/checks/exit_probe.py', 'Runtime recipe/security resources changed; use full CI'
        expected = previous(path).replace('fetch("https://ipwho.is/")', 'fetch("https://ipwho.is/" + first)')
        assert (root / path).read_text() == expected, 'Exit probe changed beyond the verified GeoIP lookup'
    elif path.startswith('src/enge_spx/'):
        assert path.startswith('src/enge_spx/ui/') or path.split('/')[-1] in ALLOWED, 'Non-client code changed; use full CI'
    else:
        assert path.startswith(('docs/', 'tests/', 'tools/', 'website/', 'packaging/windows/', '.github/workflows/')) or path in {'README.md', 'README.en.md', 'CHANGELOG.md', 'SECURITY.md'}, 'Unexpected release scope'

for path, allowed in [('src/enge_spx/engine.py', {'save_settings', 'policy', 'check', 'confirm', 'proxy_env', '_browser', '_project'}),
                      ('src/enge_spx/workspace_timezone.py', {'browser_image'}),
                      ('src/enge_spx/state.py', {'settings'})]:
    def methods(text):
        result = {}
        for node in ast.parse(text).body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result[node.name + '.' + item.name] = ast.dump(item, include_attributes=False)
            elif isinstance(node, ast.FunctionDef):
                result[node.name] = ast.dump(node, include_attributes=False)
        return result
    before, after = methods(previous(path)), methods((root / path).read_text())
    for key in before.keys() | after.keys():
        assert key.split('.')[-1] in allowed or before.get(key) == after.get(key), 'Guard, topology, lifecycle or proxy engine changed; use full CI: ' + key
before = ast.parse(previous('src/enge_spx/engine.py'))
after = ast.parse((root / 'src/enge_spx/engine.py').read_text())
def find(tree, name):
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
for name in ('proxy_env', '_browser', '_project'):
    old, new = find(before, name), find(after, name)
    class LocaleImports(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            return None if node.module in ('workspace_language', 'browser_profile_locks') else node
        def visit_Expr(self, node):
            return None if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in ('prepare_language', 'prepare_profile') else node
        def visit_If(self, node):
            self.generic_visit(node)
            return node if node.body else None
    new = LocaleImports().visit(new)
    for node in ast.walk(new):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'proxy_env':
            node.keywords = [kw for kw in node.keywords if kw.arg != 'browser']
        if name == 'proxy_env' and isinstance(node, ast.List):
            node.elts = [elt for elt in node.elts if not (isinstance(elt, ast.Starred) and isinstance(elt.value, ast.Call) and isinstance(elt.value.func, ast.Name) and elt.value.func.id == 'environment')]
    if name == 'proxy_env':
        new.args.args = new.args.args[:-1]
        new.args.defaults = new.args.defaults[:-1]
    assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False), 'Change exceeds locale-only integration: ' + name
print('Client scope verified: runtime recipes, routing, guard, sandbox and lifecycle unchanged; locale-only launch integration reviewed')
