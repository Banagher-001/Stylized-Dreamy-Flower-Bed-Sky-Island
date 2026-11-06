"""Step11 real-browser contracts: one semantic document, native input, responsive return."""
import argparse,hashlib,math
from playwright.sync_api import sync_playwright
from step11_common import *
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
checks=[];issues=[]
original_go=go
def go(page,h):
 page.bring_to_front();original_go(page,h)
def record(name,evidence):
 checks.append({'check':name,'passed':True,'evidence':evidence});print(args.engine+': '+name,flush=True)
def open_page(context,w=1440,h=900,reduced=False):
 page=context.new_page();page.set_viewport_size({'width':w,'height':h});page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}));page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['error','warning']else None)
 page.bring_to_front();page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');frames(page);return page
def mode(page):return page.locator('main').get_attribute('data-reading-mode')
def flow_go(page,key):
 page.bring_to_front()
 page.locator(f'.tour-reading-flow [data-flow-anchor="{key}"]').evaluate('e=>{const r=e.getBoundingClientRect(),h=document.querySelector(".tour-header").getBoundingClientRect();scrollTo({top:scrollY+r.top-h.bottom-15,behavior:"instant"})}')
 frames(page);page.wait_for_function('k=>document.querySelector("main").dataset.flowAnchor===k',arg=key)
def stable(page):
 page.bring_to_front()
 if mode(page)!='stable':page.locator('#tour-layout-toggle').click()
 frames(page);assert mode(page)=='stable'
def audit_flow(page,minimum=16):
 rows=page.locator('.tour-reading-flow article').evaluate_all('''es=>es.map(e=>{const r=e.getBoundingClientRect(),b=e.querySelector('[class$="-body"]'),s=getComputedStyle(b);return{id:e.dataset.flowAnchor,hidden:e.hidden,inert:e.inert,aria:e.getAttribute('aria-hidden'),visible:getComputedStyle(e).visibility,font:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),clamp:s.webkitLineClamp,overflow:e.scrollWidth-e.clientWidth,heightOverflow:e.scrollHeight-e.clientHeight,text:e.innerText,buttons:[...e.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();return{w:r.width,h:r.height,disabled:b.disabled}})}})''')
 assert len(rows)==10 and [r['id']for r in rows]==[k for k,_ in STOPS]
 for r in rows:
  assert not r['hidden']and not r['inert']and r['aria']=='false'and r['visible']=='visible',(r['id'],r)
  assert r['font']>=minimum-.1 and r['overflow']<=1 and r['heightOverflow']<=1,(r['id'],r)
  assert all(x['w']>=44 and x['h']>=44 for x in r['buttons']),r
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 ids=page.locator('[id]').evaluate_all('es=>es.map(e=>e.id)');assert len(ids)==len(set(ids))
 return rows
def pause_still(page):
 # Layout and finite still frames may finish; once stable require an uninterrupted window.
 page.wait_for_timeout(250);a=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(400);b=page.evaluate('window.__tourProbe.draws');assert a==b,(a,b);return{'draws':b,'zeroDrawWindowMs':400}
