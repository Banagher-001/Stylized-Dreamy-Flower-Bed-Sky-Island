from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail');return{d:{...root.dataset},world:{...document.querySelector('#tour-host').dataset},mode:document.querySelector('main').dataset.readingMode,body:getComputedStyle(root).opacity,rail:rail.getBoundingClientRect().toJSON(),cards:[...rail.querySelectorAll('.ar-tool-card')].map(c=>({id:c.dataset.toolId,instance:c.dataset.cardInstance,width:c.offsetWidth,flight:c.dataset.flightPose,reading:c.dataset.readingPose,inert:c.inert,detail:c.querySelector('.ar-card-detail').hidden,front:c.querySelector('.ar-card-front').getBoundingClientRect().toJSON(),faces:[...c.querySelectorAll('[data-card-face]')].map(f=>f.getBoundingClientRect().toJSON())}))}}'''
data={};errors=[]
with sync_playwright() as play:
 b=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 for pinned in [False,True]:
  name='pinned' if pinned else 'ordinary';ctx=b.new_context(viewport={'width':1440,'height':900},record_video_dir=str(OUT/'inspection-video'));p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
  def go(h):
   p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
   p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=20000)
  try:
   p.goto(s['origin']+'/?waterTime=2');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);go(3.34)
   p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"',timeout=15000);p.wait_for_timeout(1000)
   if pinned:
    front=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(front['x']+front['width']*.5,front['y']+front['height']*.45)
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');button=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(button['x']+button['width']/2,button['y']+button['height']/2);p.wait_for_timeout(450)
   result={'before':p.evaluate(READ)}
   p.evaluate('''()=>{window.__frames=[];window.__record=true;const step=t=>{if(!__record)return;const r=document.querySelector('.ar-tools-browser');__frames.push({t,d:{...r.dataset},body:getComputedStyle(r).opacity,ink:getComputedStyle(r).getPropertyValue('--ar-body-opacity'),poses:[...r.querySelectorAll('.ar-tool-card')].filter(c=>c.dataset.flightPose&&c.dataset.flightPose!=='0.0000,0.0000,0.0000,0.0000,0.0000,0.0000').map(c=>({id:c.dataset.toolId,flight:c.dataset.flightPose}))});requestAnimationFrame(step)};requestAnimationFrame(step)}''')
   go(3.56);p.wait_for_timeout(150);result['during']=p.evaluate(READ);p.screenshot(path=str(OUT/f'inspection-{name}-during.png'))
   p.wait_for_timeout(650);result['departed']=p.evaluate(READ)
   go(3.34);p.wait_for_timeout(450);result['returned']=p.evaluate(READ);p.screenshot(path=str(OUT/f'inspection-{name}-returned.png'))
   result['frames']=p.evaluate('()=>{__record=false;return __frames}')
   data[name]=result
  except Exception as e:
   data[name]={'error':str(e),'state':p.evaluate(READ)};p.screenshot(path=str(OUT/f'inspection-{name}-failure.png'))
  finally:
   ctx.close();data[name]['video']=str(Path(p.video.path()).relative_to(OUT))
 b.close()
data['errors']=errors;(OUT/'inspection-1.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{n:v[n]['d'].get('departure') for n in ['before','during','departed','returned'] if n in v} if 'error' not in v else {'error':v['error']} for k,v in data.items() if isinstance(v,dict)},ensure_ascii=False))
