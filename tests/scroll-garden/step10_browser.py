"""Current visitor/debug journey, real native inputs, replay and GPU ownership."""
import argparse,math,re
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step10_common import *
parser=argparse.ArgumentParser();parser.add_argument('--engine',default='chromium');args=parser.parse_args();checks=[];issues=[]
def record(name,value):
 checks.append({'check':name,'passed':True,'evidence':value});save(f'journey-progress-{args.engine}.json',{'checks':checks,'issues':issues});print(args.engine+': '+name,flush=True)
def scene(page):return {k:data(page)[k]for k in ['cameraPosition','cameraTarget','viewHeight','sceneTime','magicFrame','filmMagicFrame','experimentMagicFrame']}
def picture(page):
 page.mouse.move(10,page.viewport_size['height']/2);frames(page);return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')
def pause_trace(page):
 return page.evaluate('''()=>new Promise(resolve=>{const rows=[],start=performance.now();let prior=-1,stable=0;function tick(){const draws=window.__tourProbe.draws;stable=draws===prior?stable+1:0;prior=draws;rows.push({ms:performance.now()-start,draws});if(stable>=3&&performance.now()-start>=120)resolve({settled:true,rows});else if(performance.now()-start>2000)resolve({settled:false,rows});else requestAnimationFrame(tick);}requestAnimationFrame(tick);})''')
def contrast(page,label):
 selectors='.tour-heading h1,.tour-kicker,#tour-note,.tour-scroll-cue,.tour-ending-actions button,.tour-stops button>span:last-child,.tour-actions>.mode-controls button,#tour-motion'
 meta=page.locator(selectors).evaluate_all('''es=>es.filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&getComputedStyle(e).visibility!=='hidden'&&!e.closest('[aria-hidden="true"]')}).map(e=>{
 const rects=[],walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let t;while(t=walker.nextNode()){if(t.parentElement.closest('[aria-hidden="true"]'))continue;for(let i=0;i<t.length;i++){if(!t.textContent[i].trim())continue;const range=document.createRange();range.setStart(t,i);range.setEnd(t,i+1);for(const r of range.getClientRects())rects.push({x:r.x,y:r.y,width:r.width,height:r.height});}}
 return{text:e.textContent,color:getComputedStyle(e).color,rects};})''')
 prior=page.locator(selectors).evaluate_all('es=>es.map(e=>{const v=e.style.color;e.style.color="transparent";return v})')
 raw=page.screenshot(path=str(OUT/f'{args.engine}-ui-contrast-{label}.png'));page.locator(selectors).evaluate_all('(es,old)=>es.forEach((e,i)=>e.style.color=old[i])',prior)
 background=Image.open(BytesIO(raw)).convert('RGB').resize((page.viewport_size['width'],page.viewport_size['height']),Image.Resampling.NEAREST)
 def lum(c):
  values=[v/255 for v in c];linear=[v/12.92 if v<=.04045 else((v+.055)/1.055)**2.4 for v in values];return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))
 results=[]
 for entry in meta:
  foreground=lum([float(v)for v in re.findall(r'[\d.]+',entry['color'])[:3]]);minimum=100;count=0
  for rect in entry['rects']:
   for x in range(max(0,math.ceil(rect['x'])),min(background.width,math.floor(rect['x']+rect['width'])),3):
    for y in range(max(0,math.ceil(rect['y'])),min(background.height,math.floor(rect['y']+rect['height'])),3):
     b=lum(background.getpixel((x,y)));minimum=min(minimum,(max(b,foreground)+.05)/(min(b,foreground)+.05));count+=1
  assert count>0 and minimum>=4.5,(label,entry['text'],minimum,count);results.append({'text':entry['text'],'minimumRatio':minimum,'samples':count})
 return results
