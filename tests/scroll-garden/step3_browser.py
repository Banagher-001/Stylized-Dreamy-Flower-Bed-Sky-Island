"""Production integration checks for pillar reading; probes stay in this test."""
from pathlib import Path
from io import BytesIO
import argparse, ast, json, math, os
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/scroll-garden-step-3'
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
# Reuse the test-only GL/settle observer without executing the old test suite.
tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text())
PROBE=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PROBE'for t in n.targets))
checks=[];issues=[]
def record(name,evidence):
 checks.append({'check':name,'passed':True,'evidence':evidence});print(args.engine+': '+name,flush=True)
def watch(page):
 page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}))
 page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
 page.on('response',lambda r:issues.append({'type':'http','text':str(r.status)+' '+r.url})if r.status>=400 else None)
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def settled(page,h):page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def go(page,h):
 page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);settled(page,h)
def resize(page,w,h):
 old=float(data(page)['displayH']);page.set_viewport_size({'width':w,'height':h})
 page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}')
 page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');settled(page,old)
def image(page):
 page.mouse.move(10,page.viewport_size['height']/2)
 page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
 return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')
def state(page):
 d=data(page);return {k:d[k]for k in ['cameraPosition','cameraTarget','viewHeight','readingStation','readingOpacity','readingPhase']}
def panel(page):return page.locator('.pillar-reading').evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),visibleArticles:[...e.querySelectorAll("article")].filter(a=>a.getAttribute("aria-hidden")==="false").map(a=>a.dataset.readingStation),text:e.innerText})')
def layout(page):
 return page.locator('.pillar-reading').evaluate('e=>{const p=e.getBoundingClientRect(),n=document.querySelector(".tour-stops").getBoundingClientRect(),h=document.querySelector("#tour-host").getBoundingClientRect(),a=e.querySelector("article[aria-hidden=false]"),b=a.querySelector(".pillar-reading-body"),r=b.getBoundingClientRect();return {fits:e.dataset.fits,anchorClear:e.dataset.anchorClear,fontSize:parseFloat(getComputedStyle(b).fontSize),panel:p.toJSON(),body:r.toJSON(),nav:n.toJSON(),stage:h.toJSON(),noHorizontalOverflow:document.documentElement.scrollWidth<=innerWidth,noInternalScroll:e.scrollHeight<=e.clientHeight+1&&a.scrollHeight<=a.clientHeight+1}}')
def capacity(page,label):
 body=page.locator('[data-reading-station=A2] .pillar-reading-body');original=body.text_content()
 text=('长度测试，不作为个人介绍。'+'这段文字只用于检查阅读区域的排版容量、自然换行、段落高度与柱身位置关系。'*8)[:200]
 body.evaluate('(e,t)=>e.textContent=t',text)
 page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
 result=layout(page);result.update(sampleCharacters=len(text),clearlyLabelled=True)
 page.screenshot(path=str(OUT/f'capacity-{label}.png'))
 body.evaluate('(e,t)=>e.textContent=t',original)
 page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
 return result

