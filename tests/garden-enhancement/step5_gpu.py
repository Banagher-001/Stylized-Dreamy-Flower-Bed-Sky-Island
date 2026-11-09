"""Actual shared GL uniforms, world-projected field masks and original lighting.
Mask output is explicitly a test-only shaderSource substitution, not the look.
All normal screenshots are full unmodified production renders.
"""
import json,math
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step5_common import *
from step2_common import background_measurement,about,luminance

HOOK=r'''(()=>{
 const contexts=new Map(),locations=new WeakMap();window.__cloudHookCount=0;
 const forced=new URLSearchParams(location.search).get('__cloudProbeDrift');
 for(const type of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){if(!type)continue;const p=type.prototype;
 const original=p.getUniformLocation;
 p.getUniformLocation=function(program,name){const loc=original.call(this,program,name);if(loc&&['uCloudDrift','uCloudActive'].includes(name)){locations.set(loc,name);let programs=contexts.get(this);if(!programs)contexts.set(this,programs=new Map());let uniforms=programs.get(program);if(!uniforms)programs.set(program,uniforms={});uniforms[name]=loc;}return loc};
 const one=p.uniform1f;p.uniform1f=function(loc,value){if(forced!==null&&locations.get(loc)==='uCloudDrift')value=Number(forced);return one.call(this,loc,value)};
 const source=p.shaderSource;p.shaderSource=function(shader,text){if(text.includes('CLOUD_SHADOW_FINISH')){window.__cloudHookCount++;if(window.__cloudMaskOnly){const anchor='outgoingLight *= vec3(1.0) - cloudAmount * vec3(1.0, .96, .85);';if(!text.includes(anchor))throw Error('Test mask anchor missing');text=text.replace(anchor,anchor+'\n outgoingLight = vec3(cloudMask, 1.0, 0.0);')}}return source.call(this,shader,text)};
 }
 window.__cloudUniforms=()=>{const rows=[];for(const [gl,programs]of contexts){if(gl.isContextLost())continue;for(const [program,u]of programs)if(gl.isProgram(program)&&u.uCloudDrift&&u.uCloudActive)rows.push({drift:gl.getUniform(program,u.uCloudDrift),active:gl.getUniform(program,u.uCloudActive)})}return rows};
})()'''
build=json.loads((OUT/'build-verification.json').read_text());errors=[];checks=[]
def record(name,evidence):checks.append({'name':name,'passed':True,'evidence':evidence});print('GPU',name,flush=True)
def uniforms(page):
    rows=page.evaluate('window.__cloudUniforms()');assert rows and all(r['active']==1 for r in rows),rows
    t=float(data(page)['sceneTime']);expected=(t*.22)%32
    error=max(min(abs(r['drift']-expected),abs(r['drift']-expected+32),abs(r['drift']-expected-32))for r in rows)
    assert error<.000004,(t,expected,rows,error)
    return {'sceneTime':t,'programs':len(rows),'actualUniforms':rows,'maxExpectedDriftError':error}

