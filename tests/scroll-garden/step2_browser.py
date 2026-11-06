"""Step 2 integration checks. Optional deps: tests/final/requirements.txt."""
from pathlib import Path
from io import BytesIO
import argparse
import json
import os
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/scroll-garden-step-2'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--url', default='http://127.0.0.1:4173')
args = parser.parse_args()
checks, issues = [], []

PROBE = '''(()=>{window.__tourProbe={draws:0,lastScroll:0,settles:[]};
for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){
const original=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...a){window.__tourProbe.draws++;return original.apply(this,a);};}
window.addEventListener('scroll',()=>window.__tourProbe.lastScroll=performance.now(),{passive:true});
const attach=()=>{const h=document.querySelector('#tour-host');if(!h)return false;
let previous='';new MutationObserver(()=>{const state=h.dataset.cameraState;if(state==='settled'&&previous==='moving'&&window.__tourProbe.lastScroll)window.__tourProbe.settles.push(performance.now()-window.__tourProbe.lastScroll);previous=state;}).observe(h,{attributes:true,attributeFilter:['data-camera-state']});return true;};
if(new URLSearchParams(location.search).get('tour')==='prototype'&&!attach()){const discovery=new MutationObserver(()=>{if(attach())discovery.disconnect();});discovery.observe(document,{childList:true,subtree:true});}
})()'''


def record(name, evidence):
    checks.append({'check': name, 'passed': True, 'evidence': evidence})
    print(args.engine + ': ' + name, flush=True)


def ready(page):
    page.wait_for_selector('#tour-host[data-render-state="ready"]')


def data(page):
    return page.locator('#tour-host').evaluate('e=>({...e.dataset})')


def settled(page, h):
    page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003;}', arg=h)


def go(page, h):
    page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})', h)
    settled(page, h)


def image(page):
    # The element clip includes floating controls. Normalize pointer hover state.
    page.mouse.move(10, page.viewport_size['height'] / 2)
    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')


def watch(page):
    page.on('pageerror', lambda error: issues.append({'type': 'exception', 'text': str(error)}))
    page.on('console', lambda message: issues.append({'type': message.type, 'text': message.text}) if message.type in ['warning', 'error'] else None)
    page.on('response', lambda response: issues.append({'type': 'http', 'text': f'{response.status} {response.url}'}) if response.status >= 400 else None)


