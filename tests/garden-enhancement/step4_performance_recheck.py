"""Counterbalanced native-mode recheck. Controlled motion timestamps lock the
same original actual trajectory; real cost/native frame intervals stay measured.
This is a timing diagnostic, not original-time user-interaction footage.
"""
import ast,json,math
from playwright.sync_api import sync_playwright
from step4_common import *

tree=ast.parse((ROOT/'tests/garden-enhancement/step4_performance.py').read_text())
HOOK=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='HOOK'for t in n.targets))
HOOK=HOOK.replace('const before=window.__tourProbe.draws,appStart=performance.now();', '''
 if(p.force&&p.rendererCallback===callback){
  const d=document.querySelector('#tour-host').dataset;
  if(d.guidePhase==='moving'&&d.guideStation==='B1'){
   used=p.force.index<p.force.samples.length?p.force.samples[p.force.index].usedTimestamp:p.force.samples.at(-1).usedTimestamp+(p.force.index-p.force.samples.length+1)*50;
   p.force.index++;
  }
 }
 const before=window.__tourProbe.draws,appStart=performance.now();''')
HOOK=HOOK.replace('const d=document.querySelector(\'#tour-host\').dataset;\n  if(p.capture', "const d=document.querySelector('#tour-host').dataset;\n  if(d.cameraState==='moving'||d.guidePhase==='moving')p.rendererCallback=callback;\n  if(p.capture")
assert'p.rendererCallback=callback'in HOOK and'if(p.force&&p.rendererCallback===callback)'in HOOK
original=json.loads((OUT/'performance-matched.json').read_text());template=next(r for r in original['guided']if r['mode']=='native');full=template['actualGuideFullCapture'];selected=template['selectedActualTrajectory']
def stats(v):return{'count':len(v),'p50Ms':sorted(v)[math.floor((len(v)-1)*.5)],'p95Ms':sorted(v)[math.floor((len(v)-1)*.95)],'meanMs':sum(v)/len(v),'maxMs':max(v)}
runs=[];errors=[]
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1);context.add_init_script(probe);context.add_init_script(HOOK)
    old,new=context.new_page(),context.new_page()
    for page,port in [(old,4176),(new,4177)]:
        watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,at in VIEWS:visit(page,at)
        page.locator('.tour-actions [data-mode=native]').click()
    for i,phase in enumerate(['before','after','after','before']):
        if phase=='before':
            old.bring_to_front();visit(old,3.34)
            old.evaluate('rows=>{window.__guidePerf.replay={active:true,index:0,samples:rows,frames:[]};scrollBy({top:1,behavior:"instant"});dispatchEvent(new Event("scroll"));}',selected)
            old.wait_for_function('!window.__guidePerf.replay.active',timeout=120000,polling=100)
            raw=old.evaluate('window.__guidePerf.replay.frames');assert len(raw)==len(selected)
        else:
            new.bring_to_front();guide_start(new,3.34)
            new.evaluate('rows=>{window.__guidePerf.force={index:0,samples:rows};window.__guidePerf.frames=[];window.__guidePerf.capture=true;}',full)
            new.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="B1"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=120000,polling=100)
            actual=new.evaluate('window.__guidePerf.capture=false;window.__guidePerf.force=null;window.__guidePerf.frames');guide_stop(new)
            # Timestamp lock must reproduce every original guide movement sample.
            assert len(actual)>=len(full),(len(actual),len(full));raw=actual[math.floor(len(full)*.15):math.floor(len(full)*.85)]
        measured=raw[12:];reference=selected[12:]
        error=max(abs(a['h']-b['h'])for a,b in zip(measured,reference));assert error<.000003,(phase,error)
        assert len(measured)==len(reference)and all(r['time']==2 for r in measured)
        entry={'iteration':i,'phase':phase,'frames':raw,'measured':measured,'maxMatchedHError':error,'frameWork':stats([r['costMs']for r in measured]),'intervals':stats([b['nativeTimestamp']-a['nativeTimestamp']for a,b in zip(measured,measured[1:])])}
        runs.append(entry);save(OUT,'performance-recheck-progress.json',{'complete':False,'runs':runs});print(i,phase,'n',len(measured),'Herror',error,'workp95',entry['frameWork']['p95Ms'],'intervalp95',entry['intervals']['p95Ms'],flush=True)
    assert not errors,errors
    groups={}
    for phase in ['before','after']:
        frames=[r for run in runs if run['phase']==phase for r in run['measured']];iv=[b['nativeTimestamp']-a['nativeTimestamp']for run in runs if run['phase']==phase for a,b in zip(run['measured'],run['measured'][1:])]
        groups[phase]={'frameWork':stats([r['costMs']for r in frames]),'intervals':stats(iv)}
    work=100*(groups['after']['frameWork']['p95Ms']/groups['before']['frameWork']['p95Ms']-1);iv=100*(groups['after']['intervals']['p95Ms']/groups['before']['intervals']['p95Ms']-1)
    save(OUT,'performance-native-recheck.json',{'completed':True,'candidateId':original['candidateId'],'mode':'native','order':['before','after','after','before'],'method':'one browser serial ABBA; actual previous guide trajectory/time samples reused; guide receives matching movement timestamps via test-only RAF wrapper to lock exact nativeY/camera path; performance.now and actual native RAF timestamps are NOT overridden; same twelve warm convergence frames excluded in all runs; all samples aggregated, no best-run selection; not footage/hardware FPS',
        'runs':runs,'groups':groups,'frameWorkP95ChangePercent':work,'intervalP95ChangePercent':iv,'within10Percent':work<=10 and iv<=10,'errors':errors})
    context.close();browser.close();print('DONE native recheck',work,iv,flush=True)
