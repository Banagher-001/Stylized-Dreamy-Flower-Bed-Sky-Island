"""Production integration checks for the formal first-pillar biography; probes stay in this test."""
from pathlib import Path
from io import BytesIO
import argparse, ast, json, math, os
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/scroll-garden-step-5'
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
 d=data(page);return {k:d[k]for k in ['cameraPosition','cameraTarget','viewHeight','readingStation','readingOpacity','readingTitleOpacity','readingPhase','magicFrame']}
def panel(page):return page.locator('.pillar-reading').evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),visibleArticles:[...e.querySelectorAll("article")].filter(a=>a.getAttribute("aria-hidden")==="false").map(a=>a.dataset.readingStation),text:e.innerText})')
def layout(page):
 return page.locator('.pillar-reading').evaluate('e=>{const p=e.getBoundingClientRect(),n=document.querySelector(".tour-stops").getBoundingClientRect(),h=document.querySelector("#tour-host").getBoundingClientRect(),a=e.querySelector("article[aria-hidden=false]"),b=a.querySelector(".pillar-reading-body"),r=b.getBoundingClientRect();return {fits:e.dataset.fits,anchorClear:e.dataset.anchorClear,fontSize:parseFloat(getComputedStyle(b).fontSize),panel:p.toJSON(),body:r.toJSON(),nav:n.toJSON(),stage:h.toJSON(),noHorizontalOverflow:document.documentElement.scrollWidth<=innerWidth,noInternalScroll:e.scrollHeight<=e.clientHeight+1&&a.scrollHeight<=a.clientHeight+1}}')
def contrast(page,label):
 meta=page.locator('.pillar-reading').evaluate("""e=>{const a=e.querySelector('article[aria-hidden=false]'),parts=[];for(const [group,n]of [['title',a.querySelector('h2')],...[...a.querySelectorAll('[data-reading-ink]')].map(n=>['body',n])]){const walker=document.createTreeWalker(n,NodeFilter.SHOW_TEXT);let t;while(t=walker.nextNode()){const rects=[];for(let i=0;i<t.length;i++){if(!t.textContent[i].trim())continue;const r=document.createRange();r.setStart(t,i);r.setEnd(t,i+1);for(const box of r.getClientRects())rects.push({x:box.x,y:box.y,width:box.width,height:box.height});}if(rects.length)parts.push({group,label:n.className,color:getComputedStyle(t.parentElement).color,rects});}}return parts;}""")
 article=page.locator('.pillar-reading article[aria-hidden=false]');prior=article.evaluate('e=>e.style.visibility');article.evaluate("e=>e.style.visibility='hidden'")
 raw=page.screenshot(path=str(OUT/f'{args.engine}-contrast-background-{label}.png'));article.evaluate('(e,v)=>e.style.visibility=v',prior);background=Image.open(BytesIO(raw)).convert('RGB')
 def lum(c):
  v=[x/255 for x in c];v=[x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v];return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
 ratios={};details=[]
 for part in meta:
  foreground=lum([int(x)for x in part['color'].removeprefix('rgb(').removesuffix(')').split(',')]);minimum=100;samples=0
  for r in part['rects']:
   for x in range(max(0,math.ceil(r['x'])),min(background.width,math.floor(r['x']+r['width'])),3):
    for y in range(max(0,math.ceil(r['y'])),min(background.height,math.floor(r['y']+r['height'])),3):
     l=lum(background.getpixel((x,y)));minimum=min(minimum,(max(l,foreground)+.05)/(min(l,foreground)+.05));samples+=1
  assert samples>0 and minimum>=4.5,(label,part['label'],minimum,samples)
  ratios[part['group']]=min(ratios.get(part['group'],100),minimum);details.append({'label':part['label'],'minimumRatio':minimum,'samples':samples})
 return {'station':label,'minimumRatios':ratios,'textParts':details,'method':'sample composed background at every real text-node character rectangle including notes, companies and direction labels; temporarily hide ink then restore; glow excluded'}