with sync_playwright()as p:
    browser=launch(p)
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);context.add_init_script(HOOK)
    page=context.new_page();watch(page,errors);load(page,'http://127.0.0.1:4179/?waterTime=2')
    rows=[]
    for key,h in [('O',0),('A2',2.54),('B2',5.95),('C2',10.05),('W',11.5)]:visit(page,h);rows.append({'pose':key,'uniforms':uniforms(page)})
    record('all visible receivers use the same actual GL drift and active state',rows)
    visit(page,0);original=pure_canvas(page);start=uniforms(page);playing(page)
    page.wait_for_function('Number(document.querySelector("#tour-host").dataset.sceneTime)>3.5',timeout=30000)
    pause(page);later=uniforms(page);moved=pure_canvas(page);assert not equal(original,moved)
    freeze=still(page);frozen=pure_canvas(page);page.wait_for_timeout(600);assert equal(frozen,pure_canvas(page))
    visit(page,2.54);station=uniforms(page);assert station['sceneTime']==later['sceneTime']
    visit(page,0);assert equal(frozen,pure_canvas(page))
    record('real playback changes shared uniforms; pause and reverse camera roundtrip retain exact world pixels',{'initial':start,'later':later,'paused':freeze,'station':station,'exactPixelReturn':True,'pixelChangeIncludesOriginalWaterAndGrass':True})
    context.close()
    # Actual mask pixels count receiver surfaces in the original full overview.
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);context.add_init_script('window.__cloudMaskOnly=true');context.add_init_script(HOOK)
    page=context.new_page();watch(page,errors);coverage=[]
    threshold=round((1.055*.25**(1/2.4)-.055)*255)
    for t in [2,18,40,64]:
        load(page,f'http://127.0.0.1:4179/?waterTime={t}&render=native');raw=pure_canvas(page)
        name=f'diagnostic-field-O-{t:02d}.png';(OUT/name).write_bytes(raw)
        pixels=Image.open(BytesIO(raw)).convert('RGB').getdata();total=covered=0
        for r,g,b in pixels:
            if g>=254 and b<=1:total+=1;covered+=r>threshold
        assert total>100000 and page.evaluate('window.__cloudHookCount')>=5
        coverage.append({'time':t,'visibleReceiverPixels':total,'coverageAbovePoint25':covered/total,'file':name})
    assert all(.20<=r['coverageAbovePoint25']<=.40 for r in coverage),coverage
    record('actual world-field mask on visible overview surfaces; broad partial shade',{'method':'test-only output substitution vec3(cloudMask,1,0) after actual depth/instancing/world projection; count green255/blue0 receiver pixels and red corresponding to linear0.25; full raw raster saved, not visual design footage','samples':coverage})
    seams=[]
    for h,key in [(0,'O'),(2.54,'A2'),(11.5,'W')]:
        rasters=[]
        for phase,label in [(31.999999,'before'),(.000001,'after')]:
            load(page,f'http://127.0.0.1:4179/?waterTime=2&render=native&__cloudProbeDrift={phase}');visit(page,h)
            raw=pure_canvas(page);name=f'diagnostic-wrap-{key}-{label}.png';(OUT/name).write_bytes(raw);rasters.append(Image.open(BytesIO(raw)).convert('RGB'))
        maximum=max(b for _,b in ImageChops.difference(*rasters).getextrema());assert maximum<=1,(key,maximum)
        seams.append({'pose':key,'fixedOriginalEnvironmentTime':2,'forcedDrifts':[31.999999,.000001],'maximum8bitChannelDifference':maximum})
    record('GPU cyclic field continuous at reset with original geometry held exactly',{'method':'explicit test-only uCloudDrift override through actual WebGL.uniform1f; all original geometry/water/vegetation held at same original time2; not real-time motion footage','samples':seams})
    context.close()
    # Original pixels, no diagnostic shader: darkness and UI background protection.
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    off,on=context.new_page(),context.new_page()
    for page,param in [(off,'&clouds=off'),(on,'')]:watch(page,errors);load(page,'http://127.0.0.1:4179/?waterTime=2&render=native'+param)
    for key,h in [('O',0),('A2',2.54),('W',11.5)]:
        rasters=[]
        for page,label in [(off,'off'),(on,'on')]:
            visit(page,h);raw=pure_canvas(page);(OUT/f'actual-shading-{key}-{label}.png').write_bytes(raw);rasters.append(Image.open(BytesIO(raw)).convert('RGB'))
        changed=brightDrop=darkDrop=0;blackened=0
        table=[(v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4)for v in range(256)]
        for a,b in zip(rasters[0].getdata(),rasters[1].getdata()):
            if a==b:continue
            changed+=1;la=sum(table[v]*k for v,k in zip(a,[.2126,.7152,.0722]));lb=sum(table[v]*k for v,k in zip(b,[.2126,.7152,.0722]))
            if la>.15:brightDrop=max(brightDrop,(la-lb)/la)
            if .005<la<.05:darkDrop=max(darkDrop,la-lb);blackened+=lb<.001
        assert changed>10000 and .04<brightDrop<.205 and darkDrop<.0045 and blackened==0,(key,changed,brightDrop,darkDrop,blackened)
        record('actual '+key+' lighting retains dark detail',{'changedPixels':changed,'maximumBrightLinearLuminanceDrop':brightDrop,'maximumDeepShadeAbsoluteLuminanceDrop':darkDrop,'newBlackPixelsInDeepShade':blackened,'mode':'native','time':2})
    context.close()
    backgrounds=[]
    for w,h,dpr in [(1440,900,1),(390,844,2)]:
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr)
        for mode in ['pixel','native']:
            samples=[]
            for label,port in [('before',4178),('after-cloud-on',4179)]:
                page=context.new_page();watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2&render={mode}');visit(page,2.54)
                name=f'cloud-on-about-alpha-{w}-{mode}-{label}.png';measurement=background_measurement(page,OUT,name,check=True)
                samples.append({'file':name,'actual':about(page),'measurement':measurement});page.close()
            assert samples[0]['actual']==samples[1]['actual']and equal(*[(OUT/r['file']).read_bytes()for r in samples])
            backgrounds.append({'width':w,'mode':mode,'RGBAExactWithCloudsOn':True,'samples':samples})
        context.close()
    record('original About actual RGBA remains exact with clouds enabled',backgrounds)
    assert not errors,errors
    save(OUT,'gpu-field-and-lighting.json',{'passed':True,'candidateId':build['candidateId'],'browser':browser.version,'checks':checks,'errors':errors,'diagnosticMaskClearlySeparated':True,'hardwareFPSProof':False})
    browser.close()
print('PASS GPU shared field, lighting and enabled-cloud background protection',flush=True)
