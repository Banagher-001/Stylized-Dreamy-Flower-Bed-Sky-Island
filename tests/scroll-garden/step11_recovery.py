"""Reuse the real native CDP transport; exercise the Step11 stable/overlay contracts."""
from pathlib import Path
source=Path(__file__).with_name('step7_recovery.py').read_text()
prefix=source[:source.index('  go(10.05);wait(')].replace('docs/evidence/scroll-garden-step-7','docs/evidence/scroll-garden-step-11').replace('step7-native-','step11-native-').replace('STEP 07','张辰翰')
cleanup=source[source.index('\n finally:'):]
prefix=prefix.replace("   evaluate('document.querySelector('+json.dumps(selector)+').scrollIntoView({block:\"center\",inline:\"nearest\",behavior:\"instant\"})')", "   evaluate('(()=>{const e=document.querySelector('+json.dumps(selector)+'),r=e.getBoundingClientRect();if(r.top<0||r.bottom>900||r.left<0||r.right>1440)e.scrollIntoView({block:\"center\",inline:\"nearest\",behavior:\"instant\"})})()')")
assert 'if(r.top<0' in prefix,'native helper must not scroll an already visible sticky control'
body=r'''
  from step11_common import PROBE
  evaluate(PROBE)
  wait('document.querySelector("main").dataset.layoutReady==="true"')
  evaluate('window.__originalReadingCanvas=document.querySelector("canvas")')
  def reading_state():return evaluate('(()=>{const m=document.querySelector("main"),d=document.querySelector("#tour-host").dataset;return{mode:m.dataset.readingMode,anchor:m.dataset.flowAnchor,y:scrollY,h:d.displayH,time:d.sceneTime,position:d.cameraPosition,target:d.cameraTarget,height:d.viewHeight,canvas:window.__originalReadingCanvas===document.querySelector("canvas")}})()')
  def full_picture(name):
   evaluate('document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
   raw=base64.b64decode(rpc('Page.captureScreenshot',{'format':'png','clip':{'x':0,'y':0,'width':1440,'height':900,'scale':1},'captureBeyondViewport':False},session)['data']);(OUT/name).write_bytes(raw);return Image.open(BytesIO(raw)).convert('RGB')
  def flow_to(id):
   evaluate('(()=>{const e=document.querySelector(".tour-reading-flow [data-flow-anchor='+id+']"),r=e.getBoundingClientRect(),h=document.querySelector(".tour-header").getBoundingClientRect();scrollTo({top:scrollY+r.top-h.bottom-15,behavior:"instant"})})()')
   wait('document.querySelector("main").dataset.flowAnchor==='+json.dumps(id));settled()
  go(2.54);native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="stable"&&document.querySelector("main").dataset.flowAnchor==="A2"')
  wait('[...document.querySelectorAll(".tour-reading-flow img")].every(e=>!e.src||e.complete)');time.sleep(.3)
  before=reading_state();pictureBefore=full_picture('native-stable-before-hidden.png');draws=evaluate('window.__tourProbe.draws');other=hide();time.sleep(.4);assert evaluate('window.__tourProbe.draws')==draws;show(other)
  assert reading_state()==before;assert ImageChops.difference(pictureBefore,full_picture('native-stable-after-hidden.png')).getbbox()is None
  record('real native hidden/return preserves stable text, exact native position, pixels and paused scene',{'state':before,'zeroHiddenDrawMs':400,'actualHiddenObserved':True,'fullViewportPixelsExact':True})
  lose();assert evaluate('document.querySelector("main").dataset.readingMode==="stable"&&document.querySelectorAll(".tour-reading-flow article[aria-hidden=false]").length===10&&!document.querySelector("#tour-reference").hidden')
  restore();wait('document.querySelector("main").dataset.immersiveAvailable==="true"');assert reading_state()==before
  native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="immersive"');wait('document.querySelector("#tour-host").dataset.renderState==="ready"');settled();assert abs(float(evaluate('document.querySelector("#tour-host").dataset.displayH'))-2.54)<.003
  record('offscreen context recovery retains full stable reading and waits for explicit immersive choice',{'noAutomaticCameraReturn':True,'sameCanvas':True,'returnedH':2.54,'allTenStationsWhileLost':True})
  go(10.05);native_click('[data-project-tab=live]');wait('document.querySelector("#tour-host").dataset.projectView==="live"');lose();native_click('[data-project-view=archive]');close_project()
  wait('document.querySelector("main").dataset.readingMode==="stable"&&document.querySelector("main").dataset.flowAnchor==="C2"');assert evaluate('document.querySelectorAll("dialog[open]").length===0&&document.querySelectorAll("video").length===0')
  restore();wait('document.querySelector("main").dataset.immersiveAvailable==="true"');assert evaluate('document.querySelector("main").dataset.readingMode==="stable"')
  record('close during live graphic loss returns to full C2 reading and recovery keeps layout',{'noModalDeadlock':True,'stableAnchor':'C2','archiveStillUsable':True,'noVideoAfterClose':True})
  native_click('[data-project-tab=archive]');native_click('.tour-project-play');wait('document.querySelector("video")?.currentTime>.15&&!document.querySelector("video").paused');other=hide();time.sleep(.3);assert evaluate('document.querySelector("video").paused');show(other);assert evaluate('document.querySelector("video").paused');close_project();assert evaluate('document.querySelectorAll("video").length===0')
  record('real hidden pauses archive video, return never autoplays and close releases decoder',{'realHidden':True,'videoPausedAfterReturn':True,'decoderReleased':True})
  native_click('#tour-stop-overview');native_click('#tour-motion');start=float(evaluate('document.querySelector("#tour-host").dataset.sceneTime'));wait('Number(document.querySelector("#tour-host").dataset.sceneTime)>'+str(start+.1));flow_to('A2');time.sleep(.3);draws=evaluate('window.__tourProbe.draws');clock=evaluate('document.querySelector("#tour-host").dataset.sceneTime');time.sleep(.4);assert evaluate('window.__tourProbe.draws')==draws and evaluate('document.querySelector("#tour-host").dataset.sceneTime')==clock
  native_click('#tour-stop-overview');wait('Number(document.querySelector("#tour-host").dataset.sceneTime)>'+str(float(clock)+.1));native_click('#tour-motion')
  record('playing cover suspends all GL and its clock offscreen, then resumes only preserved play intent',{'offscreenZeroDrawMs':400,'offscreenClock':clock,'sameCanvas':True})
  native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="immersive"');go(10.05);native_click('[data-project-tab=live]')
  rpc('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'reduce'}]},session);time.sleep(.2);assert evaluate('document.querySelector(".tour-project-dialog").open');close_project();wait('document.querySelector("main").dataset.readingMode==="stable"&&document.querySelector("main").dataset.flowAnchor==="C2"')
  paused=reading_state();rpc('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'no-preference'}]},session);time.sleep(.3);assert reading_state()==paused
  record('reduced-motion change respects active modal ownership, restores C2 and never auto-resumes',{'sourceAnchor':'C2','modeAfterClose':'stable','preferenceRemovedStillPaused':True})
  exceptions=[e['params']for e in events if e.get('method')=='Runtime.exceptionThrown'];assert not exceptions,exceptions
  diagnostics=[e['params']for e in events if e.get('method')=='Runtime.consoleAPICalled'and e.get('params',{}).get('type')in ['warning','error']]
  (OUT/'native-recovery.json').write_text(json.dumps({'passed':True,'engine':'native Chromium, Linux Xvfb/SwiftShader; real CDP target switching and context extension','checks':results,'unhandledExceptions':exceptions,'intentionalContextLossConsoleDiagnostics':diagnostics,'fakeHiddenEventsUsed':False,'physicalDeviceOrFPSProof':False},ensure_ascii=False,indent=2)+'\n');print('PASS',len(results),'native recovery groups',flush=True)
'''
exec(compile(prefix+body+cleanup,'<Step11 native recovery>','exec'),globals())
