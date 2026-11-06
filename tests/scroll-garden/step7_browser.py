"""Current production C chapter, actual project layer, native media and restoration."""
from io import BytesIO
import argparse,ast,math
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step7_common import *

parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
source=(ROOT/'tests/scroll-garden/step5_browser.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='contrast')
contrast_source=ast.get_source_segment(source,node).replace('.pillar-reading','.experiment-reading').replace('data-reading-ink','data-experiment-ink')
contrast_source=contrast_source.replace("background=Image.open(BytesIO(raw)).convert('RGB')","background=Image.open(BytesIO(raw)).convert('RGB');background=background.resize((page.viewport_size['width'],page.viewport_size['height']),Image.Resampling.NEAREST)")
exec(compile(contrast_source,'<actual contrast>','exec'))
checks=[];issues=[];requests=[]
def record(name,evidence):checks.append({'check':name,'passed':True,'evidence':evidence});print(args.engine+': '+name,flush=True)
def watch(page):
    page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}));page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
    page.on('response',lambda r:issues.append({'type':'http','text':str(r.status)+' '+r.url})if r.status>=400 else None)
def state(page):
    d=data(page);return {k:d[k] for k in ['cameraPosition','cameraTarget','viewHeight','experimentStation','experimentPhase','experimentPresentation','experimentMagicFrame','sceneTime']}
def picture(page):
    page.mouse.move(10,page.viewport_size['height']/2);frames(page);return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')
def layout(page):
    return page.locator('.experiment-reading').evaluate('e=>{const r=e.getBoundingClientRect(),a=e.querySelector("article:not([hidden])");return{data:{...e.dataset},rect:r.toJSON(),nav:document.querySelector(".tour-stops").getBoundingClientRect().toJSON(),horizontalOverflow:document.documentElement.scrollWidth>innerWidth,internalScroll:e.scrollHeight>e.clientHeight+1,text:a.innerText,textBoxes:[...a.querySelectorAll("h2,[data-experiment-ink]")].map(n=>{const b=n.getBoundingClientRect();return{text:n.textContent,font:parseFloat(getComputedStyle(n).fontSize),inside:b.left>=r.left+10&&b.right<=r.right-10&&b.top>=r.top+10&&b.bottom<=r.bottom-10}}),buttons:[...a.querySelectorAll("button")].map(b=>({disabled:b.disabled,rect:b.getBoundingClientRect().toJSON()}))}}')
def validate(page):
    r=layout(page);assert r['data']['fits']=='true'and r['data']['anchorClear']=='true'and not r['horizontalOverflow']and not r['internalScroll'],r
    assert all(t['inside']and t['font']>=16 for t in r['textBoxes']),r
    assert all(not b['disabled']and b['rect']['width']>=44 and b['rect']['height']>=44 for b in r['buttons']),r
    return r
def open_project(page,tab='live'):
    page.locator(f'[data-project-tab={tab}]').click();page.wait_for_selector(f'.tour-project-dialog[open][data-tab={tab}]');frames(page)
def close_project(page):
    page.locator('.tour-project-close').click();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');frames(page)
def project_controls(page):
    return page.locator('.tour-project-dialog').evaluate('e=>{const s=e.getBoundingClientRect();return [...e.querySelectorAll("button")].filter(b=>b.getClientRects().length&&!b.hidden).map(b=>{const r=b.getBoundingClientRect();return{text:b.textContent,width:r.width,height:r.height,inside:r.left>=s.left&&r.right<=s.right&&r.top>=s.top&&r.bottom<=s.bottom}})}')

