"""Serial final-version regressions after shader optimization; no benchmark.
All subprocess reports must freshly bind to the same frozen build/source bytes.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-6'
build=json.loads((OUT/'build-verification.json').read_text());reports=[]
commands=[(['step6_browser.py','--engine',e],f'browser-{e}.json')for e in ['chromium','firefox','webkit']]
commands += [(['step6_protection.py'],'birds-off-protection.json'),(['step6_native.py'],'native-guide-recovery.json'),(['step6_failure.py'],'failure-and-font.json')]
for args,report in commands:
    subprocess.run([sys.executable,str(ROOT/'tests/garden-enhancement'/args[0]),*args[1:]],cwd=ROOT,check=True)
    d=json.loads((OUT/report).read_text());assert d['passed']and d['candidateId']==build['candidateId']
    reports.append(report)
    (OUT/'regression-progress.json').write_text(json.dumps({'complete':False,'candidateId':build['candidateId'],'completedReports':reports},indent=2)+'\n')
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in build['buildInputsSha256'].items())
(OUT/'fresh-regressions.json').write_text(json.dumps({'passed':True,'candidateId':build['candidateId'],'reports':reports,'method':'all current sources frozen; each engine and GPU/native/failure regression run serially after optimization; historical checks only reused as source, no old output copied'},indent=2)+'\n')
print('PASS all six final-version regression reports',flush=True)
