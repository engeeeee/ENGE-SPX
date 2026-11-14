"""Opt-in regional locales using verified exits and ordinary browser policies.

No fingerprint scripts, host language changes, fonts or third-party downloads.
All locale data comes from the already installed glibc locales package.
"""
import io
import ipaddress
import json
import subprocess
import tarfile

from .state import SPXError

MODES = ('unchanged', 'line', 'exit')
COUNTRIES = {
    'US': ('en_US', 'en-US'), 'GB': ('en_GB', 'en-GB'), 'JP': ('ja_JP', 'ja-JP'),
    'KR': ('ko_KR', 'ko-KR'), 'DE': ('de_DE', 'de-DE'), 'FR': ('fr_FR', 'fr-FR'),
    'NL': ('nl_NL', 'nl-NL'), 'CA': ('en_CA', 'en-CA'), 'AU': ('en_AU', 'en-AU'),
    'NZ': ('en_NZ', 'en-NZ'), 'SG': ('en_SG', 'en-SG'), 'HK': ('zh_HK', 'zh-HK'),
    'TW': ('zh_TW', 'zh-TW'), 'CN': ('zh_CN', 'zh-CN'), 'IN': ('en_IN', 'en-IN'),
    'IT': ('it_IT', 'it-IT'), 'ES': ('es_ES', 'es-ES'), 'PT': ('pt_PT', 'pt-PT'),
    'BR': ('pt_BR', 'pt-BR'), 'RU': ('ru_RU', 'ru-RU'), 'SE': ('sv_SE', 'sv-SE'),
    'NO': ('nb_NO', 'nb-NO'), 'FI': ('fi_FI', 'fi-FI'), 'DK': ('da_DK', 'da-DK'),
    'PL': ('pl_PL', 'pl-PL'), 'CH': ('de_CH', 'de-CH'), 'AT': ('de_AT', 'de-AT'),
    'IE': ('en_IE', 'en-IE'), 'TH': ('th_TH', 'th-TH'), 'VN': ('vi_VN', 'vi-VN'),
    'MY': ('ms_MY', 'ms-MY'), 'ID': ('id_ID', 'id-ID'), 'TR': ('tr_TR', 'tr-TR'),
    'MX': ('es_MX', 'es-MX'), 'PH': ('en_PH', 'en-PH'), 'IL': ('he_IL', 'he-IL'),
    'AE': ('ar_AE', 'ar-AE'), 'ZA': ('en_ZA', 'en-ZA'),
}
LOCALE_ROOT = '/tmp/spx-locales-v1'


def mode(settings):
    value = settings.get('language_mode', 'unchanged')
    if value not in MODES:
        raise SPXError('容器语言模式无效，请在偏好设置中重新选择。')
    return value


def selection(country):
    if not isinstance(country, str) or country not in COUNTRIES:
        raise SPXError('该出口地区暂未提供默认语言，请选择保持现有语言，或使用另一种出口来源。')
    name, tag = COUNTRIES[country]
    return {'schema': 1, 'country_code': country, 'locale': name + '.UTF-8', 'tag': tag}


def resolved(settings):
    if mode(settings) == 'unchanged':
        return None
    value = settings.get('environment_language')
    if not isinstance(value, dict):
        raise SPXError('容器语言尚未按当前出口核验，请重新检查连接。')
    expected = selection(value.get('country_code'))
    if any(value.get(key) != item for key, item in expected.items()) or value.get('mode') != mode(settings):
        raise SPXError('容器语言与已确认设置不一致，请重新检查连接。')
    return value


GEO = '''import ipaddress,json,os,sys,urllib.request,urllib.parse
for key in tuple(os.environ):
 if key.lower() in ('http_proxy','https_proxy','all_proxy','no_proxy'): os.environ.pop(key,None)
address=str(ipaddress.IPv4Address(sys.argv[2]))
assert ipaddress.ip_address(address).is_global
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,request,fp,code,msg,headers,newurl):
  parsed=urllib.parse.urlsplit(newurl)
  if parsed.scheme!='https' or parsed.hostname!='ipwho.is' or parsed.username or parsed.password: raise ValueError('invalid geography redirect')
  return super().redirect_request(request,fp,code,msg,headers,newurl)
opener=urllib.request.build_opener(Redirect(),urllib.request.ProxyHandler({'http':sys.argv[1],'https':sys.argv[1]}))
with opener.open('https://ipwho.is/'+address,timeout=12) as response:
 raw=response.read(32769)
assert len(raw)<=32768
geo=json.loads(raw)
assert geo.get('success') is True and geo.get('ip')==address
print(json.dumps({'ip':address,'country_code':geo.get('country_code')}))
'''


def apply_verified_exit(engine, state, evidence):
    settings = engine.store.settings()
    language_mode = mode(settings)
    if language_mode == 'unchanged':
        return None
    key = 'line_ip' if language_mode == 'line' else 'ip'
    try:
        address = str(ipaddress.IPv4Address(evidence[key]))
        if not ipaddress.ip_address(address).is_global:
            raise ValueError()
    except (KeyError, ValueError, TypeError) as error:
        raise SPXError('没有取得所选语言来源的有效出口；未启用第一跳时请选择跟随落地出口。') from error
    try:
        value = json.loads(engine.docker.run('exec', state['session'], 'python3', '-I', '-c', GEO,
                                            state['proxy'], address, timeout=18))
        if value.get('ip') != address:
            raise ValueError()
        language = {**selection(value.get('country_code')), 'mode': language_mode, 'source_ip': address}
    except (ValueError, TypeError, AttributeError, SPXError) as error:
        raise SPXError('出口地区语言查询失败，未启用工作区。可重试或在偏好设置选择保持现有语言；不会改为直连查询。') from error
    settings['environment_language'] = language
    engine.store.write('settings.json', settings)
    engine.log('环境语言已选择 ' + language['tag'] + '；中文输入和 Windows 语言保持。')
    return language