with sync_playwright() as p:
    b=launch(p,args.engine);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();watch(page);page.on('request',lambda r:requests.append(r.url))
    page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');assert 'STEP 07'in page.title()
    assert page.locator('canvas').count()==1 and page.locator('.experiment-reading article').count()==3 and not page.locator('video').count()
    assert data(page)['experimentMagicStatus']=='ready'and json.loads(data(page)['experimentMagicResources'])['pool']==24
    cold=list(requests);assert not any('.webp'in x or '.mp4'in x for x in cold),cold
    go(page,8.1);page.wait_for_function('document.querySelector(".experiment-cover img").complete&&document.querySelector(".experiment-cover img").naturalWidth===1440')
    assert any('courtyard-interactive-cover'in x for x in requests)and not any('.mp4'in x for x in requests)
    record('one actual scene, three C stations, late real-cover loading and no automatic video',{'coldRequests':cold,'approachRequests':requests,'resources':json.loads(data(page)['experimentMagicResources'])})
    views=[]
    for key,h,y in STOPS:
        go(page,h);frames(page);r=validate(page);d=data(page)
        assert d['experimentStation']==key and abs(json.loads(d['cameraTarget'])[1]-y)<1e-7
        assert page.locator('[data-stop=experiments]').get_attribute('aria-current')=='location'
        assert page.locator('.pillar-reading').get_attribute('aria-hidden')=='true'and page.locator('.film-reading').get_attribute('aria-hidden')=='true'
        assert page.locator('.experiment-reading article[aria-hidden=true]').evaluate_all('es=>es.every(e=>e.hidden&&e.inert)')
        if key=='C1':assert 'Vibe Coding'in r['text']and page.locator('.experiment-process li').count()==3
        if key=='C2':assert '庭院习作'in r['text']and len(r['buttons'])==2
        if key=='C3':assert '让想象，动起来。'in r['text']and '继续向下，回到水潭。'in r['text']and not r['buttons']
        assert all(x not in r['text'] for x in ['待补','GitHub','STEP'])
        page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.engine}-{key}.png'));views.append({'station':key,'scene':d,'layout':r,'contrast':contrast(page,key)})
    record('three accurate full-reading layouts and measured text/background contrast',views)
    plateaus=[]
    for start,duration in [(8.7,.8),(9.5,1),(10.5,.6)]:
        go(page,start+duration*.38);a=state(page);pic=picture(page);go(page,start+duration*.72);assert state(page)==a and ImageChops.difference(pic,picture(page)).getbbox()is None;plateaus.append({'start':start,'pixelsExact':True})
    record('all three full-reading windows keep exact camera, text and paused pixels',plateaus)
    phases=[]
    for start,duration in [(8.7,.8),(9.5,1),(10.5,.6)]:
        for u in [.1,.18,.25,.55,.9,.97]:
            go(page,start+duration*u);d=data(page);s=json.loads(d['experimentPresentation']);g=json.loads(d['experimentMagicFrame'])
            if u==.1:assert s['title']==s['body']==0 and g['glyph']>0
            if u==.18:assert s['title']>0 and s['body']==0
            if u==.25:assert s['title']==1 and .44<s['body']<.56
            if u==.55:assert s['title']==s['body']==1 and g['dustVisible']==8
            if u==.9:assert s['title']>s['body']and s['body']<.5
            if u==.97:assert s['body']==0 and s['title']>0
            if u in [.18,.97]:assert page.locator('.experiment-reading article:not([hidden]) button:enabled').count()==0
            phases.append({'station':d['experimentStation'],'requestedU':u,'actualH':d['displayH'],'state':s,'magic':g})
    record('eighteen ordered scroll-only reveal/leave states and safe entry buttons',phases)
    positions=[8.3,8.7,8.84,9.14,9.42,9.5,9.63,10.05,10.4,10.5,10.57,10.83,11.08,11.1,11.25,11.5,11.7,11.8];saved={}
    for h in positions:go(page,h);frames(page);saved[h]=state(page)
    for h in reversed(positions):go(page,h);frames(page);assert state(page)==saved[h],(h,state(page),saved[h])
    go(page,9.42);a=state(page);pic=picture(page);page.wait_for_timeout(350);assert state(page)==a and ImageChops.difference(pic,picture(page)).getbbox()is None
    record('reverse/fast jumps and paused descents reproduce exact states through the water return',{'positionsH':positions,'pausedMidDescentExact':True})
    page.locator('[data-stop=experiments]').click();settled(page,9.14);page.locator('.tour-inspector summary').click();page.locator('[data-reading-stop=C3]').click();settled(page,10.83);page.locator('.tour-inspector summary').click()
    page.locator('#tour-reference').focus();old=float(data(page)['displayH']);page.mouse.wheel(0,-180);page.wait_for_function('h=>Number(document.querySelector("#tour-host").dataset.displayH)<h',arg=old);page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
    assert page.evaluate('document.activeElement.id')=='tour-reference'
    record('native wheel and C chapter/debug stops preserve native focus',{'C3Stop':10.83,'wheelMoves':True})
    go(page,10.05);a=state(page);pic=picture(page);open_project(page);before_h=data(page)['displayH'];before_y=page.evaluate('scrollY');draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(250)
    assert page.evaluate('window.__tourProbe.draws')==draws and page.locator('canvas').count()==1
    assert page.locator('.experiment-reading').get_attribute('aria-hidden')=='true'and all(json.loads(data(page)[k])['glyph']==0 for k in ['magicFrame','filmMagicFrame','experimentMagicFrame'])
    assert page.locator('.tour-project-dialog').evaluate('e=>getComputedStyle(e,"::backdrop").backdropFilter')=='none'
    page.mouse.wheel(0,800);page.wait_for_timeout(150);assert data(page)['displayH']==before_h and page.evaluate('scrollY')==before_y
    page.keyboard.press('Escape');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');frames(page)
    assert state(page)==a and ImageChops.difference(pic,picture(page)).getbbox()is None and page.locator('[data-project-tab=live]').evaluate('e=>document.activeElement===e')
    record('live view uses one sharp actual canvas, hides glyphs, freezes story and returns exact paused state',{'sameCanvas':True,'noBlur':True,'scrollFrozen':True,'pixelsAndFocusRestored':True,'pausedDraws':draws})
    open_project(page);page.locator('[data-project-mode=native]').click();assert page.locator('canvas').get_attribute('data-render-mode')=='native'
    page.locator('.tour-project-motion').click();page.wait_for_function('Number(document.querySelector("#tour-host").dataset.sceneTime)>2.05');page.locator('.tour-project-motion').click();time=data(page)['sceneTime']
    close_project(page);settled(page,10.05);assert data(page)['motionState']=='paused'and data(page)['sceneTime']==time and page.locator('.tour-actions [data-mode=native]').get_attribute('aria-pressed')=='true'
    assert data(page)['cameraTarget']==a['cameraTarget'];page.locator('.tour-actions [data-mode=pixel]').click()
    record('explicit live mode/play choices survive exit with original station and synchronized controls',{'timeAdvanced':time,'modeKept':'native','latestPauseKept':True,'h':data(page)['displayH']})
    go(page,10.05);open_project(page,'archive');assert not page.locator('video').count();assert '固定视角动效片段'in page.locator('.tour-project-archive').inner_text()and '12秒'in page.locator('.tour-project-archive').inner_text()
    t=data(page)['sceneTime'];page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector(".tour-project-dialog video")?.currentTime>.15&&!document.querySelector(".tour-project-dialog video").paused')
    metadata=page.locator('video').evaluate('v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,loop:v.loop,inline:v.playsInline})');assert abs(metadata['duration']-12)<.1 and metadata['width']==metadata['height']==680 and not metadata['loop']and metadata['inline']
    page.locator('button[data-project-view=archive]').click();assert page.locator('video').count()==1 and not page.locator('video').evaluate('v=>v.paused')
    v=page.locator('video').evaluate('v=>v.currentTime');page.wait_for_timeout(300);assert page.locator('video').evaluate('v=>v.currentTime')>v and data(page)['sceneTime']==t
    page.locator('button[data-project-view=live]').click();assert not page.locator('video').count();page.locator('button[data-project-view=archive]').click();assert not page.locator('video').count()
    assert page.locator('dialog[open]').count()==1;page.locator('.tour-project-archive').evaluate('e=>e.scrollTop=500');close_project(page);assert not page.locator('video').count()
    open_project(page,'archive');assert page.locator('.tour-project-archive').evaluate('e=>e.scrollTop')==0;close_project(page)
    record('real version-labelled archive video decodes, advances and releases on tab change/close',metadata)
    open_project(page);page.locator('.tour-project-motion').click();page.wait_for_function('document.querySelector("#tour-host").dataset.motionState==="running"');page.locator('button[data-project-view=archive]').click();t=data(page)['sceneTime'];page.wait_for_timeout(300);assert data(page)['sceneTime']==t
    page.locator('button[data-project-view=live]').click();page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)',arg=t);page.locator('.tour-project-motion').click();close_project(page)
    record('archive suspension preserves manual play intent and only live view resumes it',{'archiveTimeFrozen':True,'liveResumesChoice':True})
    resized=[]
    for w,h in [(1366,768),(390,844),(1440,900)]:
        resize(page,w,h)
        for key,at,y in STOPS:
            go(page,at);frames(page);r=validate(page);page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'{args.engine}-{w}-{key}.png'));resized.append({'viewport':[w,h],'station':key,'layout':r})
        go(page,10.05);prior=float(data(page)['displayH']);open_project(page);buttons=project_controls(page);assert all(x['inside']and x['height']>=44 and x['width']>=44 for x in buttons),buttons
        page.screenshot(path=str(OUT/f'{args.engine}-{w}-live.png'));page.locator('button[data-project-view=archive]').click();page.screenshot(path=str(OUT/f'{args.engine}-{w}-archive.png'));close_project(page);settled(page,prior)
    go(page,10.05);prior=float(data(page)['displayH']);open_project(page);resize(page,1366,768);close_project(page);settled(page,prior);validate(page);resize(page,1440,900)
    record('three target layouts, live controls and normalized return after modal resizing pass',resized)
    for h in [1.74,3.34,4.95,5.95,6.84,7.64,9.14,10.83,10.05]:go(page,h)
    # Warm both project tabs and the decoder before the resource-stability series.
    open_project(page,'archive');page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.readyState>=1');close_project(page);frames(page)
    before=json.loads(data(page)['rendererStats']);nodes=page.locator('*').count();cycles=10
    for i in range(cycles):
        open_project(page);page.locator('button[data-project-view=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.readyState>=1');close_project(page);settled(page,10.05)
    frames(page);after=json.loads(data(page)['rendererStats']);assert all(before[k]==after[k]for k in ['geometries','textures','programs'])
    assert page.locator('*').count()==nodes and page.locator('canvas').count()==1 and page.locator('dialog[open]').count()==0 and not page.locator('video').count()
    draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(400);assert page.evaluate('window.__tourProbe.draws')==draws
    # A close/reopen within one task exercises stale close and focus callbacks.
    page.evaluate('()=>{document.querySelector("[data-project-tab=live]").click();document.querySelector(".tour-project-close").click();document.querySelector("[data-project-tab=archive]").click()}');page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]');assert data(page)['overlayState']=='open';close_project(page)
    record('ten project/media cycles and rapid reopen keep DOM/GPU stable and paused drawing stopped',{'cycles':cycles,'before':before,'after':after,'nodes':nodes,'singleCanvas':True,'activeVideos':0,'staleCloseSafe':True})
    kwargs={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True,'reduced_motion':'reduce'}
    if args.engine!='firefox':kwargs['is_mobile']=True
    mobile=b.new_context(**kwargs);mobile.add_init_script(PROBE);m=mobile.new_page();watch(m);m.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');m.wait_for_selector('#tour-host[data-render-state="ready"]');mobile_views=[]
    for key,at,y in STOPS:
        go(m,at);frames(m);r=validate(m);assert r['rect']['bottom']<=r['nav']['top']-15 and json.loads(data(m)['experimentMagicFrame'])['dustVisible']==0
        m.screenshot(path=str(OUT/f'{args.engine}-mobile-{key}.png'));mobile_views.append({'station':key,'layout':r,'contrast':contrast(m,'mobile-'+key)})
    go(m,10.05);m.locator('[data-project-tab=live]').tap();frames(m);assert data(m)['motionState']=='paused';m.locator('.tour-project-close').tap();settled(m,10.05)
    if args.engine=='chromium':
        session=mobile.new_cdp_session(m);old=float(data(m)['displayH']);session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':350}]})
        for y in [310,270,230,190]:session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]});m.wait_for_timeout(35)
        session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(350);assert float(data(m)['displayH'])>old
    mobile.close();record('portrait touch, reduced motion, full content and actual contrast pass',{'simulatedPhone':True,'nativeTouchDrag':args.engine=='chromium','stations':mobile_views})
    known=[x for x in issues if args.engine=='firefox'and any(s in x['text']for s in ['Depth texture comparison requests','WebGL context was lost.','This site appears to use a scroll-linked positioning effect.'])];unexpected=[x for x in issues if x not in known];assert not unexpected,unexpected
    record('normal browser diagnostics contain no unidentified errors or HTTP failures',{'knownFirefox':known,'unexpected':unexpected})
    save(f'verification-{args.engine}.json',{'engine':args.engine,'version':b.version,'checks':checks,'issues':issues,'passed':True,'environment':'Linux software graphics; simulated mobile; GTK WebKit is not Apple Safari; no physical FPS/trackpad claim'});b.close()