with sync_playwright() as p:
    options = {'headless': args.engine == 'chromium'}
    if args.engine == 'chromium':
        options.update(executable_path=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'), args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    if args.engine == 'firefox':
        options['firefox_user_prefs'] = {'webgl.force-enabled': True}
    if args.engine == 'webkit' and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):
        options['executable_path'] = os.environ['COURTYARD_WEBKIT_EXECUTABLE']
    browser = getattr(p, args.engine).launch(**options)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    context.add_init_script(PROBE)
    page = context.new_page()
    watch(page)
    page.goto(args.url + '/?tour=prototype&waterTime=2', wait_until='networkidle')
    ready(page)
    assert page.locator('canvas').count() == 1
    assert page.locator('.work-card').count() == 0
    assert page.locator('#tour-scroll-space').evaluate('e=>e.offsetHeight') > 12 * 900
    initial = image(page)
    assert len(initial.getcolors(1000000)) > 32
    record('isolated production prototype has one visible scene and native document scroll', {'canvasCount': 1, 'scene': data(page)})

    page.mouse.wheel(0, 900)
    page.wait_for_function('scrollY>100')
    page.wait_for_function('()=>{const d=document.querySelector("#tour-host").dataset;const h=scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003;}')
    wheel_h=float(data(page)['displayH'])
    assert wheel_h>0
    assert data(page)['stage'] == 'T01'
    page.mouse.wheel(0, -900)
    page.wait_for_function('h=>Number(document.querySelector("#tour-host").dataset.displayH)<h',arg=wheel_h)
    page.wait_for_function('()=>{const d=document.querySelector("#tour-host").dataset;const h=scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003;}')
    page.keyboard.press('Home')
    settled(page,0)
    page.keyboard.press('End')
    settled(page, 12.3)
    page.keyboard.press('Home')
    settled(page, 0)
    record('real browser wheel and Home/End control the same progress', {'requestedWheelDelta':900,'actualWheelProgressH':wheel_h,'wheelReversed': True, 'homeH': data(page)['displayH'],'mapping':'actual document scroll, not raw wheel delta'})

    keyframes = []
    for key, h, stage in [('about',1.74,'A1'),('films',4.95,'B1'),('experiments',9.14,'C1'),('water',11.5,'T3W'),('overview',0,'S00')]:
        page.locator(f'[data-stop="{key}"]').click()
        settled(page, h)
        d = data(page)
        assert d['stage'] == stage
        assert d['sceneTime'] == '2.000000'
        page.screenshot(path=str(OUT / f'{args.engine}-{key}.png'))
        keyframes.append({'key': key, 'h': float(d['displayH']), 'position': json.loads(d['cameraPosition']), 'target': json.loads(d['cameraTarget']), 'viewHeight': float(d['viewHeight'])})
    record('all five key views work with environment paused', keyframes)

    poses = {}
    for h in [.9,3.92,8.32,11.3]:
        go(page,h)
        d=data(page)
        poses[h]={k:d[k]for k in ['cameraPosition','cameraTarget','viewHeight']}
        page.screenshot(path=str(OUT / f'{args.engine}-travel-{str(h).replace(".","-")}.png'))
    go(page,12.3)
    for h in reversed(list(poses)):
        go(page,h)
        assert poses[h]=={k:data(page)[k]for k in poses[h]}
    record('fast jumps and reverse travel restore identical settled camera parameters', {'midpointsH':list(poses),'exact':True})

    go(page,1.74)
    pixel=image(page)
    page.get_by_role('button',name='正常画面',exact=True).click()
    assert data(page)['viewHeight']=='3.6000000'
    assert ImageChops.difference(pixel,image(page)).getbbox() is not None
    page.get_by_role('button',name='像素预览',exact=True).click()
    assert ImageChops.difference(pixel,image(page)).getbbox() is None
    record('near-view mode switching changes actual picture without resetting zoom', {'returnedPixelsExact':True})

    before=float(data(page)['displayH'])
    page.set_viewport_size({'width':1366,'height':768})
    settled(page,before)
    assert data(page)['viewHeight']=='3.6000000'
    assert page.locator('#tour-host').evaluate('e=>Math.abs(e.getBoundingClientRect().bottom-document.querySelector(".tour-footer").getBoundingClientRect().top)<2')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.set_viewport_size({'width':1440,'height':900})
    settled(page,before)
    record('resize preserves chapter progress and current view height, controls do not cover the canvas', {'beforeH':before,'afterH':float(data(page)['displayH'])})

    reference=image(page)
    page.evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()')
    page.wait_for_selector('#tour-host[data-render-state="context-lost"]')
    assert page.locator('[data-stop]:disabled').count()==5
    page.evaluate('window.__loss.restoreContext()')
    ready(page)
    assert ImageChops.difference(reference,image(page)).getbbox() is None
    record('real context restore keeps the paused camera pose and visible image', {'restoredPixelsExact':True})

    for h in [1.74,4.95,9.14,11.5,0]:go(page,h)
    page.wait_for_timeout(250)
    before_stats=json.loads(data(page)['rendererStats'])
    cycles=10 if args.engine=='chromium' else 2
    for _ in range(cycles):
        for h in [1.74,4.95,9.14,11.5,0]:go(page,h)
    page.wait_for_timeout(250)
    after_stats=json.loads(data(page)['rendererStats'])
    for k in ['geometries','textures','programs']:assert before_stats[k]==after_stats[k],(before_stats,after_stats)
    assert before_stats['pixel']['allocations']==after_stats['pixel']['allocations']
    before_draw=page.evaluate('window.__tourProbe.draws')
    page.wait_for_timeout(700)
    assert page.evaluate('window.__tourProbe.draws')==before_draw
    record('repeated tours retain GPU resource counts and settled pause stops drawing', {'cycles':cycles,'locationsPerCycle':5,'before':before_stats,'after':after_stats,'pausedDrawCount':before_draw})

    page.get_by_role('button',name='播放动效',exact=True).click()
    page.wait_for_timeout(180)
    a=float(data(page)['sceneTime'])
    go(page,4.95)
    page.wait_for_timeout(180)
    assert float(data(page)['sceneTime'])>a
    page.get_by_role('button',name='暂停动效',exact=True).click()
    record('environment playback and scroll camera remain independent', {'timeAdvancesWhileTouring':True})

    kwargs={'viewport':{'width':390,'height':844},'device_scale_factor':2,'has_touch':True,'reduced_motion':'reduce'}
    if args.engine!='firefox':kwargs['is_mobile']=True
    mobile=browser.new_context(**kwargs)
    m=mobile.new_page()
    watch(m)
    m.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle')
    ready(m)
    m.locator('[data-stop="about"]').tap()
    settled(m,1.74)
    assert not m.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert m.locator('[data-stop],.mode-controls button,#tour-motion').evaluate_all('es=>es.every(e=>{let r=e.getBoundingClientRect();return r.width>=44&&r.height>=44;})')
    m.screenshot(path=str(OUT/f'{args.engine}-mobile.png'))
    if args.engine=='chromium':
        session=mobile.new_cdp_session(m)
        old=float(data(m)['displayH'])
        session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':220,'y':500}]})
        for y in [460,420,380,340,300]:
            session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':220,'y':y}]})
            m.wait_for_timeout(35)
        session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        m.wait_for_timeout(500)
        assert float(data(m)['displayH'])>old
    mobile.close()
    record('basic mobile touch navigation and reduced-motion camera work', {'viewport':[390,844],'simulatedPhone':True,'nativeTouchDragTested':args.engine=='chromium'})

    settle_samples=page.evaluate('window.__tourProbe.settles')
    assert settle_samples, 'No camera settle events were actually observed'
    record('settle latency recorded from browser-observed frame state', {'samples':len(settle_samples),'maxMs':max(settle_samples,default=0),'p95Ms':sorted(settle_samples)[int((len(settle_samples)-1)*.95)] if settle_samples else None,'targetMs':200,'environment':'software rendering; observer includes frame work, not physical input-to-display timing'})

    if args.engine=='chromium':
        page.set_viewport_size({'width':1440,'height':1000})
        for mode in ['pixel','native']:
            page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle')
            page.wait_for_selector('#scene-host[data-render-state="ready"]')
            actual=image(page)
            baseline=Image.open(OUT/f'reference-before-{mode}.png').convert('RGB')
            assert ImageChops.difference(baseline,actual).getbbox() is None
            page.locator('canvas').screenshot(path=str(OUT/f'reference-after-{mode}.png'))
        assert page.locator('.work-card').count()==3
        record('default reference page retains both exact scene images and its portfolio', {'modes':['pixel','native'],'pixelsExact':True})

    known=[item for item in issues if args.engine=='firefox'and('Depth texture comparison requests'in item['text']or'WebGL context was lost.'in item['text'])]
    unexpected=[item for item in issues if item not in known]
    assert not unexpected,unexpected
    record('all diagnostics retained with no unidentified errors or warnings',{'knownFirefoxDiagnostics':len(known),'unexpected':unexpected})
    result={'engine':args.engine,'version':browser.version,'environment':'Linux cloud software renderer; not real phone or hardware FPS acceptance','checks':checks,'issues':issues,'passed':True}
    (OUT/f'verification-{args.engine}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    browser.close()
