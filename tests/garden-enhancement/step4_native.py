"""Real native Chrome/CDP scrollbar, hidden tab, context, resize/zoom and RM.
Reuses only the established transport; no old evidence output is written.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
import json
candidate_id=json.loads((ROOT/'docs/evidence/garden-enhancement-step-4/build-verification.json').read_text())['candidateId']
source=(ROOT/'tests/scroll-garden/step7_recovery.py').read_text()
prefix=source[:source.index('  go(10.05);wait(')]
cleanup=source[source.index('\n finally:'):]
prefix=prefix.replace('docs/evidence/scroll-garden-step-7','docs/evidence/garden-enhancement-step-4').replace('step7-native-','garden-step4-native-').replace('127.0.0.1:4173','127.0.0.1:4177').replace('STEP 07','张辰翰')
prefix=prefix.replace("'--window-size=1440,1000'", "'--window-position=0,0','--window-size=1440,1000'")
# Keep the native scrollbar inside the actual headed window, not on its clipped
# right border. Functional1440/900 is covered separately in each engine.
prefix=prefix.replace("'width':1440,'height':900,'deviceScaleFactor':1,'mobile':False", "'width':1366,'height':768,'deviceScaleFactor':1,'mobile':False")
prefix=prefix.replace("   evaluate('document.querySelector('+json.dumps(selector)+').scrollIntoView({block:\"center\",inline:\"nearest\",behavior:\"instant\"})')", "   evaluate('(()=>{const e=document.querySelector('+json.dumps(selector)+'),r=e.getBoundingClientRect();if(r.top<0||r.bottom>900||r.left<0||r.right>1440)e.scrollIntoView({block:\"center\",inline:\"nearest\",behavior:\"instant\"})})()')")
assert'if(r.top<0'in prefix
prefix=prefix.replace('r.bottom>900||r.left<0||r.right>1440','r.bottom>innerHeight||r.left<0||r.right>innerWidth')
body=r'''
  import ast
  tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text())
  probe=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PROBE'for t in n.targets))
  evaluate(probe)
  wait('document.querySelector("main").dataset.layoutReady==="true"&&document.querySelector("#tour-host").dataset.guideState==="manual"')
  evaluate('window.__originalCanvas=document.querySelector("canvas");window.__originalNodes=[...document.querySelectorAll(".tour-reading-flow article")]')
  def guide_state():return evaluate('(()=>{const d=document.querySelector("#tour-host").dataset;return{y:scrollY,h:d.displayH,target:d.targetH,time:d.sceneTime,state:d.guideState,phase:d.guidePhase,station:d.guideStation,deadline:d.guideDeadline,reason:d.guideReason,layout:document.querySelector("main").dataset.readingMode,canvas:window.__originalCanvas===document.querySelector("canvas")}})()')
  def start(h):
   if evaluate('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="true"'):native_click('#tour-guide')
   go(h);wait('document.querySelector("#tour-guide").getAttribute("aria-disabled")==="false"');native_click('#tour-guide');wait('document.querySelector("#tour-host").dataset.guidePhase==="reading"');return guide_state()
  def full(name):
   size=evaluate('({width:innerWidth,height:innerHeight})');raw=base64.b64decode(rpc('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,**size,'scale':1},'captureBeyondViewport':False},session)['data']);(OUT/name).write_bytes(raw)
  # Native scrollbar thumb drag, not a DOM wheel/scroll substitute.
  before=start(2.54);rpc('Emulation.setScrollbarsHidden',{'hidden':False},session)
  full('native-scrollbar-before.png')
  bar=evaluate('({width:innerWidth,height:innerHeight,client:document.documentElement.clientWidth,total:document.documentElement.scrollHeight,y:scrollY})')
  thumb=max(20,bar['height']*bar['height']/bar['total']);top=bar['y']/(bar['total']-bar['height'])*(bar['height']-thumb)
  x=bar['width']-7;y=top+thumb/2
  rpc('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x,'y':y},session);time.sleep(.15)
  rpc('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,'x':x,'y':y},session)
  for delta in [10,20,35,50,70]:rpc('Input.dispatchMouseEvent',{'type':'mouseMoved','button':'left','buttons':1,'x':x,'y':y+delta},session);time.sleep(.035)
  rpc('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,'x':x,'y':y+70},session)
  wait('document.querySelector("#tour-host").dataset.guidePhase==="paused"');settled();after=guide_state()
  assert abs(after['y']-before['y'])>10,(bar,before,after)
  time.sleep(.5);assert guide_state()['y']==after['y'];full('native-scrollbar-takeover.png')
  record('real native scrollbar drag interrupts the first held guide without rebound',{'before':before,'after':after,'scrollbar':bar,'input':'actual CDP mouse drag at native scrollbar thumb; no CSS replacement or DOM synthetic scroll'})
  before=start(2.54);old_deadline=float(before['deadline']);other=hide();time.sleep(.25);hidden=guide_state();draws=evaluate('window.__tourProbe.draws');time.sleep(.4)
  assert guide_state()['time']==hidden['time']and evaluate('window.__tourProbe.draws')==draws
  show(other);wait('document.querySelector("#tour-host").dataset.guideState==="paused"');after=guide_state();assert abs(after['y']-before['y'])<=1 and after['deadline']==''
  remaining=max(0,(old_deadline-float(evaluate('performance.now()')))/1000+.15);time.sleep(remaining)
  assert guide_state()['y']==after['y']and guide_state()['state']=='paused'
  record('real hidden tab cancels reading deadline and never resumes after it would have expired',{'before':before,'hidden':hidden,'after':after,'zeroHiddenDrawMs':400,'oldDeadlineAllowedToPass':True,'noFakeHiddenEvent':True})
  before=start(2.54);rpc('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':2,'mobile':False},session)
  wait('document.querySelector("#tour-host").dataset.guidePhase==="paused"');wait('document.querySelector("main").dataset.layoutReady==="true"');settled();after=guide_state();assert abs(float(after['h'])-float(before['h']))<.003
  rpc('Emulation.setDeviceMetricsOverride',{'width':1440,'height':900,'deviceScaleFactor':1,'mobile':False},session);time.sleep(.4);settled()
  assert guide_state()['phase']=='paused';record('actual layout metrics change preserves anchor and explicit consent',{'before':before,'after':after,'returnedPaused':True})
  before=start(2.54);rpc('Emulation.setPageScaleFactor',{'pageScaleFactor':1.3},session);wait('document.querySelector("#tour-host").dataset.guidePhase==="paused"');scaled=guide_state()
  rpc('Emulation.setPageScaleFactor',{'pageScaleFactor':1},session);time.sleep(.3);assert guide_state()['phase']=='paused';record('actual visual scale change cancels guide without auto-resume',{'before':before,'scaled':scaled})
  before=start(2.54);lose();wait('document.querySelector("main").dataset.readingMode==="stable"');assert evaluate('document.querySelectorAll(".tour-reading-flow article[aria-hidden=false]").length===10')
  restore();wait('document.querySelector("main").dataset.immersiveAvailable==="true"');assert guide_state()['state']=='blocked'and guide_state()['phase']=='paused'
  native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="immersive"');settled();after=guide_state();assert after['canvas']and abs(float(after['h'])-2.54)<.003 and after['state']=='paused'
  record('real context loss retains all text and restores one canvas without guide restart',{'before':before,'after':after,'tenReadableNodesDuringLoss':True})
  before=start(10.05);native_click('[data-project-tab=live]');wait('document.querySelector("#tour-host").dataset.projectView==="live"');lose();assert evaluate('!document.querySelector(".tour-project-close").disabled')
  native_click('[data-project-view=archive]');close_project();restore();wait('document.querySelector("main").dataset.immersiveAvailable==="true"');assert guide_state()['state']=='blocked'and guide_state()['phase']=='paused'
  assert evaluate('document.querySelectorAll("video").length===0&&document.querySelectorAll("dialog[open]").length===0')
  native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="immersive"');settled();record('viewer close during graphics loss cannot revive guide or leak media',{'before':before,'after':guide_state(),'oneCanvas':True,'videoReleased':True})
  before=start(2.54);rpc('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'reduce'}]},session);wait('document.querySelector("main").dataset.readingMode==="stable"');assert guide_state()['state']=='blocked'and guide_state()['phase']=='paused'
  rpc('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'no-preference'}]},session);time.sleep(.3);assert guide_state()['phase']=='paused'
  record('actual reduced-motion preference change preserves stopped guide and stable reading',{'before':before,'after':guide_state()})
  # Existing stable-cover energy contract remains independent of the guide.
  native_click('#tour-stop-overview');native_click('#tour-motion');wait('document.querySelector("#tour-host").dataset.motionState==="running"')
  evaluate('(()=>{const e=document.querySelector(".tour-reading-flow [data-flow-anchor=A2]"),r=e.getBoundingClientRect(),header=document.querySelector(".tour-header").getBoundingClientRect();scrollTo({top:scrollY+r.top-header.bottom-15,behavior:"instant"})})()');time.sleep(.4);clock=guide_state()['time'];draws=evaluate('window.__tourProbe.draws');time.sleep(.4)
  assert guide_state()['time']==clock and evaluate('window.__tourProbe.draws')==draws
  native_click('#tour-stop-overview');wait('Number(document.querySelector("#tour-host").dataset.sceneTime)>'+str(float(clock)));assert guide_state()['state']=='blocked'and guide_state()['phase']=='paused'
  native_click('#tour-motion');record('offscreen stable cover suspends environment, return never enables guide',{'offscreenZeroDrawMs':400,'clock':clock,'guide':guide_state()})
  exceptions=[e['params']for e in events if e.get('method')=='Runtime.exceptionThrown'];assert not exceptions,exceptions
  (OUT/'native-guide-recovery.json').write_text(json.dumps({'passed':True,'candidateId':candidate_id,'engine':'native headed Chromium/Linux Xvfb/SwiftShader; actual CDP input, targets, metrics, scale and context extension','checks':results,'unhandledExceptions':exceptions,'fakeHiddenEventsUsed':False,'physicalDevice':False},ensure_ascii=False,indent=2)+'\n');print('PASS',len(results),'native guide lifecycle groups',flush=True)
'''
# Established transport names this helper close_project only in later harnesses.
body=body.replace('close_project();','close_project();')
body=body.replace("  before=start(10.05);", "  def close_project():\n   native_click('.tour-project-close');wait('document.querySelector(\"#tour-host\").dataset.overlayState===\"closed\"');settled()\n  before=start(10.05);")
exec(compile(prefix+body+cleanup,'<Step4 actual native lifecycle>','exec'),globals())
