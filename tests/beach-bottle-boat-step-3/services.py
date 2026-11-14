"""Own three temporary services and stop only their verified process identities."""
from pathlib import Path
import os,shutil,signal,socket,subprocess,sys,time,urllib.request
from common import *
parser=__import__('argparse').ArgumentParser();parser.add_argument('action',choices=['run','stop']);args=parser.parse_args()
if args.action=='stop':
 assert(OUT/'services-started.json').exists()and not(OUT/'services-cleanup.json').exists();(OUT/'stop-services').write_text(now());print('Stop requested for owned step-3 services');raise SystemExit
assert not(OUT/'services-started.json').exists()
build=Path(read(OUT/'build.json')['buildRoot']);assert sha(build/'experiments/bottle-ocean/index.html')==ENTRY_SHA
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
devport=port();prodport=port()
while prodport==devport:prodport=port()
display=next(':'+str(n)for n in range(122,140)if not Path('/tmp/.X'+str(n)+'-lock').exists()and not Path('/tmp/.X11-unix/X'+str(n)).exists())
deps='/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu';browserenv={'DISPLAY':display,'LD_LIBRARY_PATH':deps,'LIBGL_ALWAYS_SOFTWARE':'1','LP_NUM_THREADS':'3','PLAYWRIGHT_BROWSERS_PATH':'/workspace/.cache/ms-playwright'}
commands=[('dev',['node',str(ROOT/'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port',str(devport),'--strictPort']),('production',[sys.executable,str(TEST/'serve.py'),'--root',str(build),'--port',str(prodport),'--log',str(OUT/'production-http.jsonl')]),('display',['/workspace/.cache/browser-deps/root/usr/bin/Xvfb',display,'-screen','0','1920x1200x24','-nolisten','tcp'])]
processes=[];rows=[];startup=False;streams=[]
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 try:
  fields=(p/'stat').read_text().split(') ')[1].split();return {'pid':pid,'argv':(p/'cmdline').read_bytes().decode().strip('\0').split('\0'),'startTicks':fields[19],'state':fields[0]}
 except FileNotFoundError:return None
try:
 for name,argv in commands:
  stream=(OUT/(name+'-service.log')).open('w');streams.append(stream);env=os.environ.copy();env['LD_LIBRARY_PATH']=deps
  p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True);processes.append(p);time.sleep(.15);item=identity(p.pid);assert item and p.poll()is None,(name,p.returncode);rows.append({'name':name,**item})
 state={'startedAtShanghai':now(),'services':rows,'devOrigin':'http://127.0.0.1:'+str(devport),'productionOrigin':'http://127.0.0.1:'+str(prodport),'productionPrefix':'/portfolio-check/','buildRoot':str(build),'browserEnvironment':browserenv,'coordinator':identity(os.getpid())}
 deadline=time.monotonic()+30
 for origin in[state['devOrigin'],state['productionOrigin']]:
  while True:
   try:
    with urllib.request.urlopen(origin+'/experiments/bottle-ocean/index.html',timeout=3)as response:assert hashlib.sha256(response.read()).hexdigest()==ENTRY_SHA
    break
   except Exception:
    assert time.monotonic()<deadline,'Service startup timed out';assert all(p.poll()is None for p in processes);time.sleep(.2)
 write(OUT/'services-started.json',state);startup=True;print(json.dumps({'servicesReady':True,'devOrigin':state['devOrigin'],'productionOrigin':state['productionOrigin'],'display':display}),flush=True)
 while not(OUT/'stop-services').exists():assert all(p.poll()is None for p in processes),'Owned service exited unexpectedly';time.sleep(.25)
finally:
 stopped=[]
 for old,p in zip(rows,processes):
  current=identity(p.pid)
  if current and current['state']!='Z':
   assert all(current[k]==old[k]for k in['pid','argv','startTicks']);p.terminate()
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
  stopped.append({'name':old['name'],'pid':old['pid'],'identityChecked':True,'stopped':p.poll()is not None})
 for stream in streams:stream.close()
 remaining=[]
 for path in Path('/proc').iterdir():
  if not path.name.isdigit():continue
  try:
   argv=(path/'cmdline').read_bytes()
   if not any(x in argv for x in[b'/chromium',b'/firefox-',b'WebKitWebProcess',b'playwright/driver']):continue
   env=(path/'environ').read_bytes().split(b'\0');item=identity(int(path.name))
   if('DISPLAY='+display).encode()in env and item and item['state']!='Z':remaining.append(item)
  except(FileNotFoundError,PermissionError):pass
 scratch=Path(read(OUT/'baseline.json')['scratch']);assert scratch.parent==Path('/tmp')and scratch.name.startswith('bottle-ocean-step-3-')and build==scratch/'production'
 manifest=read(OUT/'build.json')['productionManifest'];actual=[row(p,build)for p in sorted(build.rglob('*'))if p.is_file()];assert actual==manifest
 cleanup={'finishedAtShanghai':now(),'startupCompleted':startup,'services':stopped,'ownedBrowsersRemaining':remaining,'productionManifestVerifiedBeforeCleanup':len(actual),'scratch':str(scratch),'scratchRemoved':False,'otherServicesStopped':False}
 if not remaining:shutil.rmtree(scratch);cleanup['scratchRemoved']=not scratch.exists()
 write(OUT/'services-cleanup.json',cleanup);print(json.dumps({'servicesStopped':len(stopped),'remainingBrowsers':len(remaining),'scratchRemoved':cleanup['scratchRemoved']}),flush=True)
