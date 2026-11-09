"""Real normal-layout projection, full-envelope safety, motion and depth pixels.
birds=inspect only reports state; it does not expose extra UI or change time.
Explicit shader color/depth probes are isolated from normal visual screenshots.
"""
import json
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright
from step6_common import *
build=json.loads((OUT/'build-verification.json').read_text());checks=[];errors=[]
def state(page):return json.loads(data(page)['birdState'])
def safety(page):
    snapshot=state(page)
    rects=page.evaluate('''()=>[...document.querySelectorAll('.tour-header,.tour-footer,.tour-stops,.tour-heading,.pillar-reading,.film-reading,.experiment-reading')].filter(e=>!e.hidden&&getComputedStyle(e).visibility==='visible'&&Number(getComputedStyle(e).opacity)>.000001).map(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,class:e.className}})''')
    margin=14 if page.viewport_size['width']<600 else 20
    host=data(page);height=page.locator('#tour-host').bounding_box()['height']
    radius=.55*height/float(host['viewHeight'])
    for family,key in [('.pillar-reading','readingStation'),('.film-reading','filmStation'),('.experiment-reading','experimentStation')]:
        if not host.get(key):continue
        anchor=page.locator(family).evaluate('e=>({x:Number(e.dataset.anchorX),y:Number(e.dataset.anchorY)})')
        rects.append({'left':anchor['x']-radius,'right':anchor['x']+radius,'top':anchor['y']-radius,'bottom':anchor['y']+radius,'class':'actual projected GPU inscription safety area'})
    for p in snapshot['poses']:
        s=p['screen']
        if s['alpha']<.015:continue
        for r in rects:
            gap=max(r['left']-s['x'],s['x']-r['right'],r['top']-s['y'],s['y']-r['bottom'])-s['radius']-margin
            assert gap>-.01,(snapshot,r,gap)
    return snapshot
def record(name,evidence):checks.append({'name':name,'passed':True,'evidence':evidence});print('birds',name,flush=True)

DEPTH=r'''(()=>{
 const mode=new URLSearchParams(location.search).get('__birdDepth');window.__birdProbeShaders=0;
 for(const type of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){if(!type)continue;const p=type.prototype,source=p.shaderSource;
 p.shaderSource=function(shader,text){
  if(text.includes('vBirdAlpha')){window.__birdProbeShaders++;
   if(this.getShaderParameter(shader,this.SHADER_TYPE)===this.FRAGMENT_SHADER)text=text.replace(/}\s*$/,'gl_FragColor = vec4(1.0, 0.0, 1.0, diffuseColor.a);\n}');
   else if(mode==='far')text=text.replace(/}\s*$/,'gl_Position.z = .99 * gl_Position.w;\n}');
   else if(mode==='front')text=text.replace(/}\s*$/,'gl_Position.z = -.99 * gl_Position.w;\n}');
  }return source.call(this,shader,text);
 };
 }
})()'''
with sync_playwright()as p:
    browser=launch(p)
    for w,h,dpr,times in [(1440,900,1,[2,8,18,28,44,60]),(1366,768,1,[2,18,44]),(390,844,2,[2,18,44])]:
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr)
        context.add_init_script(probe);page=context.new_page();watch(page,errors);rows=[]
        for t in times:
            load(page,f'http://127.0.0.1:4181/?waterTime={t}&birds=inspect')
            for key,hpos in VIEWS:
                visit(page,hpos);snapshot=safety(page);rows.append({'time':t,'pose':key,'H':hpos,'state':snapshot})
            if t==2:
                visit(page,0);page.screenshot(path=str(OUT/f'birds-{w}-opening.png'))
        record(f'actual normal UI full bird envelopes avoid all reading/controls at{w}',{'viewport':[w,h],'DPR':dpr,'samples':rows})
        context.close()
    context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(probe)
    page=context.new_page();watch(page,errors);load(page,'http://127.0.0.1:4181/?waterTime=2&birds=inspect')
    start=safety(page);playing(page);page.wait_for_function('Number(document.querySelector("#tour-host").dataset.sceneTime)>7',timeout=30000)
    pause(page);held=safety(page);assert any(a['position']!=b['position']for a,b in zip(start['poses'],held['poses']))
    frozen=pure_canvas(page);quiet=still(page);page.wait_for_timeout(600);assert equal(frozen,pure_canvas(page))and state(page)==held
    visit(page,2.54);turn=safety(page);assert [r['position']for r in turn['poses']]==[r['position']for r in held['poses']]
    visit(page,0);assert equal(frozen,pure_canvas(page))and state(page)==held
    record('real play and pause retain wing tips, route time and exact world pixels after reverse camera roundtrip',{'start':start,'held':held,'pausedZeroDraw':quiet,'cameraRoundtripExact':True})
    visit(page,10.05);page.locator('[data-project-tab=live]').click();frames(page);live=state(page)
    r=page.locator('.tour-project-live-space').bounding_box();assert r
    for bird in live['poses']:
        s=bird['screen']
        if s['alpha']>=.015:assert r['x']+s['radius']<s['x']<r['x']+r['width']-s['radius']and r['y']+s['radius']<s['y']<r['y']+r['height']-s['radius']
    page.screenshot(path=str(OUT/'birds-live-pane.png'));page.locator('.tour-project-close').click();frames(page)
    record('live pane uses original canvas with projected birds confined to its real bounds',{'pane':r,'state':live,'canvasCount':page.locator('canvas').count()})
    context.close()
    # Deliberate test-only shader probes; original geometry and projection stay.
    context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(probe);context.add_init_script(DEPTH)
    page=context.new_page();watch(page,errors);depth=[]
    for mode in ['normal','front','far']:
        load(page,f'http://127.0.0.1:4181/?waterTime=2&render=native&__birdDepth={mode}');raw=pure_canvas(page);name=f'diagnostic-bird-depth-{mode}.png';(OUT/name).write_bytes(raw)
        count=sum(1 for r,g,b in Image.open(BytesIO(raw)).convert('RGB').getdata()if r>240 and g<15 and b>240)
        assert page.evaluate('window.__birdProbeShaders')>=2;depth.append({'mode':mode,'markerPixels':count,'file':name})
    assert depth[0]['markerPixels']>20 and depth[1]['markerPixels']>=depth[0]['markerPixels']and depth[2]['markerPixels']==0,depth
    record('actual GL depth test occludes original projected bird geometry behind the courtyard',{'method':'test-only magenta output; normal original depth, forced front and forced far clip-depth; XY/geometry/alpha unchanged; not normal visual or motion footage','samples':depth})
    context.close();assert not errors,errors
    save(OUT,'projection-motion-and-depth.json',{'passed':True,'candidateId':build['candidateId'],'browser':browser.version,'checks':checks,'errors':errors,'physicalDevice':False});browser.close()
print('PASS actual bird projection, frozen pose, live pane and depth pixels',flush=True)
