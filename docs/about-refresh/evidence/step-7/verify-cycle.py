from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,os,json,time,hashlib,traceback,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]);shutil.copy2(__file__,run/'verify-cycle.py.txt')
MONITOR=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),slots=[...rail.querySelectorAll('.ar-tool-slot')],base=new Map(),last=new Map();window.__cycleEvidence={recycles:[],seam:[],maxFrameGap:0};const rect=e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]};let previous=performance.now(),active=true;window.__stopCycleMonitor=()=>active=false;
 function frame(now){const d=root.dataset,period=Number(d.trackPeriod),r=rect(rail),phase=Number(d.trackOffset),cycle=Number(d.trackCycles);__cycleEvidence.maxFrameGap=Math.max(__cycleEvidence.maxFrameGap,now-previous);previous=now;
 for(const [i,slot] of slots.entries()){const id=slot.dataset.cardId,card=slot.querySelector('.ar-tool-card'),dx=parseFloat(slot.style.transform.split('(')[1])||0;const old=last.get(id);if(!base.has(id))base.set(id,card.dataset.cardInstance);if(base.get(id)!==card.dataset.cardInstance)throw Error('Card instance replaced');
 const raw=slot.offsetLeft+dx,near=raw<100||raw>rail.clientWidth-400&&raw<rail.clientWidth+300;const bounds=near?rect(card.querySelector('.ar-card-front')):null;
 if(old&&Math.abs(dx-old.dx)>period/2)__cycleEvidence.recycles.push({id,time:now,old:old.bounds,next:bounds,rail:r,delta:dx-old.dx});
 last.set(id,{dx,bounds:bounds||old?.bounds});}
 if(phase>period-100||cycle>0&&phase<85)__cycleEvidence.seam.push({time:now,phase,cycle,rail:r,cards:slots.filter(s=>['vibe-coding','midjourney','comfyui'].includes(s.dataset.cardId)).map(s=>({id:s.dataset.cardId,front:rect(s.querySelector('.ar-card-front'))}))});
 if(active)requestAnimationFrame(frame);}requestAnimationFrame(frame);}'''
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),r=rail.getBoundingClientRect();return {now:performance.now(),state:{...root.dataset},count:root.querySelectorAll('.ar-tool-card').length,ids:[...root.querySelectorAll('.ar-tool-card')].map(e=>e.dataset.toolId),instances:[...root.querySelectorAll('.ar-tool-card')].map(e=>e.dataset.cardInstance),visible:[...root.querySelectorAll('.ar-tool-card')].filter(e=>{const b=e.querySelector('.ar-card-front').getBoundingClientRect();return b.right>r.left&&b.left<r.right}).map(e=>e.dataset.toolId),overflow:document.documentElement.scrollWidth-innerWidth};}'''
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'complete':False,'samples':[],'errors':[],'clockModified':False,'configuredSpeed':28};seen=set()
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['version']=browser.version
 ctx=browser.new_context(viewport={'width':1440,'height':900},record_video_dir=str(run/'video'),record_video_size={'width':1440,'height':900});p=ctx.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
 try:
  p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
  p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackMode==="program"',timeout=20000);p.evaluate(MONITOR)
  initial=p.evaluate(READ);identities=initial['instances'];ids=initial['ids'];assert initial['count']==len(set(ids))==22;deadline=time.monotonic()+290;seam_saved=False
  while time.monotonic()<deadline:
   data=p.evaluate(READ);assert data['count']==22 and data['ids']==ids and data['instances']==identities;assert data['state']['trackState']=='running' and data['overflow']<=1
   seen.update(data['visible']);report['samples'].append(data)
   if float(data['state']['trackOffset'])>float(data['state']['trackPeriod'])-120 and not seam_saved:p.screenshot(path=str(run/'before-seam.png'));seam_saved=True
   if int(data['state']['trackCycles'])>=1 and float(data['state']['trackOffset'])>=85:break
   if len(report['samples'])%10==0:save(run/'progress.json',{'samples':len(report['samples']),'offset':data['state']['trackOffset'],'cycles':data['state']['trackCycles'],'seen':len(seen),'running':True})
   p.wait_for_timeout(1000)
  else:raise AssertionError('A natural full cycle did not complete in 290 seconds')
  p.evaluate('__stopCycleMonitor()');motion=p.evaluate('__cycleEvidence');save(run/'frame-evidence.json',motion);assert not report['errors'],report['errors'];assert seen==set(ids),(seen,ids)
  for rec in motion['recycles']:
   assert rec['old'] is not None
   assert rec['old'][2]<rec['rail'][0]-5 or rec['old'][0]>rec['rail'][2]+5,rec
  assert len(motion['recycles'])>=20,len(motion['recycles'])
  before=[f for f in motion['seam'] if f['cycle']==0];after=[f for f in motion['seam'] if f['cycle']>=1];assert before and after
  a,b=before[-1],after[0];gap=(b['time']-a['time'])/1000
  for id in ['midjourney','comfyui']:
   x=next(c for c in a['cards'] if c['id']==id)['front'][0];y=next(c for c in b['cards'] if c['id']==id)['front'][0];assert abs(y-x)<28*gap*1.5+2,(id,x,y,gap)
  p.screenshot(path=str(run/'after-seam.png'));report.update(complete=True,seenIDs=sorted(seen),recycles=len(motion['recycles']),seamGapMS=gap*1000,naturalDurationSeconds=(data['now']-initial['now'])/1000,initial=initial,final=data)
 except Exception as e:
  report.update(failure=str(e),traceback=traceback.format_exc())
  try:p.screenshot(path=str(run/'failure.png'));report['final']=p.evaluate(READ)
  except Exception:pass
 finally:ctx.close();browser.close();report['browserClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'complete':report['complete'],'failure':report.get('failure'),'seconds':report.get('naturalDurationSeconds'),'seen':len(seen),'recycles':report.get('recycles')},ensure_ascii=False));raise SystemExit(0 if report['complete'] else 1)
