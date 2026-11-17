"""Validate old artifacts, runtime inputs, final archives and repository status."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
baseline=json.loads((OUT/'baseline.json').read_text());build=json.loads((OUT/'build.json').read_text());pack=json.loads((OUT/'packaging-final.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(rows):
    changed=[]
    for f in rows:
        p=ROOT/f['path']
        if not p.is_file() or p.stat().st_size!=f['bytes'] or sha(p)!=f['sha256']:changed.append(f['path'])
    return changed
history=check(baseline['protectedHistory']);runtime=check(build['inputs']);assets=check(baseline['publicAssets'])
changed_sources=check(baseline['sources']);assert changed_sources==['README.md'],changed_sources
assert not history and not runtime and not assets,(history,runtime,assets)
manifest=json.loads(Path(pack['manifest']).read_text())
for kind,a in manifest['artifacts'].items():
    p=ROOT/a['path'];assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        for f in a['files']:
            raw=z.read(f['path']);assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
        if kind=='source':
            for local in (ROOT/'tests/about-refresh-final').glob('*.py'):
                assert z.read('tests/about-refresh-final/'+local.name)==local.read_bytes(),local.name
            assert z.read('scripts/package-about-refresh.py')==(ROOT/'scripts/package-about-refresh.py').read_bytes()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();origin=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
assert head==baseline['head'] and origin==baseline['localOriginMain']
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert diff.returncode==0,diff.stdout+diff.stderr
status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
(OUT/'final-git-status.txt').write_text(status)
result={'checkedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'candidateId':build['candidateId'],'deliveryId':manifest['deliveryId'],'runtimeInputFilesUnchanged':len(build['inputs']),'publicFilesUnchanged':len(baseline['publicAssets']),'historicalFilesUnchanged':len(baseline['protectedHistory']),'baselineFilesChanged':['README.md'],'archiveHashesAndCRC':True,'packagedChecksMatchCurrentFiles':True,'head':head,'originMain':origin,'committed':False,'pushed':False,'deployed':False,'diffCheckPassed':True,'complete':True}
(OUT/'integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
