from pathlib import Path
import json
from playwright.sync_api import sync_playwright
OUT=(Path(__file__).resolve().parents[2]/'docs/evidence/step-9')
TRACK='''(()=>{let raf=0,draw=0;const r=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=f=>r(t=>{raf++;f(t)});for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){const p=WebGL2RenderingContext.prototype,o=p[name];p[name]=function(...a){draw++;return o.apply(this,a)}}window.__counts=()=>({raf,draw});})()'''
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=b.new_context(viewport={'width':1440,'height':1000});c.add_init_script(TRACK);q=c.new_page();issues=[];q.on('console',lambda m:issues.append(m.text)if m.type in('error','warning')else None)
 q.goto('http://127.0.0.1:4174/?waterTime=2',wait_until='networkidle');q.wait_for_selector('#scene-host[data-render-state="ready"]');q.wait_for_timeout(200);a=q.evaluate('window.__counts()');q.wait_for_timeout(1000);z=q.evaluate('window.__counts()');assert a==z
 q.get_by_role('button',name='正常画面',exact=True).click();q.wait_for_timeout(150);resized=q.evaluate('window.__counts()');q.wait_for_timeout(800);assert resized==q.evaluate('window.__counts()')
 q.get_by_role('button',name='播放动效',exact=True).click();q.wait_for_function("Number(document.querySelector('#scene-host').dataset.sceneTime)>2.02")
 q.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))");q.wait_for_timeout(100);hidden=q.evaluate('window.__counts()');clock=q.locator('#scene-host').get_attribute('data-scene-time');q.wait_for_timeout(1000);assert hidden==q.evaluate('window.__counts()')and clock==q.locator('#scene-host').get_attribute('data-scene-time')
 q.evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))");q.wait_for_selector('#scene-host[data-motion-state="running"]')
 q.goto('http://127.0.0.1:5173/?waterTime=2',wait_until='networkidle')
 cleanup=q.evaluate('''async()=>{
 const {createScene}=await import('/src/scene/createScene.ts');const {createRenderer}=await import('/src/rendering/createRenderer.ts');const {createAnimationController}=await import('/src/animation/createAnimationController.ts');
 const p=EventTarget.prototype,add=p.addEventListener,remove=p.removeEventListener,records=[];const Native=window.ResizeObserver;const active=new Set();
 const track=t=>t===window||t===document||t instanceof HTMLCanvasElement||t instanceof MediaQueryList;
 p.addEventListener=function(type,fn,opt){if(track(this)&&!records.some(r=>r.t===this&&r.type===type&&r.fn===fn&&r.capture===!!(typeof opt==='boolean'?opt:opt?.capture)))records.push({t:this,type,fn,capture:!!(typeof opt==='boolean'?opt:opt?.capture)});return add.call(this,type,fn,opt);};
 p.removeEventListener=function(type,fn,opt){const i=records.findIndex(r=>r.t===this&&r.type===type&&r.fn===fn&&r.capture===!!(typeof opt==='boolean'?opt:opt?.capture));if(i>=0)records.splice(i,1);return remove.call(this,type,fn,opt);};
 window.ResizeObserver=class extends Native{observe(...a){active.add(this);return super.observe(...a)}disconnect(){active.delete(this);return super.disconnect()}};
 let maxListeners=0,maxObservers=0;const h=document.createElement('div');h.style.cssText='width:96px;height:96px';document.body.append(h);
 try{for(let i=0;i<20;i++){const w=createScene(),v=createRenderer(h,'pixel',w.setAspect),clock=createAnimationController(()=>{},2,true);v.setAnimating(false);v.start(w.scene,w.camera,()=>w.update(clock.time));await new Promise(requestAnimationFrame);maxListeners=Math.max(maxListeners,records.length);maxObservers=Math.max(maxObservers,active.size);clock.dispose();v.dispose();w.dispose();if(records.length||active.size)throw new Error('Leaked '+records.map(r=>r.type)+' / observers '+active.size);}return {cycles:20,maxListeners,maxObservers,remainingListeners:records.length,remainingObservers:active.size};}
 finally{p.addEventListener=add;p.removeEventListener=remove;window.ResizeObserver=Native;h.remove();}
 }''')
 assert not issues,issues;result={'paused':{'before':a,'afterOneSecond':z,'noContinuousRAFOrDraw':True},'modeChange':{'counts':resized,'settlesWithoutContinuousWork':True},'visibilityFixture':{'counts':hidden,'timeFrozen':True,'notNativeTabTest':True},'cleanup':cleanup,'issues':issues};(OUT/'scheduling-and-cleanup.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True);b.close()
