"""Strict build and source/output identity for the current Step4 candidate."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (OUT/'build.log').open('w')as log:subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
old=json.loads((ROOT/'docs/evidence/garden-enhancement-step-3/build-verification.json').read_text())
inputs={n:sha(ROOT/n)for n in sorted(set(old['buildInputsSha256'])|{'src/tour/autoGuide.ts','src/tour/autoGuide.css'})}
finger=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
result={'passed':True,'candidateId':'garden-enhancement-step4-'+finger[:16],'buildInputFingerprint':finger,
    'buildInputsSha256':inputs,'runtimeSourceSha256':{n:v for n,v in inputs.items()if n.startswith('src/')and n.endswith(('.ts','.css'))},
    'productionSha256':{str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()},
    'command':'npm run build (strict typecheck included)','log':'build.log','exitCode':0,
    'node':subprocess.check_output(['node','-v'],text=True).strip(),'npm':subprocess.check_output(['npm','-v'],text=True).strip(),
    'changedRuntimeSources':[n for n,v in inputs.items()if n.startswith('src/')and old['buildInputsSha256'].get(n)!=v]}
(OUT/'build-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS',result['candidateId'],result['changedRuntimeSources'])
