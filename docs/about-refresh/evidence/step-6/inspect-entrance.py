from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,argparse,traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--video',action='store_true');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
SAMPLE=r'''() => {const r=document.querySelector('.ar-tools-browser'),rail=r.querySelector('.ar-tool-rail');const rect=e=>{const b=e.getBoundingClientRect();return {left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height}};return {time:performance.now(),browser:{...r.dataset},host:{...document.querySelector('#tour-host').dataset},main:{...document.querySelector('main').dataset},rail:rect(rail),railX:rail.scrollLeft,cards:[...r.querySelectorAll('.ar-tool-card')].filter(c=>['midjourney','comfyui','kling','blender'].includes(c.dataset.toolId)).map(c=>({id:c.dataset.toolId,instance:c.dataset.cardInstance,pose:c.dataset.pose,inert:c.inert,frontInert:c.querySelector('.ar-card-front').inert,style:c.getAttribute('style'),box:rect(c),front:rect(c.querySelector('.ar-card-front')),faces:[...c.querySelectorAll('[data-card-face]')].map(rect),slot:rect(rail.querySelector('[data-card-id="'+c.dataset.toolId+'"]')),inSlot:c.parentElement.classList.contains('ar-tool-slot')})),foreground:r.querySelector('.ar-card-foreground').children.length,duplicateIDs:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,a)=>a.indexOf(id)!==i)};}'''
INIT=r'''(() => {window.__entranceEvidence={phases:[],frames:[]};let root,last='';const box=e=>{if(!e)return null;const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]};const take=()=>{const b=root.dataset;return {time:performance.now(),phase:b.entrance,guide:document.querySelector('#tour-host')?.dataset.guidePhase,cards:[...root.querySelectorAll('.ar-tool-card')].filter(e=>['midjourney','comfyui','kling','blender'].includes(e.dataset.toolId)).map(e=>({id:e.dataset.toolId,pose:e.dataset.pose,inert:e.inert,frontInert:e.querySelector('.ar-card-front').inert,front:box(e.querySelector('.ar-card-front')),faces:[...e.querySelectorAll('[data-card-face]')].map(box),position:getComputedStyle(e.querySelector('.ar-card-position')).transform,orientation:getComputedStyle(e.querySelector('.ar-card-orientation')).transform,slot:box(root.querySelector('[data-card-id="'+e.dataset.toolId+'"]'))}))}};let running=false;function frame(){window.__entranceEvidence.frames.push(take());if(root.dataset.entrance==='playing')requestAnimationFrame(frame);else running=false;}const observer=new MutationObserver(()=>{root=document.querySelector('.ar-tools-browser');if(!root)return;const phase=root.dataset.entrance;if(phase!==last){last=phase;window.__entranceEvidence.phases.push(take());if(phase==='playing'&&!running){running=true;frame();}}});observer.observe(document,{subtree:true,attributes:true,attributeFilter:['data-entrance'],childList:true});})();'''
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'complete':False,'errors':[]}
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,**({'record_video_dir':str(run/'video'),'record_video_size':{'width':1440,'height':900}} if args.video else {}))
 context.add_init_script(INIT);p=context.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
 try:
  p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
  p.wait_for_timeout(350);report['before']=p.evaluate(SAMPLE)
  p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})')
  p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="playing"',timeout=20000)
  p.screenshot(path=str(run/'start.png'))
  for tag,progress in [('early',.25),('middle',.5),('late',.8)]:
   p.wait_for_function('t=>Number(document.querySelector(".ar-tools-browser").dataset.entranceProgress)>=t',arg=progress,timeout=10000)
   p.screenshot(path=str(run/(tag+'.png')))
  p.wait_for_function('["ready","cancelled"].includes(document.querySelector(".ar-tools-browser").dataset.entrance)',timeout=10000)
  p.wait_for_timeout(150);report['after']=p.evaluate(SAMPLE);report['motion']=p.evaluate('window.__entranceEvidence');p.screenshot(path=str(run/'settled.png'))
  report['complete']=True
 except Exception as e:
  report['failure']=str(e);report['traceback']=traceback.format_exc()
  try:report['after']=p.evaluate(SAMPLE);report['motion']=p.evaluate('window.__entranceEvidence');p.screenshot(path=str(run/'failure.png'))
  except Exception:pass
 finally:
  context.close();browser.close();report['browserClosed']=True
  (run/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'complete':report['complete'],'failure':report.get('failure'),'state':report.get('after',{}).get('browser'),'frames':len(report.get('motion',{}).get('frames',[]))},ensure_ascii=False))
