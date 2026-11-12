"""Confirm corrected observations using new, non-overwriting run names."""
from pathlib import Path
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7';TEST=Path(__file__).parent
path=OUT/'corrections-suite.json';assert not path.exists();results=[]
tasks=[('roof-final-standalone','supplement.py',['--run','roof-final-standalone','--only','BUTTON.roof-actual'],'standalone'),('roof-final-embedded','supplement.py',['--run','roof-final-embedded','--only','BUTTON.roof-actual'],'embedded'),('journey-final','verify_journey.py',['--run','journey-final','--only','journey'],None)]
for name,file,arguments,mode in tasks:
    cmd=[sys.executable,'-u',str(TEST/file),*arguments];env=dict(os.environ)
    if mode:env['LAWSON_MODE']=mode
    log=OUT/(name+'.log');assert not log.exists();print('START '+name,flush=True);started=time.monotonic()
    with log.open('w')as f:
        child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in child.stdout:f.write(line);f.flush();print(line,end='',flush=True)
        code=child.wait()
    results.append({'name':name,'command':cmd,'exitCode':code,'wallSeconds':time.monotonic()-started,'log':log.name});path.write_text(json.dumps({'complete':False,'results':results},ensure_ascii=False,indent=2)+'\n')
path.write_text(json.dumps({'complete':True,'allExitCodesZero':all(r['exitCode']==0 for r in results),'results':results},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(r['exitCode']==0 for r in results)else 1)
