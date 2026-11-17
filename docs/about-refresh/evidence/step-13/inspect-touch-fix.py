from pathlib import Path
import json,os,traceback
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent;ROOT=OUT.parents[3]
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),box=e=>e?.getBoundingClientRect().toJSON();return {viewport:[innerWidth,innerHeight],mode:document.querySelector('main').dataset.readingMode,reason:document.querySelector('main').dataset.layoutReason,host:{...document.querySelector('#tour-host').dataset},d:{...root.dataset},y:scrollY,overflow:document.documentElement.scrollWidth-innerWidth,header:box(document.querySelector('.tour-header')),root:box(root),rail:box(rail),railX:rail.scrollLeft,help:box(root.querySelector('.ar-tool-help-panel')),focus:document.activeElement?.outerHTML.slice(0,300),cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,detail:e.dataset.detailState,wide:e.dataset.detailWide,rect:box(e),front:box(e.querySelector('.ar-card-front')),bodyHidden:e.querySelector('.ar-card-detail').hidden,button:box(e.querySelector('button')),text:e.querySelector('.ar-card-front').innerText})),controls:box(root.querySelector('.ar-tool-controls'))}}'''
result={'matrix':[],'states':{},'errors':[]}
with sync_playwright() as play:
 b=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 def ready(p):
  p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
 def go(p):
  if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
  else:
   p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-3.34)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',timeout=25000)
  p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=12000);p.wait_for_timeout(450)
 def page(size=(1440,900),touch=False):
  c=b.new_context(viewport={'width':size[0],'height':size[1]},has_touch=touch,is_mobile=touch);p=c.new_page();p.set_default_timeout(12000);p.on('pageerror',lambda e:result['errors'].append(str(e)));ready(p);go(p);return c,p
 try:
  for size in []:
   c,p=page(size,size[0]<500);m=p.evaluate(READ);result['matrix'].append(m);p.screenshot(path=str(OUT/f'baseline-{size[0]}x{size[1]}.png'));c.close()
  c,p=page();p.locator('[data-action=auto]').click();button=p.locator('.ar-tool-card[data-tool-id=comfyui] button');button.click();p.wait_for_timeout(450);result['states']['pinBefore']=p.evaluate(READ)
  for label,mutation in [('phone',lambda:p.set_viewport_size({'width':390,'height':844})),('desktop',lambda:p.set_viewport_size({'width':1440,'height':900})),('large',lambda:p.evaluate('document.documentElement.style.fontSize="200%"')),('normal',lambda:p.evaluate('document.documentElement.style.fontSize=""'))]:
   mutation();p.wait_for_timeout(1000);result['states'][label]=p.evaluate(READ);p.screenshot(path=str(OUT/f'touch-fix-pin-{label}.png'))
  c.close()
  c,p=page();p.locator('[data-action=auto]').click();front=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front');r=front.bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');result['states']['hybridBefore']=p.evaluate(READ)
  r=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();cdp=c.new_cdp_session(p);x=r['x']+r['width']/2;y=r['y']+r['height']/2
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});p.wait_for_timeout(60);result['states']['hybridDown']=p.evaluate(READ);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(650);result['states']['hybridAfter']=p.evaluate(READ);p.screenshot(path=str(OUT/'touch-fix-hybrid-tap.png'));c.close()
 except Exception as e:result['failure']={'error':str(e),'traceback':traceback.format_exc()}
 finally:b.close();result['browserClosed']=True
(OUT/'inspection-touch-fix.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'matrix':[{k:v[k] for k in ['viewport','mode','overflow']} for v in result['matrix']],'states':{k:{'mode':v['mode'],'reading':v['d'].get('readingId'),'track':v['d'].get('trackMode'),'input':v['d'].get('toolInput'),'focus':v['focus']} for k,v in result['states'].items()},'failure':result.get('failure'),'errors':result['errors']},ensure_ascii=False))
