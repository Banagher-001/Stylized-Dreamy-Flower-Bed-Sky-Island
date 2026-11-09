"""Diagnostic-only response instrumentation, separate from normal app proofs.
The frozen production files remain unchanged. Records actual bird presentation,
DOM-read and GL-submit costs during a matched native-mode guide segment.
"""
import ast,hashlib,json
from playwright.sync_api import sync_playwright
from step6_common import *
build=json.loads((OUT/'build-verification.json').read_text());errors=[];runs=[]
tree=ast.parse((ROOT/'tests/garden-enhancement/step6_performance.py').read_text())
hook=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='HOOK'for t in n.targets))
script=next((ROOT/'dist/assets').glob('startTourPrototype-*.js'));original=script.read_text()
start='if(K.update(r),K.birds){';end='ct&&(G.dataset.birdState=JSON.stringify(K.birds.snapshot()))}let i='
assert original.count(start)==original.count(end)==1
modified=original.replace(start,start+'const __birdStart=performance.now();').replace(end,'ct&&(G.dataset.birdState=JSON.stringify(K.birds.snapshot()));window.__birdDiagnostic.presentationMs+=performance.now()-__birdStart;window.__birdDiagnostic.visible=K.birds.snapshot().visible}let i=')
DIAGNOSTIC=r'''(()=>{
 window.__birdDiagnostic={presentationMs:0,visible:0,rectMs:0,rectCalls:0,styleMs:0,styleCalls:0,glMs:0,glCalls:0,rows:[]};
 const box=Element.prototype.getBoundingClientRect;Element.prototype.getBoundingClientRect=function(...a){let p=window.__birdDiagnostic,t=performance.now(),r=box.apply(this,a);p.rectMs+=performance.now()-t;p.rectCalls++;return r};
 const style=getComputedStyle;window.getComputedStyle=function(...a){let p=window.__birdDiagnostic,t=performance.now(),r=style.apply(this,a);p.styleMs+=performance.now()-t;p.styleCalls++;return r};
 for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){const draw=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...a){let p=window.__birdDiagnostic,t=performance.now(),r=draw.apply(this,a);p.glMs+=performance.now()-t;p.glCalls++;return r}}
 const raw=requestAnimationFrame.bind(window);window.requestAnimationFrame=callback=>raw(t=>{let p=window.__birdDiagnostic;p.presentationMs=p.rectMs=p.rectCalls=p.styleMs=p.styleCalls=p.glMs=p.glCalls=0;let begin=performance.now();callback(t);let d=document.querySelector('#tour-host')?.dataset;if(p.glCalls&&d?.guidePhase==='moving')p.rows.push({h:Number(d.displayH),costMs:performance.now()-begin,presentationMs:p.presentationMs,visible:p.visible,rectMs:p.rectMs,rectCalls:p.rectCalls,styleMs:p.styleMs,styleCalls:p.styleCalls,glMs:p.glMs,glCalls:p.glCalls})});
})()'''
def stats(values):
    s=sorted(values);return {'count':len(s),'mean':sum(s)/len(s),'p50':s[int((len(s)-1)*.5)],'p95':s[int((len(s)-1)*.95)],'max':max(s)}
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900})
    context.add_init_script(probe);context.add_init_script(DIAGNOSTIC);context.add_init_script(hook)
    for phase,port in [('before',4180),('after',4181)]:
        page=context.new_page();watch(page,errors)
        if phase=='after':page.route('**/'+script.name,lambda route:route.fulfill(status=200,content_type='text/javascript',body=modified))
        load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,h in VIEWS:visit(page,h)
        guide_start(page,3.8,reading=False);page.wait_for_function('window.__cloudPerf.renderer!==null');guide_stop(page)
        visit(page,3.8);page.evaluate('window.__birdDiagnostic.rows=[];window.__cloudPerf.control={base:0,index:0,count:240,started:false,done:false,frames:[]}')
        page.locator('#tour-motion').click();assert data(page)['motionState']=='running';guide_start(page,reading=False)
        page.wait_for_function('window.__cloudPerf.control.done',timeout=120000,polling=100)
        guide_stop(page);pause(page)
        rows=page.evaluate('window.__birdDiagnostic.rows').copy();selected=[r for r in rows if 3.8<r['h']<4.75]
        report={'phase':phase,'rows':rows,'stats':{k:stats([r[k]for r in selected])for k in ['costMs','presentationMs','rectMs','rectCalls','styleMs','styleCalls','glMs','glCalls']},'visibleCounts':sorted(set(r['visible']for r in selected))}
        runs.append(report);print(phase,json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True);page.close()
    assert not errors,errors
    save(OUT,'performance-cost-isolation.json',{'passed':True,'candidateId':build['candidateId'],'diagnosticOnly':True,'instrumentedScript':script.name,'originalSha256':hashlib.sha256(original.encode()).hexdigest(),'responseInstrumentationSha256':hashlib.sha256(modified.encode()).hexdigest(),'method':'response-only passive timings around original bird presentation; actual original guide/animated environment with matching240 motion timestamps; additional DOM/GL timing wrappers; instrumentation overhead included; not the unmodified performance acceptance or video evidence','runs':runs,'errors':errors})
    context.close();browser.close()
