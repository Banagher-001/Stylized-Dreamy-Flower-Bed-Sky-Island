"""Serial matched production performance: original wheel30 and true guide move
versus external replay of its identical native positions/timestamps in Step3.
No other browser/screenshot/video may run during this command.
"""
import json,math
from playwright.sync_api import sync_playwright
from step4_common import *

HOOK=r'''(()=>{
const original=requestAnimationFrame.bind(window);
window.__guidePerf={capture:false,frames:[],replay:null};
const sample=(nativeTimestamp,usedTimestamp,cost,callbackMs)=>{
 const d=document.querySelector('#tour-host').dataset;
 return{nativeTimestamp,usedTimestamp,costMs:cost,callbackMs,y:scrollY,h:Number(d.displayH),target:Number(d.targetH),position:d.cameraPosition,lookAt:d.cameraTarget,height:Number(d.viewHeight),time:Number(d.sceneTime),calls:window.__tourProbe.draws};
};
window.requestAnimationFrame=callback=>original(nativeTimestamp=>{
 const p=window.__guidePerf;let entry=null,used=nativeTimestamp;
 const begin=performance.now();
 if(p.replay?.active&&p.replay.index<p.replay.samples.length){
  entry=p.replay.samples[p.replay.index];used=entry.usedTimestamp;
  scrollTo({top:entry.y,behavior:'instant'});
  // Test-only replay notification: invokes the unchanged original scroll reader
  // before its renderer. This is NOT claimed as a trusted-user input latency test.
  dispatchEvent(new Event('scroll'));
 }
 const before=window.__tourProbe.draws,appStart=performance.now();
 callback(used);
 const end=performance.now();
 if(window.__tourProbe.draws>before){
  const d=document.querySelector('#tour-host').dataset;
  if(p.capture&&d.guidePhase==='moving'&&d.guideStation==='B1')p.frames.push(sample(nativeTimestamp,used,end-begin,end-appStart));
  if(entry&&p.replay.active){p.replay.frames.push(sample(nativeTimestamp,used,end-begin,end-appStart));p.replay.index++;if(p.replay.index>=p.replay.samples.length)p.replay.active=false;}
 }
});
})()'''
def stats(values):
    return {'count':len(values),'p50Ms':sorted(values)[math.floor((len(values)-1)*.5)],'p95Ms':sorted(values)[math.floor((len(values)-1)*.95)],'meanMs':sum(values)/len(values),'maxMs':max(values)}
