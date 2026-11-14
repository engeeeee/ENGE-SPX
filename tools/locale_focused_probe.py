import hashlib,json,subprocess,urllib.request
from pathlib import Path
base='https://github.com/engeeeee/ENGE-SPX/releases/download/v0.15.1-windows/'
meta=json.load(urllib.request.urlopen(base+'ENGE-SPX-Runtime-linux-amd64-0.15.1.json',timeout=30))
p=Path('/tmp/spx-runtime.tar.gz');h=hashlib.sha256();count=0
with urllib.request.urlopen(base+meta['filename'],timeout=60) as source,p.open('wb') as target:
 while data:=source.read(1024*1024):
  count+=len(data);assert count<=meta['bytes'];h.update(data);target.write(data)
assert count==meta['bytes'] and h.hexdigest()==meta['sha256']
subprocess.run(['docker','load','-i',str(p)],check=True,timeout=180)
p.unlink()
images={}
for role in meta['images']:
 for identifier in (meta['images'][role],meta['image_configs'][role]):
  if subprocess.run(['docker','image','inspect',identifier],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
   images[role]=identifier;break
assert len(images)==3
Path('/tmp/locale-images.json').write_text(json.dumps({'images':images}))
import sys
sys.path.insert(0,'tests')
import enge_spx.workspace_language as lang
lang.BROWSER_PREPARE += "\np=Path('/opt/spx/browser.py');p.write_text(p.read_text().replace('stderr=subprocess.DEVNULL', 'stderr=None'))\n"
from integration_workspace_language import run
run(Path('/tmp/locale-images.json'),Path('/tmp/locale-results.json'))
print(Path('/tmp/locale-results.json').read_text())