with sync_playwright() as p:
 options={'headless':args.engine=='chromium'}
 if args.engine=='chromium':options.update(executable_path=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 if args.engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if args.engine=='webkit'and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
 b=getattr(p,args.engine).launch(**options);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();watch(page)
 page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 assert 'STEP 05'in page.title()and page.locator('canvas').count()==1 and page.locator('.pillar-reading article').count()==3
 assert data(page)['magicStatus']=='ready'
 record('one production scene and three semantic reading stations',{'canvasCount':1,'articles':3,'resources':json.loads(data(page)['magicResources'])})
 keyviews=[];contrasts=[]
 for key,h,title,y in [('A1',1.74,'sakan',2.75),('A2',2.54,'现在与此前',1.8),('A3',3.34,'让想法成形',.85)]:
  go(page,h);d=data(page);r=panel(page);assert d['readingStation']==key and d['readingOpacity']=='1.0000000'and d['sceneTime']=='2.000000'
  assert abs(json.loads(d['cameraTarget'])[1]-y)<1e-7 and r['visibleArticles']==[key]
  assert page.get_by_role('heading',name=title,exact=True).count()==1
  other=page.locator(f'.pillar-reading article:not([data-reading-station={key}])');assert other.evaluate_all('es=>es.every(e=>e.inert&&e.getAttribute("aria-hidden")==="true"&&getComputedStyle(e).visibility==="hidden")')
  assert layout(page)['fits']=='true';page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.engine}-{key}.png'));keyviews.append({'key':key,'scene':d,'reader':r});contrasts.append(contrast(page,key))
 record('all three heights show the correct complete accessible biography layout',keyviews)
 record('actual composed backgrounds retain readable title and body contrast',contrasts)

 biography=[]
 for key,h,kind,expected in [
  ('A1',1.74,'identity',['sakan','张辰翰','萨坎','AIGC','战锤 40K']),
  ('A2',2.54,'experience',['现在','枫叶互动','AI 动画制作','此前','游族网络']),
  ('A3',3.34,'practice',['图像构建','AI 图像','影像制作','AI 视频与动画','交互表达','Vibe Coding','继续向下，进入 AI 影像。'])]:
  go(page,h);article=page.locator(f'.pillar-reading article[data-reading-station={key}]');assert article.get_attribute('data-reading-layout')==kind
  copied=article.evaluate('e=>{const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r);const t=s.toString();s.removeAllRanges();return t}')
  assert all(t in copied for t in expected),(key,copied)
  assert key not in copied and 'STEP'not in copied and '待补'not in copied
  assert len(''.join(copied.split()))<=90
  if key=='A2':
   assert article.get_by_role('list').count()==1 and article.get_by_role('listitem').count()==2
   rows=article.get_by_role('listitem').all_inner_texts();assert 'AI 动画制作'in rows[0]and '游族网络'in rows[1]and 'AI 动画制作'not in rows[1]
  if key=='A3':assert article.get_by_role('listitem').count()==3 and article.locator('button,a').count()==0
  bounds=article.evaluate('e=>{const p=e.parentElement.getBoundingClientRect();return [...e.querySelectorAll("h2,[data-reading-ink]")].map(n=>{const r=n.getBoundingClientRect();return {class:n.className,font:parseFloat(getComputedStyle(n).fontSize),inside:r.left>=p.left+12&&r.right<=p.right-12&&r.top>=p.top+12&&r.bottom<=p.bottom-12}})}')
  assert all(x['inside']for x in bounds),(key,bounds)
  assert all(x['font']>=16 for x in bounds if x['class']!='about-when')
  biography.append({'station':key,'layout':kind,'copiedText':copied,'textBounds':bounds})
 record('all approved facts, distinct layouts, list semantics and actual selectable text remain complete',biography)

 plateaus=[]
 for start in [1.3,2.1,2.9]:
  go(page,start+.8*.38);a=state(page);picture=image(page)
  go(page,start+.8*.72);assert state(page)==a and ImageChops.difference(picture,image(page)).getbbox()is None
  plateaus.append({'startH':start,'samplesH':[start+.8*.38,start+.8*.72],'pixelsExact':True})
 record('reading plateaus retain identical camera, text and visible scene',plateaus)

 phases=[]
 for start in [1.3,2.1,2.9]:
  for u in [.1,.18,.25,.55,.9,.97]:
   go(page,start+.8*u);d=data(page);effect=json.loads(d['magicFrame']);body=float(d['readingOpacity']);title=float(d['readingTitleOpacity'])
   if u==.1:assert body==0 and title==0 and effect['glyph']>0
   if u==.18:assert body==0 and title>0
   if u==.25:assert .44<body<.56 and title==1
   if u==.55:assert body==1 and title==1 and effect['dustVisible']==8
   if u==.9:assert .23<body<.32 and title>body
   if u==.97:assert body==0 and title>0
   active=page.locator('.pillar-reading article[aria-hidden=false] .pillar-reading-body')
   if u in [.18,.97]:assert active.get_attribute('aria-hidden')=='true'and active.evaluate('e=>getComputedStyle(e).visibility')=='hidden'
   phases.append({'h':float(d['displayH']),'body':body,'title':title,'glyph':effect['glyph'],'dust':effect['dustVisible']})
 go(page,2.02);frozen=state(page);picture=image(page);page.wait_for_timeout(550)
 assert state(page)==frozen and ImageChops.difference(picture,image(page)).getbbox()is None
 record('eighteen ordered glyph/title/body states and a mid-fade pause follow scroll',phases)

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
 for h in [1.74,2.54,3.34,2.08]:
  go(page,h);before=state(page);resize(page,1366,768)
  assert data(page)['readingStation']==before['readingStation'] and abs(float(data(page)['viewHeight'])-3.6)<1e-6
  if h!=2.08:
   r=layout(page);assert r['fits']=='true'and r['noHorizontalOverflow']and r['noInternalScroll'];page.screenshot(path=str(OUT/f'{args.engine}-1366-{data(page)["readingStation"]}.png'))
  resized.append({'h':h,'after':data(page)});resize(page,1440,900)
 record('resize preserves full-read and descending positions with legible layout',resized)

 go(page,2.54);picture=image(page);before=state(page);context_layout_before=panel(page)
 page.evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()')
 page.wait_for_selector('#tour-host[data-render-state="context-lost"]');assert page.locator('button:disabled').count()==11
 page.evaluate('window.__loss.restoreContext()');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 after_state=state(page);after_picture=image(page);context_difference=ImageChops.difference(picture,after_picture).getbbox()
 picture.save(OUT/f'{args.engine}-context-before.png');after_picture.save(OUT/f'{args.engine}-context-after.png')
 (OUT/f'{args.engine}-context-check.json').write_text(json.dumps({'before':before,'after':after_state,'layoutBefore':context_layout_before,'layoutAfter':panel(page),'difference':context_difference},ensure_ascii=False,indent=2)+'\n')
 assert after_state==before and context_difference is None,{'stateChanges':{k:[v,after_state[k]]for k,v in before.items()if v!=after_state[k]},'difference':context_difference}
 record('context restore preserves the reading camera, paragraph and actual image',{'pixelsExact':True,'disabledSceneControls':11})

 for h in [1.74,2.54,3.34,4.95]:go(page,h)
 page.wait_for_timeout(250);before=json.loads(data(page)['rendererStats']);nodes=page.locator('.pillar-reading article').count();child_nodes=page.locator('.pillar-reading *').count();document_nodes=page.locator('*').count();cycles=10 if args.engine=='chromium'else 2
 for _ in range(cycles):
  for h in [1.74,2.54,3.34,4.95]:go(page,h)
 page.wait_for_timeout(250);after=json.loads(data(page)['rendererStats'])
 for key,limit in [('geometries',54),('textures',4),('programs',10)]:assert before[key]==after[key]and after[key]<=limit
 assert before['pixel']['allocations']==after['pixel']['allocations']and page.locator('.pillar-reading article').count()==nodes
 assert page.locator('.pillar-reading *').count()==child_nodes and page.locator('*').count()==document_nodes
 draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(650);assert page.evaluate('window.__tourProbe.draws')==draws
 record('repeated reading tours retain GPU/DOM counts; settled pause stops drawing',{'cycles':cycles,'before':before,'after':after,'articles':nodes,'readerDescendants':child_nodes,'documentNodes':document_nodes,'allNodeCountsStable':True,'pausedDrawCount':draws})
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

 # The accepted real short biography must fit all three mobile stations.
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
  go(m,2.54);session=mobile.new_cdp_session(m);old=float(data(m)['displayH'])
  session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':420}]})
  for y in [380,340,300,260]:session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]});m.wait_for_timeout(35)
  session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(400);assert float(data(m)['displayH'])>old
 assert json.loads(data(m)['magicResources'])['pool']==12
 assert json.loads(data(m)['magicFrame'])['dustVisible']==0
 m.emulate_media(reduced_motion='no-preference');go(m,2.54);m.wait_for_function('JSON.parse(document.querySelector("#tour-host").dataset.magicFrame).dustVisible===4');assert json.loads(data(m)['magicFrame'])['dustVisible']==4
 mobile.close();record('three mobile reading stations fit, remain clear and support reduced-motion navigation',{'viewport':[390,844],'simulatedPhone':True,'nativeTouchDrag':args.engine=='chromium','stations':mobile_results})

 latency=page.evaluate('window.__tourProbe.settles');assert latency
 record('browser-observed settle latency retained, without hardware FPS claims',{'samples':len(latency),'p95Ms':sorted(latency)[int((len(latency)-1)*.95)],'maxMs':max(latency),'targetMs':200})
 if args.engine=='chromium':
  page.set_viewport_size({'width':1440,'height':1000})
  for mode in ['pixel','native']:
   page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');actual=image(page);prior=Image.open(OUT/f'before-reference-{mode}.png').convert('RGB');assert ImageChops.difference(prior,actual).getbbox()is None;page.locator('canvas').screenshot(path=str(OUT/f'after-reference-{mode}.png'))
  assert page.locator('.work-card').count()==3 and '枫叶互动'in page.locator('#about').inner_text()
  record('default portfolio and both scene render modes remain pixel-identical',{'modes':['pixel','native'],'exact':True})
 known=[x for x in issues if args.engine=='firefox'and('Depth texture comparison requests'in x['text']or'WebGL context was lost.'in x['text']or'This site appears to use a scroll-linked positioning effect.'in x['text'])];unexpected=[x for x in issues if x not in known];assert not unexpected,unexpected
 record('diagnostics retained, with no unidentified errors or warnings',{'knownFirefoxDiagnostics':len(known),'unexpected':unexpected})
 (OUT/f'verification-{args.engine}.json').write_text(json.dumps({'engine':args.engine,'version':b.version,'checks':checks,'issues':issues,'passed':True,'environment':'Linux software rendering; simulated phone; not Apple Safari or hardware FPS acceptance'},ensure_ascii=False,indent=2)+'\n');b.close()
