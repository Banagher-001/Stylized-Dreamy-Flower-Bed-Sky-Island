"""Serial ABBA actual-guide comparison with identical animated scene samples.
Only motion timestamps of the established renderer RAF callback are controlled;
real performance.now/native RAF timestamps remain untouched. Not motion footage.
No concurrent browser/screenshot/video may run during this command.
"""
import json,math
from playwright.sync_api import sync_playwright
from step5_common import *

HOOK=r'''(()=>{
 const raw=requestAnimationFrame.bind(window);window.__cloudPerf={renderer:null,control:null};
 window.requestAnimationFrame=callback=>raw(nativeTimestamp=>{
  const p=window.__cloudPerf,c=p.control,d=document.querySelector('#tour-host')?.dataset;
  let used=nativeTimestamp,measured=false;
  if(c&&callback===p.renderer){
   if(!c.started&&d?.guidePhase==='moving'&&d?.guideStation==='B1')c.started=true;
   used=c.base+(c.started?Math.min(c.index,c.count-1):0)*1000/60;
   measured=c.started&&!c.done;
  }
  const before=window.__tourProbe?.draws??0,begin=performance.now();callback(used);const end=performance.now();
  if((window.__tourProbe?.draws??0)>before){
   const now=document.querySelector('#tour-host').dataset;
   if(now.guidePhase==='moving')p.renderer=callback;
   if(measured){c.frames.push({nativeTimestamp,usedTimestamp:used,costMs:end-begin,h:Number(now.displayH),y:scrollY,time:Number(now.sceneTime),position:now.cameraPosition,target:now.cameraTarget,height:now.viewHeight,draws:window.__tourProbe.draws});c.index++;if(c.index===c.count)c.done=true;}
  }
 });
})()'''
def stats(v):
    assert v
    return {'count':len(v),'p50Ms':sorted(v)[math.floor((len(v)-1)*.5)],'p95Ms':sorted(v)[math.floor((len(v)-1)*.95)],'meanMs':sum(v)/len(v),'maxMs':max(v)}
