from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent;s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
READ=r'''()=>{const r=document.querySelector('.ar-tools-browser'),panel=r.querySelector('.ar-tool-help-panel'),rail=r.querySelector('.ar-tool-rail'),button=r.querySelector('[data-action=help]');return{d:{...r.dataset},mode:document.querySelector('main').dataset.readingMode,h:document.querySelector('#tour-host').dataset.displayH,hint:r.querySelector('.ar-current-hint').textContent,help:{hidden:panel.hidden,presentation:panel.dataset.presentation,rect:panel.getBoundingClientRect().toJSON(),scrollHeight:panel.scrollHeight,clientHeight:panel.clientHeight,scrollTop:panel.scrollTop,text:panel.textContent,expanded:button.getAttribute('aria-expanded')},rail:rail.getBoundingClientRect().toJSON(),root:r.getBoundingClientRect().toJSON(),y:scrollY,focus:document.activeElement?.dataset.action,pinned:[...rail.querySelectorAll('.ar-tool-card')].filter(c=>c.dataset.detailState==='pinned').map(c=>({id:c.dataset.toolId,width:c.offsetWidth,hidden:c.querySelector('.ar-card-detail').hidden})),overflow:document.documentElement.scrollWidth-innerWidth}}'''
data={};errors=[]
with sync_playwright() as play:
 b=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 for touch in [False,True]:
  name='phone' if touch else 'desktop';ctx=b.new_context(viewport={'width':390,'height':844} if touch else {'width':1440,'height':900},has_touch=touch,is_mobile=touch);p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.set_default_timeout(12000)
  try:
   p.goto(s['origin']+'/?waterTime=2');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
   if touch:p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
   else:
    p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"');p.wait_for_timeout(1000)
   p.wait_for_timeout(300);result={'before':p.evaluate(READ)};p.screenshot(path=str(OUT/f'inspect-{name}-before.png'))
   if touch:p.locator('[data-action=help]').tap()
   else:p.locator('[data-action=help]').click()
   p.wait_for_timeout(700);result['open']=p.evaluate(READ);p.screenshot(path=str(OUT/f'inspect-{name}-open.png'))
   if not touch:
    rect=p.locator('.ar-tool-help-panel').bounding_box();p.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']*.7);p.mouse.wheel(0,220);p.wait_for_timeout(200);result['scrolled']=p.evaluate(READ);p.keyboard.press('Escape')
   else:p.locator('[data-action=help-close]').tap()
   p.wait_for_timeout(1200);result['closed']=p.evaluate(READ);data[name]=result
  except Exception as e:
   data[name]={'error':str(e)}
   try:data[name]['state']=p.evaluate(READ);p.screenshot(path=str(OUT/f'inspect-{name}-failure.png'))
   except Exception:pass
  finally:ctx.close()
 b.close()
data['errors']=errors;(OUT/'inspection-1.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{t:{'mode':m['mode'],'help':m['help']['hidden'],'hint':m['hint'],'choice':m['d']['trackEnabled'],'phase':m['d']['trackState']} for t,m in v.items() if isinstance(m,dict) and 'mode' in m} if 'error' not in v else v for k,v in data.items() if isinstance(v,dict)},ensure_ascii=False))
