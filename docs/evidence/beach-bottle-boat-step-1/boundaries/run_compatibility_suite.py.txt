"""Serialize software-rendered browsers; retain all failed run output."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/beach-bottle-boat-step-1/runner';OUT.mkdir(exist_ok=False)
cases=[('compatibility.py','chromium-compat',[]),('compatibility.py','firefox-compat',['--engine','firefox']),('compatibility.py','webkit-compat',['--engine','webkit']),('failures.py','webgl-disabled',['--no-webgl']),('failures.py','failures',[]),('boundaries.py','boundaries',[])]
results=[]
for filename,name,options in cases:
 argv=[sys.executable,'-u',str(Path(__file__).parent/filename),'--run',name,*options];print('START '+name,flush=True);started=time.monotonic()
 with(OUT/(name+'.log')).open('w')as stream:result=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
 row={'run':name,'argv':argv,'exitCode':result.returncode,'wallSeconds':time.monotonic()-started};results.append(row);(OUT/'suite.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(row,ensure_ascii=False),flush=True)
if any(r['exitCode']for r in results):raise SystemExit(1)
