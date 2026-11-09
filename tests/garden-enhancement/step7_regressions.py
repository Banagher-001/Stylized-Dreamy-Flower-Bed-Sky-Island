"""Serial final integration checks, freshly bound to the frozen application."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
build=json.loads((OUT/'build-verification.json').read_text());reports=[]
commands=[(['step7_browser.py','--engine',e],f'browser-{e}.json')for e in ['chromium','firefox','webkit']]
commands += [(['step7_safety.py'],'projection-motion-and-depth.json'),(['step7_protection.py'],'complete-scene-protection.json'),
    (['step7_native.py'],'native-guide-recovery.json'),(['step7_failure.py'],'failure-and-font.json'),(['step7_replay.py'],'replay-native-takeover.json')]
commands += [(['step7_faults.py','--engine',e],f'faults-{e}.json')for e in ['chromium','firefox','webkit']]
for args,report in commands:
    subprocess.run([sys.executable,str(ROOT/'tests/garden-enhancement'/args[0]),*args[1:]],cwd=ROOT,check=True)
    d=json.loads((OUT/report).read_text());assert d['passed']and d['candidateId']==build['candidateId'],report
    reports.append(report)
    (OUT/'regression-progress.json').write_text(json.dumps({'complete':False,'candidateId':build['candidateId'],'completedReports':reports},indent=2)+'\n')
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in build['buildInputsSha256'].items())
(OUT/'fresh-regressions.json').write_text(json.dumps({'passed':True,'candidateId':build['candidateId'],'reports':reports,
    'method':'all current application sources frozen; serial new runs on the final build, including three engines and explicit labelled image/decode failure injection; accepted old test sources reused read-only, no historical output copied'},indent=2)+'\n')
print('PASS all11fresh final integration reports',flush=True)
