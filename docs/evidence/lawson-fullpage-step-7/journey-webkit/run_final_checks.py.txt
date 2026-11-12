"""Targeted probe corrections and final host/engine checks, all serial."""
from pathlib import Path
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];TEST=Path(__file__).parent;OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
path=OUT/'final-checks-suite.json';assert not path.exists()
tasks=[
 ('controls-recheck','controls.py',['--run','recheck-embedded-controls'],{'LAWSON_MODE':'embedded'}),
 ('roof-standalone','supplement.py',['--run','recheck-standalone-roof','--only','BUTTON.roof-actual'],{'LAWSON_MODE':'standalone'}),
 ('roof-embedded','supplement.py',['--run','recheck-embedded-roof','--only','BUTTON.roof-actual'],{'LAWSON_MODE':'embedded'}),
 ('retry-standalone','verify_standalone_retry.py',['--run','standalone-native-retry'],{'LAWSON_MODE':'standalone'}),
 ('journey-chromium','verify_journey.py',['--run','journey-chromium'],{}),
 ('recovery-chromium','verify_recovery.py',['--run','recovery-chromium'],{}),
 ('touch-chromium','verify_touch.py',['--run','touch-chromium','--only','touch'],{}),
 ('compat-firefox','verify_journey.py',['--run','journey-firefox','--engine','firefox'],{}),
 ('compat-webkit','verify_journey.py',['--run','journey-webkit','--engine','webkit'],{}),
]
results=[]
for name,file,extra,env in tasks:
    cmd=[sys.executable,'-u',str(TEST/file),*extra];log=OUT/(name+'.log');assert not log.exists();started=time.monotonic();print('START '+name,flush=True)
    with log.open('w')as f:
        child=subprocess.Popen(cmd,cwd=ROOT,env=dict(os.environ,**env),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in child.stdout:f.write(line);f.flush();print(line,end='',flush=True)
        code=child.wait()
    results.append({'name':name,'script':file,'arguments':extra,'exitCode':code,'wallSeconds':time.monotonic()-started,'log':log.name})
    path.write_text(json.dumps({'complete':False,'results':results},ensure_ascii=False,indent=2)+'\n')
path.write_text(json.dumps({'complete':True,'allExitCodesZero':all(c['exitCode']==0 for c in results),'results':results},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(c['exitCode']==0 for c in results)else 1)
