"""Own two real Node preview servers, an immutable reference server and a private display."""
import argparse,os,shutil,socket,subprocess,sys,time,urllib.request
from common import *
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['run','stop']);args=parser.parse_args()
if args.action=='stop':
 assert(OUT/'services-started.json').exists()and not(OUT/'services-cleanup.json').exists();(OUT/'stop-services').write_text(now());print('Stop requested for owned step-7 services');raise SystemExit
assert not(OUT/'services-started.json').exists();active=read(OUT/'active-build.json');build=Path(active['buildRoot']);scratch=Path(read(OUT/'baseline.json')['scratch'])
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
ports=[]
while len(ports)<3:
 candidate=port()
 if candidate not in ports:ports.append(candidate)
prod,ref,prefix=ports;display=next(':'+str(n)for n in range(122,145)if not Path('/tmp/.X'+str(n)+'-lock').exists()and not Path('/tmp/.X11-unix/X'+str(n)).exists());deps='/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu'
browserenv={'DISPLAY':display,'LD_LIBRARY_PATH':deps,'LIBGL_ALWAYS_SOFTWARE':'1','LP_NUM_THREADS':'3','PLAYWRIGHT_BROWSERS_PATH':'/workspace/.cache/ms-playwright'}
commands=[('production',['node',str(ROOT/'scripts/preview-site.mjs'),'--dir',str(build),'--port',str(prod),'--strict-port','--json']),('reference',[sys.executable,str(TEST/'serve.py'),'--root',str(SOURCE),'--port',str(ref),'--log',str(OUT/'reference-http.jsonl')]),('prefix',['node',str(ROOT/'scripts/preview-site.mjs'),'--dir',str(build),'--port',str(prefix),'--base','/portfolio-check/','--strict-port','--json']),('display',['/workspace/.cache/browser-deps/root/usr/bin/Xvfb',display,'-screen','0','1920x1200x24','-nolisten','tcp'])]
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  fields=(p/'stat').read_text().split(') ')[1].split();return {'pid':pid,'argv':(p/'cmdline').read_bytes().decode().strip('\0').split('\0'),'startTicks':fields[19],'state':fields[0]}
 except FileNotFoundError:return None
processes=[];rows=[];streams=[];startup=False
try:
 for name,argv in commands:
  stream=(OUT/(name+'-service.log')).open('w');streams.append(stream);env=os.environ.copy();env['LD_LIBRARY_PATH']=deps;p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True);processes.append(p);time.sleep(.15);i=identity(p.pid);assert i and p.poll()is None,(name,p.returncode);rows.append({'name':name,**i})
 state={'startedAtShanghai':now(),'services':rows,'productionOrigin':f'http://127.0.0.1:{prod}','referenceOrigin':f'http://127.0.0.1:{ref}','prefixOrigin':f'http://127.0.0.1:{prefix}','prefix':'/portfolio-check/','buildRoot':str(build),'browserEnvironment':browserenv,'coordinator':identity(os.getpid())}
 deadline=time.monotonic()+30
 for url in[state['productionOrigin']+'/experiments/bottle-ocean/index.html',state['referenceOrigin']+'/index.html',state['prefixOrigin']+'/portfolio-check/experiments/bottle-ocean/index.html']:
  while True:
   try:
    with urllib.request.urlopen(url,timeout=3)as response:assert hashlib.sha256(response.read()).hexdigest()==ENTRY_SHA
    break
   except Exception:
    assert time.monotonic()<deadline and all(p.poll()is None for p in processes);time.sleep(.2)
 write(OUT/'services-started.json',state);startup=True;print(json.dumps({'servicesReady':True,'productionOrigin':state['productionOrigin'],'referenceOrigin':state['referenceOrigin'],'prefixOrigin':state['prefixOrigin'],'display':display}),flush=True)
 while not(OUT/'stop-services').exists():assert all(p.poll()is None for p in processes);time.sleep(.25)
finally:
 stopped=[]
 for old,p in zip(rows,processes):
  current=identity(p.pid)
  if current and current['state']!='Z':assert all(current[k]==old[k]for k in['pid','argv','startTicks']);p.terminate()
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
  stopped.append({'name':old['name'],'pid':old['pid'],'identityChecked':True,'stopped':p.poll()is not None})
 for stream in streams:stream.close()
 remaining=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   argv=(proc/'cmdline').read_bytes()
   if not any(v in argv for v in[b'/chromium',b'/firefox-',b'WebKitWebProcess',b'playwright/driver']):continue
   env=(proc/'environ').read_bytes().split(b'\0');item=identity(int(proc.name))
   if('DISPLAY='+display).encode()in env and item and item['state']!='Z':remaining.append(item)
  except(FileNotFoundError,PermissionError):pass
 verified=[]
 for record in OUT.glob('build-*.json'):
  info=read(record);target=Path(info['buildRoot']);assert target.parent==scratch and tree(target,target)==info['productionManifest'];verified.append({'record':record.name,'files':len(info['productionManifest'])})
 assert scratch.parent==Path('/tmp')and scratch.name.startswith('bottle-ocean-step-7-')
 cleanup={'finishedAtShanghai':now(),'startupCompleted':startup,'services':stopped,'ownedBrowsersRemaining':remaining,'buildsVerifiedBeforeCleanup':verified,'scratch':str(scratch),'scratchRemoved':False,'otherServicesStopped':False}
 if not remaining:shutil.rmtree(scratch);cleanup['scratchRemoved']=not scratch.exists()
 write(OUT/'services-cleanup.json',cleanup);print(json.dumps({'servicesStopped':len(stopped),'remainingBrowsers':len(remaining),'scratchRemoved':cleanup['scratchRemoved']}),flush=True)