def change(a,b):return 100*(a/b-1)
def intervals(rows):return[b['nativeTimestamp']-a['nativeTimestamp']for a,b in zip(rows,rows[1:])]
build=json.loads((OUT/'build-verification.json').read_text());baseline=json.loads((OUT/'baseline-version.json').read_text())
errors=[];wheel={};runs=[];groups={};resources={}
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);context.add_init_script(HOOK)
    pages={phase:context.new_page()for phase in ['before','after']}
    for phase,port in [('before',4178),('after',4179)]:
        page=pages[phase];watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,h in VIEWS:visit(page,h)
        resources[phase]=[]
        for mode in ['native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for key,h in [('O',0),('A2',2.54),('B2',5.95),('C2',10.05),('W',11.5)]:
                visit(page,h);frames(page)
                actual=json.loads(data(page)['rendererStats'])
                resources[phase].append({'mode':mode,'pose':key,'stats':{k:actual[k]for k in ['geometries','textures','programs','calls','triangles']}})
        routes=[]
        for key,h in [('T01',.9),('T12',4.05),('T23',8.35),('T3W',11.26),('WIDE',11.66)]:
            visit(page,h);page.mouse.move(1100,260);page.wait_for_timeout(80);page.evaluate('window.__tourProbe.settles=[]')
            for delta in [15]*3+[-15]*3:
                y=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=y)
                page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
            values=page.evaluate('window.__tourProbe.settles');assert len(values)==6,(phase,key,values)
            routes.append({'pose':key,'H':h,'deltas':[15]*3+[-15]*3,'samplesMs':values})
        wheel[phase]={'routes':routes,'stats':stats([x for r in routes for x in r['samplesMs']])}
        # Identify the stable Three renderer callback while guide movement is
        # actually running. Finite still callbacks cannot replace this identity.
        guide_start(page,3.8,reading=False)
        page.wait_for_function('window.__cloudPerf.renderer!==null&&Number(document.querySelector("#tour-host").dataset.displayH)>3.81')
        guide_stop(page);assert data(page)['sceneTime']=='2.000000'
        print(phase,'real wheel30',wheel[phase]['stats'],flush=True)
    assert resources['before']==resources['after'],resources
    save(OUT,'performance-progress.json',{'complete':False,'candidateId':build['candidateId'],'wheel30':wheel,'runs':runs})
    for mode in ['pixel','native']:
        for phase in ['before','after','after','before']:
            page=pages[phase];page.bring_to_front();guide_stop(page);pause(page)
            page.locator(f'.tour-actions [data-mode={mode}]').click();visit(page,3.8)
            t=float(data(page)['sceneTime'])
            page.evaluate('window.__cloudPerf.control={base:0,index:0,count:240,started:false,done:false,frames:[]}')
            page.locator('#tour-motion').click();assert data(page)['motionState']=='running'
            guide_start(page,reading=False)
            page.wait_for_function('window.__cloudPerf.control.done',timeout=120000,polling=100)
            raw=page.evaluate('window.__cloudPerf.control.frames');assert len(raw)==240
            # The control wrapper holds its final timestamp after the last
            # sample, so pause/stop cannot add unmatched environment time.
            guide_stop(page);pause(page)
            assert abs(float(data(page)['sceneTime'])-(t+239/60))<.000002
            selected=raw[36:204]
            run={'mode':mode,'phase':phase,'startEnvironmentTime':t,'raw':raw,'measured':selected,'frameWork':stats([r['costMs']for r in selected]),'intervals':stats(intervals(selected))}
            runs.append(run);save(OUT,'performance-progress.json',{'complete':False,'candidateId':build['candidateId'],'wheel30':wheel,'runs':runs})
            print(mode,phase,'n',len(selected),'time',t,'workp95',run['frameWork']['p95Ms'],'intervalp95',run['intervals']['p95Ms'],flush=True)
        chosen=[r for r in runs if r['mode']==mode];before=[r for r in chosen if r['phase']=='before'];after=[r for r in chosen if r['phase']=='after']
        max_h=max_time=0
        for a,b in zip(before,after):
            assert a['startEnvironmentTime']==b['startEnvironmentTime']
            for x,y in zip(a['measured'],b['measured']):
                max_h=max(max_h,abs(x['h']-y['h']));max_time=max(max_time,abs(x['time']-y['time']))
                assert x['position']==y['position']and x['target']==y['target']and x['height']==y['height']
        assert max_h<.000003 and max_time<.000002
        result={'maxMatchedHError':max_h,'maxEnvironmentTimeError':max_time}
        for phase in ['before','after']:
            rows=[r for r in chosen if r['phase']==phase]
            result[phase]={'frameWork':stats([f['costMs']for r in rows for f in r['measured']]),'intervals':stats([v for r in rows for v in intervals(r['measured'])])}
        result['frameWorkP95ChangePercent']=change(result['after']['frameWork']['p95Ms'],result['before']['frameWork']['p95Ms'])
        result['intervalP95ChangePercent']=change(result['after']['intervals']['p95Ms'],result['before']['intervals']['p95Ms'])
        groups[mode]=result
    assert not errors,errors
    wheel_change=change(wheel['after']['stats']['p95Ms'],wheel['before']['stats']['p95Ms'])
    passed=wheel_change<=10 and all(g['frameWorkP95ChangePercent']<=10 and g['intervalP95ChangePercent']<=10 for g in groups.values())
    report={'passed':passed,'completed':True,'candidateId':build['candidateId'],'baselineId':baseline['candidateId'],'browser':browser.version,'viewport':[1440,900],'DPR':1,
        'method':'one browser, serial pages, full-route same prewarm; true30 native wheels; each mode ABBA actual original guide fromH3.8 towardB1, environment playing; stable original renderer receives matching240 motion timestamps at60Hz via explicit test wrapper, real performance.now and actual native RAF timestamps unchanged; central168 same-index frames per run, all336 work/334 interval samples per phase combined; no best-run selection; same actual camera and animated environment times asserted; no screenshot/video/concurrent browsers; controlled timing diagnostic not footage or hardware FPS',
        'wheel30':wheel,'wheelP95ChangePercent':wheel_change,'resources':resources,'sameGeometryTextureProgramCallsTriangles':True,'runs':runs,'groups':groups,'errors':errors,'hardwareFPSProof':False,'productCodeChangedDuringBenchmark':False}
    save(OUT,'performance-comparison.json',report);context.close();browser.close()
    print('DONE',passed,'wheel p95',wheel_change,'groups',json.dumps(groups),flush=True)
