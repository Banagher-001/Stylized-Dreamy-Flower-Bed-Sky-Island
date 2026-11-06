"""Current second-pillar production integration; all observers stay in the test."""
from pathlib import Path
from io import BytesIO
import argparse,ast,json,math,os
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-6'
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text());PROBE=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PROBE'for t in n.targets))
source=(ROOT/'tests/scroll-garden/step5_browser.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='contrast');contrast_source=ast.get_source_segment(source,node).replace('.pillar-reading','.film-reading').replace('data-reading-ink','data-film-ink')
contrast_source=contrast_source.replace("background=Image.open(BytesIO(raw)).convert('RGB')","background=Image.open(BytesIO(raw)).convert('RGB');background=background.resize((page.viewport_size['width'],page.viewport_size['height']),Image.Resampling.NEAREST)")
exec(compile(contrast_source,'<measured contrast>','exec'))
STOPS=[('B1',4.95,2.8,'异星来信'),('B2',5.95,2.15,'画面切片'),('B3',6.84,1.5,'视觉探索'),('B4',7.64,.85,'影像，仍在继续。')]
checks=[];issues=[];requests=[]
def record(name,evidence):checks.append({'check':name,'passed':True,'evidence':evidence});print(args.engine+': '+name,flush=True)
def watch(page):
 page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}));page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None);page.on('response',lambda r:issues.append({'type':'http','text':str(r.status)+' '+r.url})if r.status>=400 else None)
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def settled(page,h):page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def go(page,h):page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);settled(page,h)
def ready_images(page):page.wait_for_function('()=>[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.complete&&i.naturalWidth>0)')
def frames(page):page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
def image(page):
 page.mouse.move(10,page.viewport_size['height']/2);frames(page)
 return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')
def layout(page):return page.locator('.film-reading').evaluate('e=>{const r=e.getBoundingClientRect(),a=e.querySelector("article:not([hidden])");return {data:{...e.dataset},rect:r.toJSON(),nav:document.querySelector(".tour-stops").getBoundingClientRect().toJSON(),stage:document.querySelector("#tour-host").getBoundingClientRect().toJSON(),header:document.querySelector(".tour-header").getBoundingClientRect().toJSON(),text:e.innerText,articles:[...e.querySelectorAll("article[aria-hidden=false]")].map(a=>a.dataset.filmStation),horizontalOverflow:document.documentElement.scrollWidth>innerWidth,internalScroll:e.scrollHeight>e.clientHeight+1,buttons:a?[...a.querySelectorAll("button")].map(b=>({disabled:b.disabled,rect:b.getBoundingClientRect().toJSON()})):[],textBoxes:a?[...a.querySelectorAll("h2,[data-film-ink]")].map(n=>{const b=n.getBoundingClientRect();return {text:n.textContent,font:parseFloat(getComputedStyle(n).fontSize),inside:b.left>=r.left+10&&b.right<=r.right-10&&b.top>=r.top+10&&b.bottom<=r.bottom-10}}):[]}}')
def state(page):
 d=data(page);r=layout(page)
 return {k:d[k]for k in ['cameraPosition','cameraTarget','viewHeight','filmStation','filmPhase','filmPresentation','filmMagicFrame','sceneTime']}|{'layout':{k:round(r['rect'][k],3)for k in ['x','y','width','height']}}
def resize(page,w,h):
 prior=float(data(page)['displayH']);page.set_viewport_size({'width':w,'height':h});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');frames(page);settled(page,prior)
def validate_layout(page):
 r=layout(page);assert r['data']['fits']=='true'and r['data']['anchorClear']=='true'and not r['horizontalOverflow']and not r['internalScroll'],r
 assert all(t['inside']and t['font']>=16 for t in r['textBoxes']),r
 assert all(b['rect']['width']>=44 and b['rect']['height']>=44 and not b['disabled']for b in r['buttons']),r
 return r

