"""Run independent acceptance suites serially and seal their source provenance."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
from step11_common import ROOT,OUT
parser=argparse.ArgumentParser();parser.add_argument('--group',choices=['browser','legacy','final'],required=True);args=parser.parse_args()
def hashes():return{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']}
current=hashes();env=os.environ.copy();env.update(DISPLAY=':100',LIBGL_ALWAYS_SOFTWARE='1',LD_LIBRARY_PATH='/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu',PLAYWRIGHT_BROWSERS_PATH='/workspace/.cache/ms-playwright',COURTYARD_WEBKIT_EXECUTABLE='/workspace/.cache/browser-deps/run-webkit.sh')
tasks=[]
if args.group=='browser':
 for engine in ['chromium','firefox','webkit']:
  for kind,script in [('browser','step11_browser.py'),('dialogs','step11_dialogs.py'),('renderer','step11_renderer.py')]:tasks.append((kind+'-'+engine,[script,'--engine',engine],kind+'-'+engine+'.json'))
elif args.group=='legacy':
 for engine in ['chromium','firefox','webkit']:
  for suite in ['about','films','chapter']:tasks.append((suite+'-'+engine,['step11_regression.py','--suite',suite,'--engine',engine],f'regression-{suite}/'+('about-'if suite=='about'else'')+f'verification-{engine}.json'))
else:
 tasks=[('native-zoom',['step11_native_zoom.py'],'native-zoom.json'),('native-recovery',['step11_recovery.py'],'native-recovery.json'),('overlay-resize',['step11_overlay_resize.py'],'overlay-resize.json'),('media-faults',['step11_faults.py'],'media-faults.json'),('geometry',['step11_geometry.py'],'geometry-continuity.json'),('scope',['step11_scope.py'],'paired-scene-isolation.json')]
runs=[]
for name,command,result in tasks:
 report=OUT/result
 if report.exists()and json.loads(report.read_text()).get('runtimeSourceSha256')==current:
  runs.append({'task':name,'exitCode':0,'alreadyVerifiedFinalRuntime':True,'result':result});print('CURRENT',name,flush=True);continue
 log=OUT/f'run-{name}.log';start=time.time()
 with log.open('w')as output:r=subprocess.run([sys.executable,str(ROOT/'tests/scroll-garden'/command[0]),*command[1:]],env=env,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
 assert hashes()==current,'Runtime changed while test was executing'
 row={'task':name,'exitCode':r.returncode,'elapsedSeconds':time.time()-start,'result':result,'log':log.name};runs.append(row)
 if r.returncode==0:
  data=json.loads(report.read_text());assert data.get('passed'),result;data['runtimeSourceSha256']=current;report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(('PASS'if r.returncode==0 else'FAIL'),name,round(row['elapsedSeconds'],1),'s',flush=True)
 if r.returncode:print('\n'.join(log.read_text().splitlines()[-18:]),flush=True)
 (OUT/f'runs-{args.group}.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
assert all(r['exitCode']==0 for r in runs),[r['task']for r in runs if r['exitCode']]