def verify(engine, evidence):
    settings = engine.store.settings()
    value = resolved(settings)
    if value is not None and value.get('source_ip') != evidence.get('line_ip' if mode(settings) == 'line' else 'ip'):
        raise SPXError('语言来源出口发生变化，请重新检查并确认；未启用工作区。')


def environment(settings, browser=False):
    value = resolved(settings)
    if value is None:
        if not settings.get('environment_language'):
            return []
        return [part for key, value in {'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'LC_CTYPE': 'en_US.UTF-8', 'LC_MESSAGES': '', 'LANGUAGE': '', 'LOCPATH': ''}.items() for part in ('--env', key + '=' + value)]
    name = value['locale']
    # LC_ALL from the old image must not override the selected LANG. CLI
    # diagnostics stay English; UTF-8/CJK input does not depend on message locale.
    values = {'LANG': name, 'LC_ALL': name if browser else '',
              'LC_CTYPE': name, 'LC_MESSAGES': name if browser else 'C',
              'LANGUAGE': value['tag'].split('-')[0] if browser else 'en',
              'LOCPATH': '/usr/lib/locale' if browser else LOCALE_ROOT}
    return [part for key, value in values.items() for part in ('--env', key + '=' + value)]


PREPARE_PROJECT = '''import json,locale,os,subprocess,sys,tempfile
from pathlib import Path
name=sys.argv[1];root=Path('/tmp/spx-locales-v1')
assert not root.is_symlink()
root.mkdir(mode=0o755,exist_ok=True)
assert root.is_dir() and root.stat().st_uid==os.getuid()
target=root/name
assert not target.is_symlink()
if not target.exists():
 with tempfile.TemporaryDirectory(prefix='.build-',dir=root) as temp:
  output=Path(temp)/name
  subprocess.run(['/usr/bin/localedef','--no-archive','-i',name.split('.')[0],'-f','UTF-8',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25)
  os.rename(output,target)
os.environ['LOCPATH']=str(root)
locale.setlocale(locale.LC_CTYPE,name)
assert 'UTF' in locale.nl_langinfo(locale.CODESET).upper()
print(json.dumps({'locale':name,'utf8':True}))
'''


def prepare_project(engine, obj):
    settings = engine.store.settings()
    value = resolved(settings)
    if value is None and not settings.get('environment_language'):
        return
    engine.owned(obj, 'project')
    try:
        if value:
            result = json.loads(engine.docker.run('exec', obj['Id'], 'python3', '-I', '-c', PREPARE_PROJECT,
                                                 value['locale'], timeout=35))
            if result != {'locale': value['locale'], 'utf8': True}:
                raise ValueError()
        # Fixed public configuration file only; never mount a host directory or
        # execute the workspace as root. Existing project/identity layers remain.
        body = (('LANG=' + value['locale'] + '\nLC_ALL=\nLC_CTYPE=' + value['locale'] +
                 '\nLC_MESSAGES=C\nLANGUAGE=en\nLOCPATH=' + LOCALE_ROOT + '\n') if value else
                'LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8\nLC_CTYPE=en_US.UTF-8\nLC_MESSAGES=\nLANGUAGE=\nLOCPATH=\n').encode('ascii')
        matches = engine.docker.run('exec', obj['Id'], 'python3', '-I', '-c',
                                   "from pathlib import Path;import sys;p=Path('/etc/default');assert p.is_dir() and not p.is_symlink();f=p/'locale';assert not f.is_symlink();print('yes' if f.is_file() and f.read_bytes()==sys.argv[1].encode('ascii') else 'no')",
                                   body.decode('ascii'), timeout=8)
        if matches.strip() == 'yes':
            return
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            entry = tarfile.TarInfo('locale')
            entry.size, entry.mode, entry.uid, entry.gid = len(body), 0o644, 0, 0
            archive.addfile(entry, io.BytesIO(body))
        result = subprocess.run(engine.docker.command('cp', '-', obj['Id'] + ':/etc/default'), input=data.getvalue(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12,
                                env=engine.docker.environment(), creationflags=subprocess.CREATE_NO_WINDOW if __import__('os').name == 'nt' else 0)
        if result.returncode:
            raise ValueError()
        actual = engine.docker.run('exec', obj['Id'], 'python3', '-I', '-c', "from pathlib import Path;print(Path('/etc/default/locale').read_text(),end='')", timeout=8)
        if actual.rstrip('\n') != body.decode('ascii').rstrip('\n'):
            raise ValueError()
    except (ValueError, SPXError, OSError, subprocess.TimeoutExpired) as error:
        raise SPXError('工作区 UTF-8 语言准备失败，未启动 CLI；项目及账号数据保留，请重试或保持现有语言。') from error


BROWSER_PREPARE = '''
import json,locale,subprocess
name,tag=sys.argv[2:4]
subprocess.run(['/usr/bin/localedef','--no-archive','-i',name.split('.')[0],'-f','UTF-8','/usr/lib/locale/'+name],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25)
os.environ['LOCPATH']='/usr/lib/locale'
locale.setlocale(locale.LC_ALL,name)
assert 'UTF' in locale.nl_langinfo(locale.CODESET).upper()
directory=Path('/etc/chromium/policies/managed')
directory.mkdir(parents=True,exist_ok=True)
policy=directory/'spx-language.json'
assert not policy.is_symlink()
policy.write_text(json.dumps({'ForcedLanguages':[tag]}),encoding='utf-8')
os.chmod(policy,0o644)
Path('/etc/default/locale').write_text('LANG='+name+'\\nLC_ALL='+name+'\\n',encoding='ascii')
'''
