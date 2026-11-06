"""Fully warm both output modes across all chapters, with/without ornament."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-6';results={}
NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for disabled in [True,False]:
  context=b.new_context(viewport={'width':1440,'height':900})
  if disabled:context.add_init_script(NO_2D)
  page=context.new_page();page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');rows=[]
  for mode in ['pixel','native','pixel']:
   page.get_by_role('button',name='像素预览'if mode=='pixel'else'正常画面',exact=True).click()
   for h in [0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,11.5,7.64]:
    page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
   page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');rows.append(json.loads(page.locator('#tour-host').get_attribute('data-renderer-stats')))
  results['decorationUnavailable'if disabled else'normal']=rows;context.close()
 assert results['normal'][0]['geometries']==56 and results['normal'][0]['textures']==5 and results['normal'][0]['programs']<=11 and results['normal'][1]['programs']<=20
 (OUT/'resource-caches.json').write_text(json.dumps({'method':'same pixel/native/pixel history, visiting both pillars, third-pillar first view, water and overview within each mode','frames':results,'passed':True},ensure_ascii=False,indent=2)+'\n');b.close();print({k:[(v['geometries'],v['textures'],v['programs'])for v in rows]for k,rows in results.items()},flush=True)