with sync_playwright() as p:
 options={'headless':args.engine=='chromium'}
 if args.engine=='chromium':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 if args.engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if args.engine=='webkit'and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
 b=getattr(p,args.engine).launch(**options);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();watch(page);page.on('request',lambda r:requests.append(r.url))
 page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');assert 'STEP 06'in page.title()
 assert page.locator('canvas').count()==1 and page.locator('.film-reading article').count()==4 and not page.locator('video').count()
 assert data(page)['filmMagicStatus']=='ready'and json.loads(data(page)['filmAvailability'])['realFilm']=='not-supplied'
 cold=list(requests);assert not any(x.endswith('.webp')or x.endswith('.mp4')for x in cold),cold
 go(page,3.8);ready_images(page);assert any('signal-garden'in x and x.endswith('.webp')for x in requests)and not any('liquid-form'in x for x in requests)
 record('cold scene defers exhibition images until approach and never requests a fake film',{'coldRequests':cold,'approachRequests':[x for x in requests if x.endswith('.webp')],'realFilm':'not-supplied'})
 views=[];ratios=[]
 for key,h,y,title in STOPS:
  go(page,h);ready_images(page);frames(page);r=validate_layout(page);d=data(page)
  assert d['filmStation']==key and abs(json.loads(d['cameraTarget'])[1]-y)<1e-7 and r['articles']==[key]
  assert page.get_by_role('heading',name=title,exact=True).count()==1
  assert page.locator('[data-stop=films]').get_attribute('aria-current')=='location'
  assert page.locator('.pillar-reading').get_attribute('aria-hidden')=='true'
  assert page.locator('.film-reading article[aria-hidden=true]').evaluate_all('es=>es.every(e=>e.hidden&&e.inert)')
  if key!='B4':assert '网页设计样片 / 非个人实际项目'in r['text']
  else:assert not r['buttons']and '继续向下，进入交互实验。'in r['text']
  assert not page.locator('[data-play-film]').count()
  page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.engine}-{key}.png'));views.append({'station':key,'layout':r,'scene':d});ratios.append(contrast(page,key))
 record('four distinct full-reading stations preserve true sample labels, proportions and real actions',views)
 record('all station titles, captions and provenance pass actual-background contrast',ratios)
 plateaus=[]
 for start,duration in [(4.4,1),(5.4,1),(6.4,.8),(7.2,.8)]:
  go(page,start+duration*.38);a=state(page);pic=image(page);go(page,start+duration*.72);assert state(page)==a and ImageChops.difference(pic,image(page)).getbbox()is None;plateaus.append({'startH':start,'pixelsExact':True})
 record('all four held reading windows keep exact camera, layout and composed pixels',plateaus)
 phases=[]
 for start,duration in [(4.4,1),(5.4,1),(6.4,.8),(7.2,.8)]:
  for u in [.1,.18,.25,.55,.9,.97]:
   go(page,start+duration*u);d=data(page);s=json.loads(d['filmPresentation']);glyph=json.loads(d['filmMagicFrame'])['glyph']
   if u==.1:assert s['frame']==s['media']==s['title']==s['body']==0 and glyph>0
   if u==.18:assert s['frame']>0 and s['media']<.01 and s['title']==s['body']==0
   if u==.25:assert s['media']>s['title']>s['body']>0
   if u==.55:assert all(s[k]==1 for k in ['frame','media','title','body'])
   if u==.9:assert s['title']>s['body']and s['body']<.5
   if u==.97:assert s['body']==s['media']==0 and s['title']>0
   if u in [.18,.97]:assert page.locator('.film-reading article:not([hidden]) button:enabled').count()==0
   phases.append({'station':d['filmStation'],'requestedU':u,'actualH':float(d['displayH']),'actualU':(float(d['displayH'])-start)/duration,'state':s,'glyph':glyph})
 go(page,5.34);a=state(page);pic=image(page);page.wait_for_timeout(500);assert state(page)==a and ImageChops.difference(pic,image(page)).getbbox()is None
 record('twenty-four ordered reveal states and a paused mid-descent remain scroll-controlled',phases)
 positions=[4.57,4.95,5.30,5.4,5.6,5.95,6.3,6.4,6.58,6.84,7.12,7.2,7.4,7.64,7.96,8,8.3];saved={}
 for h in positions:
  go(page,h);frames(page);saved[h]=state(page)
  if h in [5.3,5.4,6.3,6.4,7.12,8,8.3]:page.screenshot(path=str(OUT/f'{args.engine}-travel-{h}.png'))
 go(page,9.14)
 for h in reversed(positions):go(page,h);frames(page);assert state(page)==saved[h],(h,state(page),saved[h])
 record('reverse and fast jumps restore exact camera, presentation and layout including pillar exit',{'positionsH':positions,'exact':True})
 go(page,4.95);page.locator('#tour-reference').focus();old=float(data(page)['displayH']);page.mouse.wheel(0,340);page.wait_for_function('h=>Number(document.querySelector("#tour-host").dataset.displayH)>h',arg=old);page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"');mapped=page.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3');assert abs(float(data(page)['displayH'])-mapped)<1e-6 and page.evaluate('document.activeElement.id')=='tour-reference'
 page.keyboard.press('Home');settled(page,0);page.keyboard.press('End');settled(page,12.3);page.locator('[data-stop=films]').click();settled(page,4.95);page.locator('.tour-inspector summary').click();page.locator('[data-reading-stop=B4]').click();settled(page,7.64);page.locator('.tour-inspector summary').click()
 record('wheel, keyboard, chapter and four debug stops use native progress without stealing focus',{'nativeMappedH':mapped,'HomeEnd':True,'debugB4':True})
 go(page,5.95);a=state(page);pic=image(page);page.get_by_role('button',name='正常画面',exact=True).click();assert state(page)==a and ImageChops.difference(pic,image(page)).getbbox()is not None;page.get_by_role('button',name='像素预览',exact=True).click();assert state(page)==a and ImageChops.difference(pic,image(page)).getbbox()is None
 record('render modes preserve media and camera and return exact pixels',{'exact':True})
 resized=[]
 for key,h,y,title in STOPS:
  go(page,h);resize(page,1366,768);r=validate_layout(page);page.mouse.move(10,400);page.screenshot(path=str(OUT/f'{args.engine}-1366-{key}.png'));resized.append({'station':key,'layout':r});resize(page,1440,900)
 go(page,6.30);resize(page,1366,768);assert data(page)['filmStation']=='B2';resize(page,1440,900)
 record('desktop resizing keeps all four stations complete and preserves descent position',resized)
 dialogs=[]
 for key,h in [('B1',4.95),('B2',5.95),('B3',6.84)]:
  go(page,h);frames(page);a=state(page);button=page.locator(f'[data-film-station={key}] button[data-work]').first;button.click();page.wait_for_selector('.film-dialog[open][data-state=ready]');assert data(page)['overlayState']=='open'and '非个人实际项目'in page.locator('.film-dialog-label').inner_text()
  covered=data(page)['sceneTime'];prior_y=page.evaluate('scrollY');page.mouse.wheel(0,550);page.wait_for_timeout(150);assert data(page)['sceneTime']==covered and page.evaluate('scrollY')==prior_y
  page.keyboard.press('Escape');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');frames(page);assert state(page)==a and button.evaluate('e=>document.activeElement===e')
  dialogs.append({'station':key,'progressTimeAndFocusRestored':True,'backgroundScrollBlocked':True})
 record('full-image dialogs retain provenance, freeze background and restore exact progress and focus',dialogs)
 go(page,6.84);page.locator('[data-film-station=B3] button').first.click();page.wait_for_selector('.film-dialog[open][data-state=ready]');resize(page,1366,768);page.get_by_role('button',name='关闭画面',exact=True).click();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');settled(page,6.84);validate_layout(page);resize(page,1440,900)
 record('dialog resizing restores the normalized station rather than old scroll pixels',{'station':'B3','h':6.84})
 go(page,5.95);a=state(page);pic=image(page);page.evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()');page.wait_for_selector('#tour-host[data-render-state="context-lost"]');assert page.locator('[data-stop]:disabled,[data-reading-stop]:disabled,.mode-controls button:disabled,#tour-motion:disabled').count()==15;page.evaluate('window.__loss.restoreContext()');page.wait_for_selector('#tour-host[data-render-state="ready"]');frames(page);restored=image(page);diff=ImageChops.difference(pic,restored).getbbox();pic.save(OUT/f'{args.engine}-context-before.png');restored.save(OUT/f'{args.engine}-context-after.png');assert state(page)==a and diff is None
 record('context recovery restores four-station presentation and actual pixels',{'pixelsExact':True,'disabledGraphControls':15})
 for h in [1.74,3.34,4.95,5.95,6.84,7.64]:go(page,h)
 page.wait_for_timeout(200);before=json.loads(data(page)['rendererStats']);nodes=page.locator('*').count();cycles=10 if args.engine=='chromium'else 2
 for _ in range(cycles):
  for h in [4.95,5.95,6.84,7.64]:go(page,h)
  go(page,6.84);page.locator('[data-film-station=B3] button').first.click();page.wait_for_selector('.film-dialog[open][data-state=ready]');page.keyboard.press('Escape');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
 go(page,7.64);page.wait_for_timeout(200);after=json.loads(data(page)['rendererStats']);assert all(before[k]==after[k]and after[k]<=limit for k,limit in [('geometries',56),('textures',5),('programs',11)])
 assert page.locator('*').count()==nodes and page.locator('video').count()==0 and page.locator('dialog').count()==1
 draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(600);assert page.evaluate('window.__tourProbe.draws')==draws
 record('repeated tours and image dialogs keep DOM and GPU counts stable and stop paused drawing',{'cycles':cycles,'before':before,'after':after,'documentNodes':nodes,'activeVideos':0,'pausedDraws':draws})
 page.get_by_role('button',name='播放动效',exact=True).click();go(page,4.95);page.wait_for_timeout(150);page.locator('[data-film-station=B1] button').click();page.wait_for_selector('.film-dialog[open][data-state=ready]');t=data(page)['sceneTime'];page.wait_for_timeout(250);assert data(page)['sceneTime']==t;page.keyboard.press('Escape');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)',arg=t);page.get_by_role('button',name='暂停动效',exact=True).click()
 record('closing a view restores the prior manual environment playback choice',{'resumesIfPreviouslyPlaying':True,'keepsPausedIfPreviouslyPaused':True})
 kwargs={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True,'reduced_motion':'reduce'}
 if args.engine!='firefox':kwargs['is_mobile']=True
 mobile=b.new_context(**kwargs);m=mobile.new_page();watch(m);m.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');m.wait_for_selector('#tour-host[data-render-state="ready"]');mobile_results=[]
 for key,h,y,title in STOPS:
  go(m,h);ready_images(m);frames(m);r=validate_layout(m);assert r['rect']['bottom']<=r['nav']['top']-15
  assert json.loads(data(m)['filmMagicFrame'])['dustVisible']==0 and json.loads(data(m)['filmMagicResources'])['pool']==12
  m.mouse.move(10,400);m.screenshot(path=str(OUT/f'{args.engine}-mobile-{key}.png'));mobile_results.append({'station':key,'layout':r,'contrast':contrast(m,'mobile-'+key)})
 go(m,4.95);m.locator('[data-film-station=B1] button').tap();m.wait_for_selector('.film-dialog[open][data-state=ready]');m.get_by_role('button',name='关闭画面',exact=True).tap();m.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');settled(m,4.95)
 if args.engine=='chromium':
  session=mobile.new_cdp_session(m);old=float(data(m)['displayH']);session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':350}]})
  for y in [310,270,230,190]:session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]});m.wait_for_timeout(35)
  session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(350);assert float(data(m)['displayH'])>old
 m.emulate_media(reduced_motion='no-preference');go(m,5.95);m.wait_for_function('JSON.parse(document.querySelector("#tour-host").dataset.filmMagicFrame).dustVisible===4');mobile.close()
 record('four portrait layouts, contrast, touch viewing and reduced-motion navigation pass',{'viewport':[390,844],'simulatedPhone':True,'nativeTouchDrag':args.engine=='chromium','stations':mobile_results})
 latency=page.evaluate('window.__tourProbe.settles');record('integration settle diagnostics retained separately from the matched benchmark',{'samples':len(latency),'p95Ms':sorted(latency)[int((len(latency)-1)*.95)],'maxMs':max(latency),'hardwareFPSProof':False})
 known=[x for x in issues if args.engine=='firefox'and any(s in x['text']for s in ['Depth texture comparison requests','WebGL context was lost.','This site appears to use a scroll-linked positioning effect.'])];unexpected=[x for x in issues if x not in known];assert not unexpected,unexpected
 record('all browser diagnostics retained with no unidentified errors or requests',{'knownFirefoxDiagnostics':len(known),'unexpected':unexpected})
 (OUT/f'verification-{args.engine}.json').write_text(json.dumps({'engine':args.engine,'version':b.version,'checks':checks,'issues':issues,'passed':True,'environment':'Linux software graphics; simulated phone; GTK WebKit is not Apple Safari; no hardware FPS acceptance'},ensure_ascii=False,indent=2)+'\n');b.close()
