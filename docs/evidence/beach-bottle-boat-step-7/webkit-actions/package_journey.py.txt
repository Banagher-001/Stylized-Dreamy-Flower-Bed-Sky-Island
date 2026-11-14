"""Start and stop only the independently extracted package's own preview processes."""
import os,socket,subprocess,time,urllib.request
from common import *
assert read(OUT/'package-validation.json')['complete'];assert not(OUT/'package-preview-cleanup.json').exists();site=Path(read(OUT/'package-validation.json')['archives']['site']['path']);processes=[];records=[];streams=[]
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 fields=(p/'stat').read_text().split(') ')[1].split();return {'pid':pid,'argv':(p/'cmdline').read_bytes().decode().strip('\0').split('\0'),'startTicks':fields[19]}
try:
 origins=[]
 for label,base in[('root','/'),('prefix','/portfolio-check/')]:
  number=port();url=f'http://127.0.0.1:{number}'+base;argv=['node','scripts/preview-site.mjs','--port',str(number),'--base',base,'--strict-port','--json'];stream=(OUT/('package-preview-'+label+'.log')).open('w');streams.append(stream);p=subprocess.Popen(argv,cwd=site,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True);processes.append(p);time.sleep(.2);record=identity(p.pid);assert record and p.poll()is None;records.append({'name':label,**record,'url':url});origins.append(url);deadline=time.monotonic()+20
  while True:
   try:
    with urllib.request.urlopen(url+'experiments/bottle-ocean/index.html',timeout=3)as response:assert hashlib.sha256(response.read()).hexdigest()==ENTRY_SHA
    break
   except Exception:assert time.monotonic()<deadline and p.poll()is None;time.sleep(.2)
 write(OUT/'package-preview-started.json',{'startedAtShanghai':now(),'siteDirectory':str(site),'processes':records})
 argv=['python',str(TEST/'journey.py'),'--run','package-journey','--site-url',origins[0],'--prefix-url',origins[1]];result=subprocess.run(argv,cwd=ROOT);assert result.returncode==0,'Extracted package journey requires review'
finally:
 stopped=[]
 for record,p in zip(records,processes):
  current=identity(p.pid)
  if current:assert all(current[k]==record[k]for k in['pid','argv','startTicks']);p.terminate()
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
  stopped.append({'name':record['name'],'pid':p.pid,'identityChecked':True,'stopped':p.poll()is not None})
 for stream in streams:stream.close()
 write(OUT/'package-preview-cleanup.json',{'finishedAtShanghai':now(),'services':stopped,'otherServicesStopped':False});print(json.dumps({'packagePreviewServicesStopped':len(stopped)}),flush=True)
