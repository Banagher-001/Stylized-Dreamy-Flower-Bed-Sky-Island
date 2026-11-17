from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,os,json,hashlib,traceback,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--video',action='store_true');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
SAMPLE=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail');const rect=e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom,r.width,r.height]};return {now:performance.now(),root:{...root.dataset},main:{...document.querySelector('main').dataset},host:{...document.querySelector('#tour-host').dataset},rail:{box:rect(rail),scrollLeft:rail.scrollLeft},cards:[...root.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,inert:e.inert,pose:e.dataset.pose,box:rect(e),front:rect(e.querySelector('.ar-card-front')),faces:[...e.querySelectorAll('[data-card-face]')].map(rect),position:getComputedStyle(e.querySelector('.ar-card-position')).transform,slot:e.parentElement.classList.contains('ar-tool-slot')?rect(e.parentElement):null})),button:{hidden:root.querySelector('[data-action=auto]').hidden,label:root.querySelector('[data-action=auto]').textContent,pressed:root.querySelector('[data-action=auto]').getAttribute('aria-pressed')},focus:{action:document.activeElement?.dataset.action,tool:document.activeElement?.closest('.ar-tool-card')?.dataset.toolId},overflow:document.documentElement.scrollWidth-innerWidth,duplicates:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,a)=>a.indexOf(id)!==i)};}'''
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
(run/'source-manifest.json').write_text(json.dumps([{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],indent=2)+'\n');shutil.copy2(__file__,run/'inspect-track.py.txt')
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'complete':False,'errors':[],'samples':[]}
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 context=browser.new_context(viewport={'width':1440,'height':900},**({'record_video_dir':str(run/'video'),'record_video_size':{'width':1440,'height':900}} if args.video else {}));p=context.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
 try:
  p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
  report['samples'].append(p.evaluate(SAMPLE));p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})')
  p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=20000)
  report['samples'].append(p.evaluate(SAMPLE));p.wait_for_timeout(1500);report['samples'].append(p.evaluate(SAMPLE));p.screenshot(path=str(run/'running.png'))
  p.wait_for_timeout(2100);report['samples'].append(p.evaluate(SAMPLE));p.locator('[data-action=auto]').click();p.wait_for_timeout(100);report['samples'].append(p.evaluate(SAMPLE));p.screenshot(path=str(run/'paused.png'))
  p.wait_for_timeout(400);report['samples'].append(p.evaluate(SAMPLE));p.locator('[data-action=auto]').focus();p.keyboard.press('Enter');p.wait_for_timeout(1200);report['samples'].append(p.evaluate(SAMPLE));p.screenshot(path=str(run/'resumed.png'));report['complete']=True
 except Exception as e:
  report['failure']=str(e);report['traceback']=traceback.format_exc()
  try:report['samples'].append(p.evaluate(SAMPLE));p.screenshot(path=str(run/'failure.png'))
  except Exception:pass
 finally:context.close();browser.close();report['browserClosed']=True;(run/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'complete':report['complete'],'errors':report['errors'],'failure':report.get('failure'),'states':[{k:d['root'].get(k) for k in ['entrance','trackState','trackMode','trackOffset','trackReason','trackEnabled']} for d in report['samples']]},ensure_ascii=False))