def intervals(rows):return[b['nativeTimestamp']-a['nativeTimestamp']for a,b in zip(rows,rows[1:])]
errors=[];wheel={};guided=[]
with sync_playwright()as p:
    browser=launch(p)
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);context.add_init_script(HOOK)
    old,new=context.new_page(),context.new_page()
    for label,page,port in [('before',old,4176),('after',new,4177)]:
        watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,at in VIEWS:visit(page,at)
        routes=[]
        for key,at in [('T01',.9),('T12',4.05),('T23',8.35),('T3W',11.26),('WIDE',11.66)]:
            visit(page,at);page.mouse.move(1100,260);page.wait_for_timeout(80);page.evaluate('window.__tourProbe.settles=[]')
            for delta in [15]*3+[-15]*3:
                y=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=y)
                page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
            values=page.evaluate('window.__tourProbe.settles');assert len(values)==6,(label,key,values);routes.append({'key':key,'H':at,'deltas':[15]*3+[-15]*3,'samplesMs':values})
        wheel[label]={'routes':routes,'stats':stats([v for r in routes for v in r['samplesMs']])};print(label,'wheel30',wheel[label]['stats'],flush=True)
    for mode in ['pixel','native']:
        new.bring_to_front();new.locator(f'.tour-actions [data-mode={mode}]').click();guide_start(new,3.34)
        new.evaluate('window.__guidePerf.frames=[];window.__guidePerf.capture=true')
        new.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="B1"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=120000,polling=100)
        capture=new.evaluate('window.__guidePerf.capture=false;window.__guidePerf.frames');guide_stop(new)
        # Central70% excludes route endpoint quantization. Twelve initial replay
        # frames let the original camera converge; same indices excluded in both.
        first=math.floor(len(capture)*.15);last=math.floor(len(capture)*.85);trajectory=capture[first:last]
        assert len(trajectory)>60,(mode,len(capture),len(trajectory))
        old.bring_to_front();old.locator(f'.tour-actions [data-mode={mode}]').click();visit(old,3.34)
        old.evaluate('rows=>{window.__guidePerf.replay={active:true,index:0,samples:rows,frames:[]};scrollBy({top:1,behavior:"instant"});dispatchEvent(new Event("scroll"));}',trajectory)
        old.wait_for_function('window.__guidePerf.replay&&!window.__guidePerf.replay.active',timeout=120000,polling=100)
        replay=old.evaluate('window.__guidePerf.replay.frames');assert len(replay)==len(trajectory)
        actual,baseline=trajectory[12:],replay[12:]
        max_h=max(abs(a['h']-b['h'])for a,b in zip(actual,baseline));assert max_h<.000003,(mode,max_h)
        assert all(a['time']==b['time']==2 and abs(a['height']-b['height'])<.0001 for a,b in zip(actual,baseline))
        result={'mode':mode,'path':'A3→B1 actual guide, original7s movement','actualGuideFullCapture':capture,'selectedActualTrajectory':trajectory,'baselineReplay':replay,
            'excludedInitialConvergenceFrames':12,'measuredSamplesPerPhase':len(actual),'maxMatchedDisplayHError':max_h,
            'afterFrameWork':stats([r['costMs']for r in actual]),'beforeFrameWork':stats([r['costMs']for r in baseline]),
            'afterCallbackOnly':stats([r['callbackMs']for r in actual]),'beforeCallbackOnly':stats([r['callbackMs']for r in baseline]),
            'afterIntervals':stats(intervals(actual)),'beforeIntervals':stats(intervals(baseline))}
        result['frameWorkP95ChangePercent']=100*(result['afterFrameWork']['p95Ms']/result['beforeFrameWork']['p95Ms']-1)
        result['intervalP95ChangePercent']=100*(result['afterIntervals']['p95Ms']/result['beforeIntervals']['p95Ms']-1)
        guided.append(result);save(OUT,'performance-progress.json',{'complete':False,'wheel30':wheel,'guided':guided})
        print(mode,'matched guide n',len(actual),'H error',max_h,'p95 changes',result['frameWorkP95ChangePercent'],result['intervalP95ChangePercent'],flush=True)
    assert not errors,errors
    report={'completed':True,'candidateId':json.loads((OUT/'build-verification.json').read_text())['candidateId'],'baselineId':json.loads((OUT/'baseline-version.json').read_text())['candidateId'],
        'browser':browser.version,'viewport':[1440,900],'DPR':1,'wheel30':wheel,'guided':guided,'wheelP95ChangePercent':100*(wheel['after']['stats']['p95Ms']/wheel['before']['stats']['p95Ms']-1),
        'method':'one browser, only one page rendered/measured at a time; both original full-route pixel/native/pixel prewarm; no screenshot/video; true guide capture then Step3 replay of exact actual nativeY/animation timestamps; central70%, same12 convergence frames excluded; pose/time tolerance asserted',
        'frameWorkConvention':'guide:original renderer RAF callback including guide/native write/read handling; baseline:external native write+test-only scroll notification+original renderer callback, so equivalent total script work; callback-only also retained; native timestamps used for drawing intervals',
        'baselineReplayIsTrustedInput':False,'wheelIsActualNativeInput':True,'environmentTime':2,'gpuCompletionTiming':False,'hardwareFPSProof':False,'errors':errors}
    save(OUT,'performance-matched.json',report);context.close();browser.close()
    print('DONE matched performance',flush=True)