with sync_playwright()as p:
 b=launch(p,args.engine);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page()
 page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}));page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['error','warning']else None);page.on('response',lambda r:issues.append({'type':'http','text':str(r.status)+' '+r.url})if r.status>=400 else None)
 ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');page.evaluate('window.__journeyCanvas=document.querySelector("canvas")');assert '张辰翰'in page.title()and'STEP'not in page.title()
 assert page.locator('canvas').count()==1 and page.locator('.tour-inspector').is_hidden()and page.locator('#tour-reference').is_hidden()
 assert all(x not in page.locator('main').inner_text()for x in ['本步仅验证','阅读区域预留','镜头数据'])
 assert '张辰翰'in page.locator('.tour-heading').inner_text()and page.locator('#tour-title').inner_text()=='让想象，动起来。'
 record('visitor opening names the author and hides engineering controls with one canvas',{'title':page.title(),'heading':page.locator('.tour-heading').inner_text(),'inspectorHidden':True,'referenceHidden':True})
 alpha=[]
 for h in [0,.35,.4,.45,.49,.5,.9,1.3,1.74,4.05,4.95,8.35,9.14,11.3,11.5,11.67,11.8,11.875,11.95,12.3]:
  go(page,h);frames(page);alpha.append({'h':float(data(page)['displayH']),'nativeScrollY':page.evaluate('scrollY'),'heading':page.locator('.tour-heading').evaluate('e=>({kind:e.dataset.kind,opacity:Number(e.dataset.opacity),text:e.textContent,transform:e.style.transform})'),'active':page.locator('.tour-stops [aria-current]').get_attribute('data-stop')})
 assert alpha[0]['heading']['opacity']==1 and alpha[4]['heading']['opacity']<.02 and alpha[-1]['heading']['kind']=='closing'and alpha[-1]['heading']['opacity']==1
 for entry in reversed(alpha):
  page.evaluate('y=>scrollTo({top:y,behavior:"instant"})',entry['nativeScrollY']);settled(page,entry['h']);frames(page);actual=float(page.locator('.tour-heading').get_attribute('data-opacity'));assert abs(actual-entry['heading']['opacity'])<1e-6,(entry,actual,data(page))
 record('opening, reading, transfers, water and closing derive reversible UI from native H',alpha)
 go(page,9.004);frames(page);page.evaluate('''()=>{window.__headingChanges=0;window.__headingObserver=new MutationObserver(()=>window.__headingChanges++);window.__headingObserver.observe(document.querySelector('.tour-heading'),{subtree:true,childList:true,characterData:true});const range=document.createRange();range.selectNodeContents(document.querySelector('#tour-title'));const selection=getSelection();selection.removeAllRanges();selection.addRange(range);}''');selected=page.evaluate('getSelection().toString()');go(page,9.276);frames(page)
 assert page.evaluate('window.__headingChanges')==0 and page.evaluate('getSelection().toString()')==selected
 page.evaluate('window.__headingObserver.disconnect();getSelection().removeAllRanges()')
 record('held reading preserves actual title text nodes and user text selection',{'sameFullReadingWindow':[9.004,9.276],'headingTextMutations':0,'selectedText':selected})
 history=page.evaluate('history.length');navigation=[]
 for key,h in [('overview',0),('about',1.74),('films',4.95),('experiments',9.14),('water',11.5)]:
  page.locator(f'#tour-stop-{key}').click();settled(page,h);frames(page);assert page.locator('.tour-stops [aria-current]').count()==1 and page.locator(f'#tour-stop-{key}').get_attribute('aria-current')=='location'
  assert page.evaluate('document.activeElement.id')=='tour-stop-'+key;navigation.append({'chapter':key,'requestedH':h,'actualH':data(page)['displayH']})
 assert page.evaluate('history.length')==history and '#'not in page.url
 page.evaluate('()=>{for(const key of["about","water","films"])document.querySelector("#tour-stop-"+key).click()}');page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.003&&document.querySelector("#tour-host").dataset.cameraState==="settled"')
 record('five real chapter controls and latest rapid selection preserve focus and history',navigation)
 page.locator('#tour-stop-water').click();settled(page,11.5);before=scene(page);pic=picture(page);oldY=page.evaluate('scrollY');page.mouse.wheel(0,15);page.wait_for_function('y=>scrollY>y',arg=oldY);page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
 assert scene(page)==before and ImageChops.difference(pic,picture(page)).getbbox()is None
 record('native wheel crosses part of water hold with exact camera and paused canvas',{'start':11.5,'endH':data(page)['displayH'],'cameraExact':True,'canvasExact':True})
 stationViews=[]
 for key,h in STOPS:
  go(page,h);frames(page);selector='.pillar-reading'if key.startswith('A')else'.film-reading'if key.startswith('B')else'.experiment-reading'
  layout=page.locator(selector).evaluate('e=>({fits:e.dataset.fits,clear:e.dataset.anchorClear,rect:e.getBoundingClientRect().toJSON(),text:e.innerText})');assert layout['fits']==layout['clear']=='true'
  assert page.locator('.tour-heading').get_attribute('data-kind')=='reading';stationViews.append({'station':key,'layout':layout})
 record('all ten full-reading stations retain complete biography, sample and project layouts',stationViews)
 globalContrast=[]
 for key,h in [('opening',0),('water',11.5),('ending',12.3)]:go(page,h);frames(page);globalContrast.append({'pose':key,'contrast':contrast(page,key)})
 record('new heading, navigation, ending and mode controls pass actual-background contrast',globalContrast)
 go(page,12.3);frames(page);trace=pause_trace(page);assert trace['settled'];draws=page.evaluate('window.__tourProbe.draws');current=scene(page);page.wait_for_timeout(400)
 assert scene(page)==current and page.evaluate('window.__tourProbe.draws')==draws and page.locator('#tour-percent').inner_text()=='100%'
 page.locator('[data-tour-replay=overview]').click();settled(page,0);assert page.evaluate('document.activeElement.id')=='tour-stop-overview'and scene(page)['sceneTime']==current['sceneTime']and page.locator('#tour-percent').inner_text()=='0%'
 go(page,12.3);page.locator('[data-tour-replay=films]').click();settled(page,4.95);assert page.evaluate('document.activeElement.id')=='tour-stop-films'
 record('ending stays at native bottom and replay restores target focus without resetting clock',{'pauseTrace':trace,'bottomNoAutomaticLoop':True,'zeroAnd100Correct':True,'sameCanvas':page.evaluate('window.__journeyCanvas===document.querySelector("canvas")')})
 page.locator('#tour-stop-about').focus();page.keyboard.press('Home');settled(page,0);page.keyboard.press('End');settled(page,12.3);assert page.evaluate('document.activeElement.id')=='tour-stop-about'
 page.locator('#tour-stop-films').focus();page.keyboard.press('Enter');settled(page,4.95);assert page.evaluate('document.activeElement.id')=='tour-stop-films'
 record('native Home, End and Enter navigation retain keyboard focus',{'nativeDocumentKeys':True,'endingDoesNotStealFocus':True})
 caches=[]
 for mode in ['pixel','native','pixel']:
  page.locator(f'.tour-actions [data-mode={mode}]').click()
  for _,h in VIEWS:go(page,h)
  go(page,12);go(page,12.3);frames(page);caches.append(json.loads(data(page)['rendererStats']))
 baseline=json.loads((OUT/'baseline-before.json').read_text())['fullWarmCaches']
 for old,new in zip(baseline,caches):
  for key in ['geometries','textures','programs','calls']:assert old[key]==new[key],(key,old,new)
 record('full-route both-mode GPU caches and identical overview draw calls add nothing',{'before':baseline,'after':caches})
 nodes=page.locator('*').count();resources=json.loads(data(page)['rendererStats']);cycles=[]
 for i in range(10):
  go(page,12.3);page.locator('[data-tour-replay=overview]').click();settled(page,0);page.locator('#tour-stop-films').click();settled(page,4.95);go(page,12.3)
  assert page.locator('canvas').count()==1 and not page.locator('video').count();cycles.append(data(page)['sceneTime'])
 assert page.locator('*').count()==nodes and all(json.loads(data(page)['rendererStats'])[k]==resources[k]for k in ['geometries','textures','programs'])
 record('ten ending/opening/film/replay cycles retain DOM, one canvas and GPU ownership',{'cycles':10,'times':cycles,'DOMNodes':nodes,'activeVideos':0})
 page.locator('.tour-actions [data-mode=native]').click();page.bring_to_front();page.wait_for_function('!document.hidden');t=data(page)['sceneTime'];page.locator('#tour-motion').click();page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+.1',arg=t);page.locator('#tour-motion').click();t=data(page)['sceneTime'];go(page,12.3);page.locator('[data-tour-replay=overview]').click();settled(page,0)
 assert data(page)['sceneTime']==t and data(page)['motionState']=='paused'and page.locator('canvas').get_attribute('data-render-mode')=='native'
 record('latest explicit mode and manual pause survive replay with exact environment time',{'mode':'native','time':t,'motion':'paused'})
 mobileOptions={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True,'reduced_motion':'reduce'}
 if args.engine!='firefox':mobileOptions['is_mobile']=True
 mobile=b.new_context(**mobileOptions);mobile.add_init_script(PROBE);m=mobile.new_page();ready(m,'http://127.0.0.1:4173/?tour=prototype');assert data(m)['motionState']=='paused';mobileViews=[]
 for key,h in STOPS:
  go(m,h);frames(m);selector='.pillar-reading'if key.startswith('A')else'.film-reading'if key.startswith('B')else'.experiment-reading';assert m.locator(selector).get_attribute('data-fits')=='true';assert not m.evaluate('document.documentElement.scrollWidth>innerWidth');mobileViews.append(key)
 m.locator('#tour-stop-water').tap();settled(m,11.5);go(m,12.3);assert m.locator('.tour-heading').evaluate('e=>getComputedStyle(e).transform')=='none';m.locator('[data-tour-replay=overview]').tap();settled(m,0)
 assert m.locator('.tour-stops button').evaluate_all('es=>es.every(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&parseFloat(getComputedStyle(e).fontSize)>=12})')
 m.screenshot(path=str(OUT/f'{args.engine}-portrait-opening.png'));mobile.close()
 record('portrait touch, twelve-pixel chapter labels and reduced-motion opening/replay stay usable',{'viewport':[390,844],'DPR':2,'simulated':True,'fullStations':mobileViews,'nativeTap':True,'extraGlobalMotionSuppressed':True})
 ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2&debug=1');assert 'STEP 10'in page.title()and page.locator('#tour-reference').is_visible();page.locator('.tour-inspector summary').click();page.locator('[data-reading-stop=C3]').click();settled(page,10.83);assert 'C3'in page.locator('#tour-inspector-data').inner_text();page.locator('.tour-inspector summary').click();assert page.locator('canvas').count()==1
 record('explicit debug entry retains working station controls and reference without another scene',{'query':'debug=1','station':'C3','oneCanvas':True})
 known=[i for i in issues if args.engine=='firefox'and any(t in i['text']for t in ['Depth texture comparison requests','WebGL context was lost.','This site appears to use a scroll-linked positioning effect.'])];unexpected=[i for i in issues if i not in known];assert not unexpected,unexpected
 record('current normal and debug browser diagnostics contain no unknown failures',{'knownFirefox':known,'unexpected':unexpected})
 save(f'journey-verification-{args.engine}.json',{'passed':True,'engine':args.engine,'version':b.version,'checks':checks,'issues':issues,'hardwareFPSProof':False,'limits':'software rendering, simulated portrait, GTK WebKit is not Apple Safari'});b.close()
