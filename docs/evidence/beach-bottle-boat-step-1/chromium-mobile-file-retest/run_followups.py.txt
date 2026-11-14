"""Targeted repeats for corrected test preconditions; preserve earlier records."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/beach-bottle-boat-step-1/followup-runner';OUT.mkdir(exist_ok=False)
cases=[('compatibility.py','chromium-mobile-file-retest',['--only','LOAD.file,VIEW']),('compatibility.py','firefox-file',['--engine','firefox','--only','LOAD.file']),('visibility_native.py','native-tab-visibility',[])]
results=[]
for filename,name,options in cases:
 argv=[sys.executable,'-u',str(Path(__file__).parent/filename),'--run',name,*options];print('START '+name,flush=True);started=time.monotonic()
 with(OUT/(name+'.log')).open('w')as stream:result=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
 row={'run':name,'argv':argv,'exitCode':result.returncode,'wallSeconds':time.monotonic()-started};results.append(row);(OUT/'suite.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(row,ensure_ascii=False),flush=True)
if any(r['exitCode']for r in results):raise SystemExit(1)
