from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,subprocess,time,json,socket,signal
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
assert not (OUT/'services-started.json').exists()
deps='/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu'
display=next(':'+str(n) for n in range(133,160) if not Path('/tmp/.X'+str(n)+'-lock').exists() and not Path('/tmp/.X11-unix/X'+str(n)).exists())
env=os.environ.copy();env.update(DISPLAY=display,LD_LIBRARY_PATH=deps,LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='3')
processes=[];streams=[];origin=''
try:
 log=(OUT/'display-service.txt').open('w');streams.append(log)
 xv=subprocess.Popen(['/workspace/.cache/browser-deps/root/usr/bin/Xvfb',display,'-screen','0','1920x1200x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);processes.append(xv)
 node=subprocess.Popen(['node',str(ROOT/'scripts/preview-site.mjs'),'--dir',str(ROOT/'dist'),'--port','0','--strict-port','--json'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True);processes.append(node)
 lines=[]
 while True:
  line=node.stdout.readline();lines.append(line)
  if line.startswith('SAKAN_PREVIEW_READY '):origin=json.loads(line.split(' ',1)[1])['url'].rstrip('/');break
  assert node.poll() is None,lines
 (OUT/'server-service.txt').write_text(''.join(lines))
 state={'origin':origin,'display':display,'browserEnvironment':{k:env[k] for k in ['DISPLAY','LD_LIBRARY_PATH','LIBGL_ALWAYS_SOFTWARE','LP_NUM_THREADS']},'services':[{'pid':p.pid,'processGroup':os.getpgid(p.pid)} for p in processes]}
 (OUT/'services-started.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps({'servicesReady':True,**state}),flush=True)
 while not (OUT/'stop-services').exists():
  assert all(p.poll() is None for p in processes);time.sleep(.3)
finally:
 for p in reversed(processes):
  if p.poll() is None:os.killpg(os.getpgid(p.pid),signal.SIGTERM)
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:os.killpg(os.getpgid(p.pid),signal.SIGKILL);p.wait(timeout=5)
 for s in streams:s.close()
 closed=True
 if origin:
  port=int(origin.rsplit(':',1)[1])
  with socket.socket() as probe:probe.settimeout(.5);closed=probe.connect_ex(('127.0.0.1',port))!=0
 (OUT/'services-cleanup.json').write_text(json.dumps({'servicesStopped':len(processes),'portClosed':closed,'otherServicesStopped':False},indent=2)+'\n')
 print(json.dumps({'servicesClosed':True,'portClosed':closed}),flush=True)