with sync_playwright() as p:
 options={'headless':args.engine=='chromium'}
 if args.engine=='chromium':options.update(executable_path=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 if args.engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if args.engine=='webkit'and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
 b=getattr(p,args.engine).launch(**options);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();watch(page)
 page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 assert 'STEP 03'in page.title()and page.locator('canvas').count()==1 and page.locator('.pillar-reading article').count()==3
 record('one production scene and three semantic reading stations',{'canvasCount':1,'articles':3})
 keyviews=[]
 for key,h,title,y in [('A1',1.74,'我是 sakan',2.75),('A2',2.54,'现在与此前',1.8),('A3',3.34,'我的创作方式',.85)]:
  go(page,h);d=data(page);r=panel(page);assert d['readingStation']==key and d['readingOpacity']=='1.0000000'and d['sceneTime']=='2.000000'
  assert abs(json.loads(d['cameraTarget'])[1]-y)<1e-7 and r['visibleArticles']==[key]
  assert page.get_by_role('heading',name=title,exact=True).count()==1
  other=page.locator(f'.pillar-reading article:not([data-reading-station={key}])');assert other.evaluate_all('es=>es.every(e=>e.inert&&e.getAttribute("aria-hidden")==="true"&&getComputedStyle(e).visibility==="hidden")')
  assert layout(page)['fits']=='true';page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.engine}-{key}.png'));keyviews.append({'key':key,'scene':d,'reader':r})
 record('all three heights show the correct complete accessible paragraph',keyviews)

 plateaus=[]
 for start in [1.3,2.1,2.9]:
  go(page,start+.8*.38);a=state(page);picture=image(page)
  go(page,start+.8*.72);assert state(page)==a and ImageChops.difference(picture,image(page)).getbbox()is None
  plateaus.append({'startH':start,'samplesH':[start+.8*.38,start+.8*.72],'pixelsExact':True})
 record('reading plateaus retain identical camera, text and visible scene',plateaus)

 phases=[]
 for start in [1.3,2.1,2.9]:
  for u,expected in [(.1,'approach'),(.225,'reveal'),(.55,'read'),(.9,'leave')]:
   go(page,start+.8*u);d=data(page);assert d['readingPhase']==expected
   opacity=float(d['readingOpacity']);assert (opacity==0 if expected=='approach'else opacity==1 if expected=='read'else .45<opacity<.55)
   assert len(panel(page)['visibleArticles'])==(0 if expected=='approach'else 1)
   phases.append({'h':float(d['displayH']),'phase':expected,'opacity':opacity})
 go(page,2.02);frozen=state(page);picture=image(page);page.wait_for_timeout(550)
 assert state(page)==frozen and ImageChops.difference(picture,image(page)).getbbox()is None
 record('twelve reveal/read/leave states and a mid-fade pause follow scroll, not time',phases)

 poses={}
 for h in [1.48,2.02,2.1,2.28,2.54,2.82,2.9,3.08,3.34,3.7,3.92]:
  go(page,h);poses[h]=state(page)
  if h in [2.02,2.1,2.82,2.9,3.7,3.92]:page.screenshot(path=str(OUT/f'{args.engine}-travel-{str(h).replace(".","-")}.png'))
 go(page,4.95)
 for h in reversed(list(poses)):
  go(page,h);assert state(page)==poses[h]
 record('reverse and fast jumps restore identical camera and reading states, including pillar exit',{'positionsH':list(poses),'exact':True})

 go(page,1.74);page.locator('#tour-reference').focus();old=float(data(page)['displayH']);page.mouse.wheel(0,350)
 page.wait_for_function('h=>Number(document.querySelector("#tour-host").dataset.displayH)>h',arg=old)
 page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"')
 actual=float(data(page)['displayH']);mapped=page.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3');assert abs(actual-mapped)<1e-6
 assert page.evaluate('document.activeElement.id')=='tour-reference'
 page.mouse.wheel(0,-350);page.wait_for_function('h=>Number(document.querySelector("#tour-host").dataset.displayH)<h',arg=actual)
 page.keyboard.press('Home');settled(page,0);page.keyboard.press('End');settled(page,12.3)
 page.locator('[data-stop=about]').click();settled(page,1.74)
 page.locator('.tour-inspector summary').click();page.locator('[data-reading-stop=A2]').click();settled(page,2.54);page.locator('.tour-inspector summary').click()
 record('real wheel, keyboard and debug navigation share native progress without stealing focus',{'wheelMappedH':actual,'nativeH':mapped,'HomeEnd':True,'debugStop':'A2'})

 go(page,2.54);before=state(page);pixel=image(page)
 page.get_by_role('button',name='正常画面',exact=True).click();assert state(page)==before and ImageChops.difference(pixel,image(page)).getbbox()is not None
 page.get_by_role('button',name='像素预览',exact=True).click();assert state(page)==before and ImageChops.difference(pixel,image(page)).getbbox()is None
 record('render mode changes the scene and preserves reading; pixel return is exact',{'pixelsExact':True})

 resized=[]
 for h in [2.54,2.08]:
  go(page,h);before=state(page);resize(page,1366,768)
  assert data(page)['readingStation']==before['readingStation'] and abs(float(data(page)['viewHeight'])-3.6)<1e-6
  if h==2.54:
   r=layout(page);assert r['fits']=='true'and r['noHorizontalOverflow']and r['noInternalScroll'];page.screenshot(path=str(OUT/f'{args.engine}-1366-A2.png'))
  resized.append({'h':h,'after':data(page)});resize(page,1440,900)
 record('resize preserves full-read and descending positions with legible layout',resized)

 go(page,2.54);picture=image(page);before=state(page)
 page.evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()')
 page.wait_for_selector('#tour-host[data-render-state="context-lost"]');assert page.locator('button:disabled').count()==11
 page.evaluate('window.__loss.restoreContext()');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 assert state(page)==before and ImageChops.difference(picture,image(page)).getbbox()is None
 record('context restore preserves the reading camera, paragraph and actual image',{'pixelsExact':True,'disabledSceneControls':11})

 for h in [1.74,2.54,3.34,4.95]:go(page,h)
 page.wait_for_timeout(250);before=json.loads(data(page)['rendererStats']);nodes=page.locator('.pillar-reading article').count();cycles=10 if args.engine=='chromium'else 2
 for _ in range(cycles):
  for h in [1.74,2.54,3.34,4.95]:go(page,h)
 page.wait_for_timeout(250);after=json.loads(data(page)['rendererStats'])
 for key in ['geometries','textures','programs']:assert before[key]==after[key]
 assert before['pixel']['allocations']==after['pixel']['allocations']and page.locator('.pillar-reading article').count()==nodes
 draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(650);assert page.evaluate('window.__tourProbe.draws')==draws
 record('repeated reading tours retain GPU/DOM counts; settled pause stops drawing',{'cycles':cycles,'before':before,'after':after,'articles':nodes,'pausedDrawCount':draws})
 page.get_by_role('button',name='播放动效',exact=True).click();page.wait_for_timeout(180);a=float(data(page)['sceneTime']);go(page,2.54);page.wait_for_timeout(180);assert float(data(page)['sceneTime'])>a
 page.get_by_role('button',name='暂停动效',exact=True).click();go(page,3.34);assert data(page)['readingStation']=='A3'
 record('environment time advances independently and manual pause retains scroll reading',{'independent':True})

 kept=[];baseline=json.loads((OUT/'route-before.json').read_text())
 for key,h in [('B1',4.95),('C1',9.14),('water',11.5),('overview',0)]:
  go(page,h);d=data(page);prior=baseline['poses'][{'B1':'B','C1':'C','water':'W','overview':'O'}[key]]
  # Browser font metrics can change footer height, so compare at this engine's actual stage aspect.
  aspect=float(d['aspect']);height=prior['viewHeight']*max(1,1/aspect);dx=prior['position'][0]-prior['target'][0];dz=prior['position'][2]-prior['target'][2];pan=(.5-prior['screenX'])*height*aspect;shift=[dz/math.hypot(dx,dz)*pan,0,-dx/math.hypot(dx,dz)*pan]
  for field,base in [('cameraPosition','position'),('cameraTarget','target')]:assert max(abs(a-(v+s))for a,v,s in zip(json.loads(d[field]),prior[base],shift))<2e-6
  assert abs(float(d['viewHeight'])-height)<1e-6 and panel(page)['visibleArticles']==[]
  kept.append({'key':key,'approvedBasePoseRetained':True,'actualAspect':aspect});page.screenshot(path=str(OUT/f'{args.engine}-{key}.png'))
 record('other pillar first views, water and overview retain their approved camera poses',kept)

 # Capacity test is an explicit diagnostic; a long paragraph need not fit this three-station study.
 capacities={}
 if args.engine=='chromium':go(page,2.54);capacities['desktop']=capacity(page,'1440')
 kwargs={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True,'reduced_motion':'reduce'}
 if args.engine!='firefox':kwargs['is_mobile']=True
 mobile=b.new_context(**kwargs);m=mobile.new_page();watch(m);m.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');m.wait_for_selector('#tour-host[data-render-state="ready"]')
 m.locator('[data-stop=about]').tap();settled(m,1.74);mobile_results=[]
 for key,h in [('A1',1.74),('A2',2.54),('A3',3.34)]:
  go(m,h);r=layout(m);assert r['fits']=='true'and r['fontSize']>=16 and r['noHorizontalOverflow']and r['noInternalScroll']
  assert r['panel']['bottom']<r['nav']['top']and r['panel']['bottom']<r['stage']['bottom']
  assert r['body']['bottom']<=r['panel']['bottom']-12
  m.screenshot(path=str(OUT/f'{args.engine}-mobile-{key}.png'));mobile_results.append({'station':key,'layout':r})
 assert m.locator('[data-stop],.mode-controls button,#tour-motion').evaluate_all('es=>es.every(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44})')
 if args.engine=='chromium':
  go(m,2.54);capacities['mobile']=capacity(m,'390');session=mobile.new_cdp_session(m);old=float(data(m)['displayH'])
  session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':420}]})
  for y in [380,340,300,260]:session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]});m.wait_for_timeout(35)
  session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(400);assert float(data(m)['displayH'])>old
 mobile.close();record('three mobile reading stations fit, remain clear and support reduced-motion navigation',{'viewport':[390,844],'simulatedPhone':True,'nativeTouchDrag':args.engine=='chromium','stations':mobile_results})
 if capacities:record('labelled long-text capacity measured without publishing invented biography',capacities)

 latency=page.evaluate('window.__tourProbe.settles');assert latency
 record('browser-observed settle latency retained, without hardware FPS claims',{'samples':len(latency),'p95Ms':sorted(latency)[int((len(latency)-1)*.95)],'maxMs':max(latency),'targetMs':200})
 if args.engine=='chromium':
  page.set_viewport_size({'width':1440,'height':1000})
  for mode in ['pixel','native']:
   page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');actual=image(page);prior=Image.open(OUT/f'before-reference-{mode}.png').convert('RGB');assert ImageChops.difference(prior,actual).getbbox()is None;page.locator('canvas').screenshot(path=str(OUT/f'after-reference-{mode}.png'))
  assert page.locator('.work-card').count()==3 and '枫叶互动'in page.locator('#about').inner_text()
  record('default portfolio and both scene render modes remain pixel-identical',{'modes':['pixel','native'],'exact':True})
 known=[x for x in issues if args.engine=='firefox'and('Depth texture comparison requests'in x['text']or'WebGL context was lost.'in x['text'])];unexpected=[x for x in issues if x not in known];assert not unexpected,unexpected
 record('diagnostics retained, with no unidentified errors or warnings',{'knownFirefoxDiagnostics':len(known),'unexpected':unexpected})
 (OUT/f'verification-{args.engine}.json').write_text(json.dumps({'engine':args.engine,'version':b.version,'checks':checks,'issues':issues,'passed':True,'environment':'Linux software rendering; simulated phone; not Apple Safari or hardware FPS acceptance'},ensure_ascii=False,indent=2)+'\n');b.close()
