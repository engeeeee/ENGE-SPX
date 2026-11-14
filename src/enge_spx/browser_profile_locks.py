"""Recover stale Chromium singleton links only before a new owned browser boots."""
import json
import re

from .state import SPXError


RECOVER = '''import json,os
from pathlib import Path
for item in Path('/proc').iterdir():
 if item.name.isdecimal():
  try:
   if 'chrom' in (item/'comm').read_text().strip().lower(): raise RuntimeError('browser already active')
  except (FileNotFoundError,ProcessLookupError):pass
root=Path('/home/workspace/.config')
assert not root.is_symlink()
removed=0
for name in ('chromium-spx','chromium-ewb'):
 profile=root/name
 assert not profile.is_symlink()
 if not profile.exists():continue
 assert profile.is_dir() and profile.stat().st_uid==os.getuid()
 for key in ('SingletonLock','SingletonSocket','SingletonCookie'):
  target=profile/key
  if target.is_symlink():target.unlink();removed+=1
  elif target.exists():raise RuntimeError('unexpected singleton file')
print(json.dumps({'schema':1,'removed':removed}))
'''


def prepare(engine, obj, volume):
    engine.owned(obj, 'browser')
    current = obj['Id']
    output = engine.docker.run('ps', '--all', '--no-trunc', '--filter', 'volume=' + volume, '--format', '{{.ID}} {{.State}}', timeout=8)
    rows = [row.split() for row in output.splitlines()]
    valid = all(len(row) == 2 and re.fullmatch('[a-f0-9]{64}', row[0]) and row[1] in ('running', 'created', 'exited', 'paused', 'restarting', 'removing', 'dead') for row in rows)
    users = {row[0] for row in rows if len(row) == 2 and row[1] not in ('created', 'exited')}
    if not valid or [current, 'running'] not in rows or not re.fullmatch('[a-f0-9]{64}', current) or users != {current}:
        raise SPXError('浏览器资料仍被其他容器使用，或无法核验使用状态；未清理 Profile 锁。请先正常停止其他浏览器。')
    try:
        result = json.loads(engine.docker.run('exec', current, 'python3', '-I', '-c', RECOVER, timeout=8))
        if result.get('schema') != 1 or type(result.get('removed')) is not int or not 0 <= result['removed'] <= 6:
            raise ValueError()
    except (SPXError, ValueError, AttributeError) as error:
        raise SPXError('无法安全准备浏览器 Profile 锁，未启动浏览器；账号资料已保留。') from error
