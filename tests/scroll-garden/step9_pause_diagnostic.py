"""Observe actual post-open layout/draw frames on both isolated production builds."""
from playwright.sync_api import sync_playwright
from step9_common import *
with sync_playwright()as p:
 b=launch(p);results=[]
 for version,port in [('step8',4174),('step9',4173)]:
  context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();ready(page,f'http://127.0.0.1:{port}/?tour=prototype&waterTime=2')
  for cycle in range(4):
   go(page,10.05);page.locator('[data-project-tab=live]').click();frames(page)
   trace=page.evaluate('''()=>new Promise(resolve=>{const rows=[],start=performance.now();function tick(){const d=document.querySelector('#tour-host').dataset,r=document.querySelector('.tour-project-live-space').getBoundingClientRect();rows.push({ms:performance.now()-start,draws:window.__tourProbe.draws,time:d.sceneTime,viewHeight:d.viewHeight,camera:d.cameraPosition,live:[r.x,r.y,r.width,r.height]});if(performance.now()-start>=800)resolve(rows);else requestAnimationFrame(tick);}requestAnimationFrame(tick);})''')
   results.append({'version':version,'cycle':cycle,'trace':trace,'changedFrames':[r for i,r in enumerate(trace)if i==0 or r['draws']!=trace[i-1]['draws']],'clockFixed':len({r['time']for r in trace})==1})
   assert len({r['draws']for r in trace if r['ms']>=400})==1 and len({r['time']for r in trace})==1
   page.locator('.tour-project-close').click();frames(page)
  context.close()
 save('project-pause-diagnostic.json',{'passed':True,'method':'four opens per isolated Step8 and final Step9; sample every actual RAF for800ms after original two-frame helper; require last400ms drawing and all scene time fixed','rows':results})
 print('PASS: late draw counts',[(r['version'],r['cycle'],[(round(f['ms']),f['draws'])for f in r['changedFrames']])for r in results],flush=True);b.close()
