from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
OUT=(Path(__file__).resolve().parents[2]/'docs/evidence/step-9')
INSTRUMENT='''(()=>{
 const g=WebGL2RenderingContext.prototype,live={},draw={calls:0};
 for(const type of ['Buffer','Texture','Program','VertexArray','Framebuffer','Renderbuffer']){
  const set=new Set();live[type]=set;const create=g['create'+type],destroy=g['delete'+type];
  g['create'+type]=function(...args){const v=create.apply(this,args);if(v)set.add(v);return v;};
  g['delete'+type]=function(v){set.delete(v);return destroy.call(this,v);};
 }
 for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){const original=g[name];g[name]=function(...args){draw.calls++;return original.apply(this,args);};}
 const windows=Array.from({length:11},()=>({frames:0,intervals:0,sum:0,max:0,long:0,bins:new Uint32Array(1001)}));let start=0,last=0;
 const raf=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=fn=>raf(t=>{const now=performance.now();if(start){const index=Math.min(10,Math.floor((now-start)/60000)),w=windows[index];w.frames++;if(last){const d=now-last;w.intervals++;w.sum+=d;w.max=Math.max(w.max,d);if(d>100)w.long++;w.bins[Math.min(1000,Math.floor(d))]++;}last=now;}fn(t);});
 window.__soak={begin(){start=performance.now();last=0;},summary(){return {elapsedMs:start?performance.now()-start:0,drawCalls:draw.calls,live:Object.fromEntries(Object.entries(live).map(([k,v])=>[k,v.size])),windows:windows.map((w,i)=>{let n=0,p95=0;for(let j=0;j<w.bins.length;j++){n+=w.bins[j];if(n>=w.intervals*.95){p95=j+1;break;}}return {minute:i+1,frames:w.frames,meanFPS:w.frames/60,p95IntervalMs:p95,maxIntervalMs:w.max,longFramesOver100ms:w.long};})};}};
})();'''
issues=[];snapshots=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 c=b.new_context(viewport={'width':1440,'height':1000});c.add_init_script(INSTRUMENT);q=c.new_page()
 q.on('pageerror',lambda e:issues.append(str(e)));q.on('console',lambda m:issues.append(m.text)if m.type in('error','warning')else None)
 q.goto('http://127.0.0.1:4173/?waterTime=2',wait_until='networkidle');q.wait_for_selector('#scene-host[data-render-state="ready"]')
 q.get_by_role('button',name='正常画面',exact=True).click();q.get_by_role('button',name='像素预览',exact=True).click()
 q.get_by_role('button',name='播放动效',exact=True).click();q.wait_for_function("Number(document.querySelector('#scene-host').dataset.sceneTime)>2.1")
 q.wait_for_timeout(5000);q.evaluate('window.__soak.begin()');cdp=c.new_cdp_session(q);cdp.send('Performance.enable')
 start=time.monotonic();before=q.evaluate('window.__soak.summary()');print('10-minute live production soak started',flush=True)
 while time.monotonic()-start<600:
  q.wait_for_timeout(30000);data=q.evaluate('window.__soak.summary()');raw=cdp.send('Performance.getMetrics')['metrics'];heap=next(x['value']for x in raw if x['name']=='JSHeapUsedSize')
  snapshots.append({'elapsedSeconds':time.monotonic()-start,'live':data['live'],'jsHeapUsedBytes':heap,'drawCalls':data['drawCalls']})
  print('elapsed',round(time.monotonic()-start),'seconds; GPU live',data['live'],flush=True)
 after=q.evaluate('window.__soak.summary()');q.get_by_role('button',name='暂停动效',exact=True).click()
 for i in range(25):q.get_by_role('button',name='正常画面',exact=True).click();q.get_by_role('button',name='像素预览',exact=True).click()
 final=q.evaluate('window.__soak.summary()');assert final['live']==before['live'],(before['live'],final['live'])
 assert not issues,issues
 report={'environment':'Chromium headless / ANGLE SwiftShader software; cloud diagnostic, no physical GPU FPS acceptance','browser':b.version,'wallSeconds':time.monotonic()-start,'before':before,'after':after,'after50ModeChanges':final,'snapshots':snapshots,'issues':issues,'passed':True}
 (OUT/'ten-minute-stability.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('10-minute soak and 50 mode changes passed',flush=True);b.close()
