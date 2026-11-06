from playwright.sync_api import sync_playwright
from step10_common import *
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});issues=[];page.on('pageerror',lambda e:issues.append(str(e)));ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2');views=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  resize(page,w,h)
  for mode in ['pixel','native']:
   page.locator(f'.tour-actions [data-mode={mode}]').click()
   for key,at in [('O',0),('A1',1.74),('B2',5.95),('C2',10.05),('W',11.5),('S99',12.3)]:
    go(page,at);frames(page);page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'initial-{w}-{mode}-{key}.png'))
    layout=page.evaluate("""()=>({heading:document.querySelector('.tour-heading').getBoundingClientRect().toJSON(),nav:document.querySelector('.tour-stops').getBoundingClientRect().toJSON(),footer:document.querySelector('.tour-footer').getBoundingClientRect().toJSON(),overflow:document.documentElement.scrollWidth>innerWidth,reader:[...document.querySelectorAll('.pillar-reading,.film-reading,.experiment-reading')].map(e=>({type:e.className,visible:e.dataset.visible,fits:e.dataset.fits,anchorClear:e.dataset.anchorClear})),navControls:[...document.querySelectorAll('.tour-stops button')].map(b=>({box:b.getBoundingClientRect().toJSON(),font:getComputedStyle(b).fontSize}))})""")
    views.append({'viewport':[w,h],'mode':mode,'pose':key,'data':data(page),'layout':layout})
 save('initial-layout.json',{'views':views,'issues':issues});print('Initial views:',len(views),'exceptions',issues,'bad layouts',[(v['viewport'],v['pose'],v['layout']['reader'])for v in views if v['layout']['overflow']or any(r['visible']=='true'and r['fits']!='true'for r in v['layout']['reader'])],flush=True);b.close()