def snapshot(page):return page.evaluate('({y:scrollY,mode:document.querySelector("main").dataset.readingMode,anchor:document.querySelector("main").dataset.flowAnchor,h:document.querySelector("#tour-host").dataset.displayH})')
with sync_playwright()as p:
 browser=launch(p,args.engine);context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE)
 page=open_page(context);assert mode(page)=='immersive'
 page.evaluate('window.__readingCanvas=document.querySelector("canvas");window.__readingNodes=[...document.querySelectorAll(".tour-reading-flow article")];window.__readingText=window.__readingNodes.map(e=>e.textContent)')
 record('one original canvas and exactly ten original semantic inscription nodes',{'capacity':json.loads(page.locator('main').get_attribute('data-reading-capacity')),'articles':10,'canvas':1})
 views=[]
 for key,h in STOPS:
  go(page,h);frames(page)
  panel=page.locator('.pillar-reading'if key.startswith('A')else'.film-reading'if key.startswith('B')else'.experiment-reading')
  state=panel.evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),active:[...e.querySelectorAll("article")].filter(e=>e.getAttribute("aria-hidden")==="false").map(e=>e.dataset.flowAnchor)})')
  assert state['data']['fits']=='true'and state['active']==[key],(key,state)
  views.append({'id':key,'h':h,'panel':state})
 page.screenshot(path=str(OUT/f'{args.engine}-desktop-C3.png'));record('desktop ten held stations retain full readable state and projected focus clearance',views)
 go(page,2.61);original=snapshot(page);cycles=[]
 for i in range(10):
  stable(page);assert page.locator('main').get_attribute('data-flow-anchor')=='A2'
  audit_flow(page);assert page.locator('#tour-layout-toggle').is_enabled()
  page.locator('#tour-layout-toggle').click();settled(page,2.61);assert page.locator('.tour-heading').get_attribute('aria-hidden')!='true'and not page.locator('.tour-heading').evaluate('e=>e.inert');now=snapshot(page);assert abs(now['y']-original['y'])<=1,(i,original,now);cycles.append(now)
 assert page.evaluate('window.__readingCanvas===document.querySelector("canvas")&&window.__readingNodes.every((n,i)=>n===document.querySelectorAll(".tour-reading-flow article")[i]&&n.textContent===window.__readingText[i])')
 record('ten layout round trips preserve exact native position, text nodes, content and canvas',{'before':original,'after':cycles,'maximumCssPixelDrift':max(abs(c['y']-original['y'])for c in cycles)})
 go(page,2.54);page.evaluate('''()=>{const n=document.querySelector('.about-company').firstChild;window.__selectedNode=n;const r=document.createRange();r.selectNodeContents(n);getSelection().removeAllRanges();getSelection().addRange(r);window.__selectedText=getSelection().toString()}''')
 page.mouse.move(1100,350);page.mouse.wheel(0,5);page.wait_for_timeout(250)
 assert page.evaluate('getSelection().toString()===window.__selectedText&&document.querySelector(".about-company").firstChild===window.__selectedNode')
 stable(page);assert page.evaluate('getSelection().toString()===window.__selectedText');page.locator('#tour-layout-toggle').click();frames(page);assert page.evaluate('getSelection().toString()===window.__selectedText');page.evaluate('getSelection().removeAllRanges()')
 record('actual text selection survives native scroll and both layout transitions',{'text':'枫叶互动','sameTextNode':True})
 stable(page);flow_go(page,'B3');page.locator('#tour-layout-toggle').click();settled(page,6.84);record('reading another stable station returns to its full existing immersive stop',{'stableStation':'B3','returnH':data(page)['displayH']})
 stable(page);flow_go(page,'C2');before=snapshot(page);page.locator('[data-project-tab=archive]').click();frames(page)
 assert page.locator('dialog[open]').count()==1;page.locator('.tour-project-archive').evaluate('e=>e.scrollTop=400');page.locator('.tour-project-close').click();frames(page);after=snapshot(page);assert before['anchor']==after['anchor']=='C2'and abs(before['y']-after['y'])<=1
 page.wait_for_function('document.activeElement?.dataset.projectTab==="archive"')
 record('stable archive close restores the actual document position and source focus',{'before':before,'after':after})
 # Mobile is its own native touch-capable browser context, without reduced motion.
 kw={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True}
 if args.engine=='chromium':kw['is_mobile']=True
 # GTK fixedLayout viewport rotation lags its screen override; use a touch-enabled
 # layout viewport for rotation. Separate dialogs tests retain is_mobile=True at fixed sizes.
 mobile=browser.new_context(**kw);mobile.add_init_script(PROBE);phone=open_page(mobile,390,844);assert mode(phone)=='immersive'
 phone_views=[]
 for key,h in STOPS:
  go(phone,h);frames(phone)
  panel=phone.locator('.pillar-reading'if key.startswith('A')else'.film-reading'if key.startswith('B')else'.experiment-reading');r=panel.evaluate('e=>({fits:e.dataset.fits,clear:e.dataset.anchorClear,rect:e.getBoundingClientRect().toJSON(),nav:document.querySelector(".tour-stops").getBoundingClientRect().toJSON()})')
  assert r['fits']=='true'and r['clear']=='true'and r['rect']['bottom']<=r['nav']['top']-15.5,(key,r)
  phone_views.append({'id':key,**r})
 phone.screenshot(path=str(OUT/f'{args.engine}-phone-immersive-C3.png'));record('390 phone keeps immersive scroll and all ten readable stations',phone_views)
 go(phone,1.74)
 if args.engine=='chromium':
  cdp=mobile.new_cdp_session(phone);prior=phone.evaluate('scrollY');cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':350}]})
  for y in [310,270,230,190]:cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]});phone.wait_for_timeout(35)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});phone.wait_for_timeout(500);assert phone.evaluate('scrollY')>prior
  record('native Chromium touch drag advances the original document route',{'beforeY':prior,'afterY':phone.evaluate('scrollY'),'physicalDevice':False})
 phone.locator('#tour-layout-toggle').tap();frames(phone);assert mode(phone)=='stable';flow_go(phone,'C2');orientation=[]
 for i in range(10):
  for w,h in [(844,390),(390,844)]:
   phone.set_viewport_size({'width':w,'height':h});
   phone.wait_for_timeout(200);frames(phone);cssWidth=phone.evaluate('()=>{const e=document.createElement("i");e.style.cssText="position:fixed;width:100vw;visibility:hidden";document.body.append(e);const w=e.getBoundingClientRect().width;e.remove();return w}');assert abs(cssWidth-w)<1;s=snapshot(phone);assert s['mode']=='stable'and s['anchor']=='C2',(i,w,s);orientation.append(s)
 phone.wait_for_function('document.querySelector("main").dataset.immersiveAvailable==="true"');phone.screenshot(path=str(OUT/f'{args.engine}-phone-stable-C2.png'))
 record('ten portrait-landscape round trips preserve station and remain stable until explicit choice',orientation)
 # Short screens need an entire document, not a clipped fixed reader.
 sizes=[(320,568),(375,667),(430,932),(667,375),(844,390),(768,1024)]if args.engine=='chromium'else[(320,568),(844,390)]
 matrix=[]
 for w,h in sizes:
  m=open_page(context,w,h);initial=mode(m);cap=json.loads(m.locator('main').get_attribute('data-reading-capacity'));assert (initial=='immersive')==cap['fits']
  stable(m);audit=audit_flow(m)
  for key,_ in STOPS:flow_go(m,key)
  m.locator('#tour-stop-about').click();frames(m);assert m.locator('main').get_attribute('data-flow-anchor')=='A1'
  m.locator('#tour-stop-water').click();frames(m);assert m.locator('main').get_attribute('data-flow-anchor')=='water'
  m.screenshot(path=str(OUT/f'{args.engine}-stable-{w}-{h}.png'));matrix.append({'viewport':[w,h],'initialMode':initial,'capacity':cap,'readableStations':[r['id']for r in audit],'documentOverflow':m.evaluate('document.documentElement.scrollWidth-innerWidth')});m.close()
 record('small portrait, short landscape and tablet use measured capacity and full natural reading',matrix)
 # 200% rem scaling is deliberately labelled a layout simulation, not OS/native text zoom.
 phone.bring_to_front();phone.set_viewport_size({'width':390,'height':844});phone.evaluate('document.documentElement.style.fontSize="200%"');phone.wait_for_timeout(400);frames(phone);assert mode(phone)=='stable';assert phone.locator('main').get_attribute('data-flow-anchor')=='C2';audit_flow(phone,32);flow_go(phone,'B1');phone.screenshot(path=str(OUT/f'{args.engine}-200percent-text.png'))
 before=snapshot(phone);phone.locator('[data-film-station=B1] .film-image-button').click();phone.wait_for_selector('.film-dialog[data-state="ready"]');frames(phone)
 close=phone.locator('.film-dialog-close').bounding_box();assert close and close['y']>=0 and close['y']+close['height']<=844 and close['width']>=44 and close['height']>=44
 phone.locator('.film-dialog-shell').evaluate('e=>e.scrollTop=e.scrollHeight');phone.locator('.film-dialog-close').click();frames(phone);after=snapshot(phone);assert abs(before['y']-after['y'])<=1
 flow_go(phone,'C2');phone.locator('[data-project-tab=live]').click();frames(phone);phone.locator('.tour-project-shell').evaluate('e=>e.scrollTop=100');frames(phone);assert phone.locator('canvas').count()==1;phone.screenshot(path=str(OUT/f'{args.engine}-200percent-live.png'));phone.locator('.tour-project-close').click();frames(phone);assert phone.locator('main').get_attribute('data-flow-anchor')=='C2'
 record('200% text layout keeps full content, closes both viewers and restores reading',{'method':'root rem scale 200%, not native browser text zoom or real OS setting','bodyCssPixels':32,'filmBefore':before,'filmAfter':after})
 phone.evaluate('document.documentElement.style.fontSize=""');phone.wait_for_timeout(350);frames(phone)
 # Long content is injected only into the test page and the original node is restored.
 body=phone.locator('[data-reading-station=A1] .about-role');old=body.inner_text();body.evaluate('(e,t)=>e.textContent=t','长度测试，不作为个人介绍。'+('测试完整长段落的自然阅读与换行。'*12));phone.wait_for_timeout(350);stable(phone);audit_flow(phone);flow_go(phone,'A1');assert len(body.inner_text())>200;body.evaluate('(e,t)=>e.textContent=t',old);phone.wait_for_timeout(350)
 record('temporary >200-character sample stays complete in flow and is removed afterwards',{'testOnly':True,'originalContentRestored':body.inner_text()==old})
 # Initial and runtime media query changes are browser media emulation, not a custom UI flag.
 reduced_context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');reduced_context.add_init_script(PROBE);rm=open_page(reduced_context,390,844);assert mode(rm)=='stable'and rm.locator('#tour-motion').inner_text()=='播放动效'
 camera={k:data(rm)[k]for k in ['cameraPosition','cameraTarget','viewHeight','sceneTime']};flow_go(rm,'A2');rm.mouse.wheel(0,180);rm.wait_for_timeout(400);assert camera=={k:data(rm)[k]for k in camera}
 rm.emulate_media(reduced_motion='no-preference');rm.wait_for_timeout(350);assert mode(rm)=='stable'and rm.locator('#tour-motion').inner_text()=='播放动效'
 rm.locator('#tour-stop-overview').click();frames(rm);rm.locator('#tour-motion').click();rm.wait_for_function('Number(document.querySelector("#tour-host").dataset.sceneTime)>2.1');assert mode(rm)=='stable';rm.locator('#tour-motion').click()
 rm.locator('#tour-layout-toggle').click();frames(rm);assert mode(rm)=='immersive';go(rm,2.54);rm.emulate_media(reduced_motion='reduce');rm.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');assert rm.locator('main').get_attribute('data-flow-anchor')=='A2'
 record('reduced motion stops continuous camera, keeps pause on preference removal and separates explicit environment playback',{'initialStable':True,'scrollCameraUnchanged':camera,'explicitImmersiveRequired':True})
 # Original native keyboard keys and semantic skip link.
 page.locator('#tour-layout-toggle').click();frames(page);assert mode(page)=='immersive';page.locator('#tour-stop-about').focus();page.keyboard.press('Home');settled(page,0);page.keyboard.press('End');settled(page,12.3)
 page.locator('#tour-stop-films').focus();page.keyboard.press('Enter');settled(page,4.95);assert page.evaluate('document.activeElement.id')=='tour-stop-films'
 page.locator('.tour-skip').focus();page.keyboard.press('Enter');frames(page);assert mode(page)=='stable'and page.evaluate('document.activeElement.id')=='reading-A1-title'
 record('Home End Enter and skip-to-content preserve native keys and valid focus',{'skipFocus':'reading-A1-title','noGlobalKeyInterception':True})
 # Warm archive and decoder before checking ownership across repeated opens.
 flow_go(page,'C2');page.locator('[data-project-tab=live]').click();frames(page);page.locator('[data-project-view=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.readyState>=1');page.locator('.tour-project-close').click();frames(page)
 nodes=page.locator('*').count();stats=json.loads(data(page)['rendererStats']);media_cycles=[]
 for i in range(10):
  page.locator('[data-project-tab=live]').click();frames(page);page.locator('[data-project-view=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.readyState>=1');page.locator('.tour-project-close').click();frames(page)
  assert page.locator('video').count()==0 and page.locator('dialog[open]').count()==0 and page.locator('canvas').count()==1
  assert page.locator('main').get_attribute('data-flow-anchor')=='C2';media_cycles.append(json.loads(data(page)['rendererStats']))
 assert page.locator('*').count()==nodes and all(all(s[k]==stats[k]for k in ['geometries','textures','programs'])for s in media_cycles)
 still=pause_still(page);record('ten live/archive/video cycles release media, retain one canvas and stable resources, then draw zero offscreen',{'nodes':nodes,'before':stats,'after':media_cycles,'pause':still})
 flow_go(page,'ending');page.locator('[data-flow-go=opening]').focus();page.keyboard.press('Enter');frames(page);assert page.evaluate('scrollY===0&&document.activeElement.id==="tour-stable-title"')
 flow_go(page,'ending');page.locator('[data-flow-go=B1]').focus();page.keyboard.press('Enter');frames(page);assert page.locator('main').get_attribute('data-flow-anchor')=='B1'and page.evaluate('document.activeElement.id')=='film-B1-title'
 record('stable ending replay focuses its visible destination heading for keyboard continuation',{'openingFocus':'tour-stable-title','filmFocus':'film-B1-title'})
 # Small safety inset simulation proves CSS arithmetic, not actual notched hardware.
 phone.add_style_tag(content='.tour-header{padding-top:calc(14px + 28px)!important;padding-inline:calc(16px + 12px)!important}.tour-footer{padding-bottom:calc(15px + 24px)!important}')
 frames(phone);assert phone.locator('#tour-layout-toggle').bounding_box()['x']>=16;assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 record('simulated safe padding preserves controls and native document width',{'simulatedOnly':True,'topInset':28,'sideInset':12,'bottomInset':24})
 unexpected=[x for x in issues if x['type']=='exception'or(x['type']=='error'and not(args.engine=='firefox'and'WebGL context was lost'in x['text']))]
 assert not unexpected,unexpected
 save(f'browser-{args.engine}.json',{'passed':True,'engine':args.engine,'version':browser.version,'checks':checks,'diagnostics':issues,'physicalDevice':False,'phoneEmulation':{'hasTouch':True,'DPR':2,'mobileViewportFlag':args.engine=='chromium','webkitFixedMobileViewportsCoveredInDialogsSuite':args.engine=='webkit'},'environment':'Linux software graphics; Firefox/GTK WebKit are not physical iOS/Android; rem scaling is not native text zoom.'})
 print(args.engine,'PASS',len(checks),'groups',flush=True);browser.close()
