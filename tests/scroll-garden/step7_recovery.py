"""Actual native Chromium tab visibility/context recovery; direct CDP, no hidden spoof."""
from pathlib import Path
from io import BytesIO
import base64,json,os,shutil,signal,subprocess,tempfile,time
from PIL import Image,ImageChops
from websockets.sync.client import connect

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-7'
OUT.mkdir(parents=True,exist_ok=True)
results=[]
def record(name,evidence):
 results.append({'check':name,'passed':True,'evidence':evidence});print(name,flush=True)

with tempfile.TemporaryDirectory(prefix='step7-native-') as profile:
 process=subprocess.Popen(['/usr/bin/chromium','--no-sandbox','--disable-background-networking','--disable-breakpad','--no-first-run','--no-default-browser-check','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1','--user-data-dir='+profile,'--window-size=1440,1000','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 socket=None
 try:
  portfile=Path(profile)/'DevToolsActivePort';deadline=time.monotonic()+12
  while not portfile.exists():
   if process.poll()is not None or time.monotonic()>deadline:raise RuntimeError('Native browser failed to start')
   time.sleep(.05)
  port,path=portfile.read_text().splitlines()[:2];socket=connect('ws://127.0.0.1:'+port+path,max_size=20*1024*1024)
  counter=0;events=[]
  def rpc(method,params=None,session=None):
   global counter
   counter+=1;request={'id':counter,'method':method,'params':params or {}}
   if session:request['sessionId']=session
   socket.send(json.dumps(request))
   while True:
    reply=json.loads(socket.recv(timeout=20))
    if reply.get('id')==counter:
     if 'error'in reply:raise RuntimeError(reply['error'])
     return reply.get('result',{})
    events.append(reply)
  target=rpc('Target.createTarget',{'url':'http://127.0.0.1:4173/?tour=prototype&waterTime=2','newWindow':False})['targetId']
  session=rpc('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
  rpc('Runtime.enable',session=session);rpc('Page.enable',session=session)
  rpc('Emulation.setDeviceMetricsOverride',{'width':1440,'height':900,'deviceScaleFactor':1,'mobile':False},session)
  rpc('Target.activateTarget',{'targetId':target})
  def evaluate(expression):
   r=rpc('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True},session)
   if 'exceptionDetails'in r:raise RuntimeError(r['exceptionDetails'])
   return r['result'].get('value')
  def wait(expression):
   deadline=time.monotonic()+15
   while not evaluate(expression):
    if time.monotonic()>deadline:
     (OUT/'native-timeout-diagnostics.json').write_text(json.dumps({'expression':expression,'state':evaluate('({hidden:document.hidden,y:scrollY,data:{...document.querySelector("#tour-host")?.dataset},project:document.querySelector(".tour-project-dialog")?.outerHTML})')},ensure_ascii=False,indent=2)+'\n');raise RuntimeError('Timed out: '+expression)
    time.sleep(.05)
  def settled():
   wait('(()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return e.dataset.cameraState==="settled"&&Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001})()')
   evaluate('document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
  def go(h):
   evaluate(f'scrollTo({{top:{h}/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"}})')
   wait(f'(()=>{{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-{h})<.003}})()');settled()
  def state():return evaluate('(()=>{const d=document.querySelector("#tour-host").dataset;return {position:d.cameraPosition,target:d.cameraTarget,height:d.viewHeight,h:d.displayH,station:d.experimentStation,phase:d.experimentPhase,presentation:d.experimentPresentation,magic:d.experimentMagicFrame,time:d.sceneTime,project:d.projectView??"closed",text:document.querySelector(".experiment-reading article:not([hidden])")?.innerText}})()')
  def native_click(selector):
   evaluate('document.querySelector('+json.dumps(selector)+').scrollIntoView({block:"center",inline:"nearest",behavior:"instant"})')
   evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   box=evaluate('(()=>{const r=document.querySelector('+json.dumps(selector)+').getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()')
   assert 0<box['x']<1440 and 0<box['y']<900,(selector,box)
   rpc('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**box},session)
   rpc('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**box},session)
  def image(name):
   evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   bounds=evaluate('(()=>{const r=document.querySelector("canvas").getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})()')
   raw=base64.b64decode(rpc('Page.captureScreenshot',{'format':'png','clip':bounds,'captureBeyondViewport':False},session)['data']);(OUT/name).write_bytes(raw)
   return Image.open(BytesIO(raw)).convert('RGB')
  def hide():
   other=rpc('Target.createTarget',{'url':'about:blank','newWindow':False})['targetId'];rpc('Target.activateTarget',{'targetId':other});wait('document.hidden&&document.querySelector("#tour-host").dataset.visibility==="hidden"');return other
  def show(other):
   rpc('Target.activateTarget',{'targetId':target});wait('!document.hidden&&document.querySelector("#tour-host").dataset.visibility==="visible"');rpc('Target.closeTarget',{'targetId':other});settled()
  def lose():
   evaluate('window.__step7Loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__step7Loss.loseContext()');wait('document.querySelector("#tour-host").dataset.renderState==="context-lost"')
  def restore():
   evaluate('window.__step7Loss.restoreContext()');wait('!document.querySelector("canvas").getContext("webgl2").isContextLost()')
  def close_project():
   native_click('.tour-project-close');wait('document.querySelector("#tour-host").dataset.overlayState==="closed"');settled()
  wait('document.querySelector("#tour-host")?.dataset.renderState==="ready"&&!document.hidden');assert 'STEP 07'in evaluate('document.title')
  # Initial renderer readiness can precede coalesced layout restoration.
  # Match the original native harness: wait for fonts and two real frames first.
  settled()
  go(10.05);wait('document.querySelector(".experiment-cover img").complete&&document.querySelector(".experiment-cover img").naturalWidth>0')
  before=state();pic=image('native-C2-before-hide.png');other=hide();time.sleep(.35);show(other)
  assert state()==before and ImageChops.difference(pic,image('native-C2-after-show.png')).getbbox()is None
  record('C2 real hidden/return keeps exact paused time, story, layout and pixels',{'actualDocumentHiddenObserved':True,'sameState':before,'pixelsExact':True})
  go(9.42);before=state();pic=image('native-C-descent-before-loss.png');lose();restore();wait('document.querySelector("#tour-host").dataset.renderState==="ready"');settled()
  assert state()==before and ImageChops.difference(pic,image('native-C-descent-after-loss.png')).getbbox()is None
  record('context restore during C descent retains exact story and pixels',{'h':9.42,'state':before,'pixelsExact':True})
  go(10.05);native_click('[data-project-tab=live]');wait('document.querySelector(".tour-project-dialog")?.open&&document.querySelector("#tour-host").dataset.projectView==="live"');settled()
  native_click('.tour-project-motion');wait('document.querySelector("#tour-host").dataset.motionState==="running"&&Number(document.querySelector("#tour-host").dataset.sceneTime)>2.05')
  h=evaluate('document.querySelector("#tour-host").dataset.displayH');other=hide();hidden_time=evaluate('document.querySelector("#tour-host").dataset.sceneTime');time.sleep(.4)
  assert evaluate('document.querySelector("#tour-host").dataset.sceneTime')==hidden_time
  show(other);wait('Number(document.querySelector("#tour-host").dataset.sceneTime)>'+hidden_time)
  assert evaluate('document.querySelector(".tour-project-dialog").open&&document.querySelector("#tour-host").dataset.projectView==="live"&&document.querySelector("#tour-host").dataset.displayH==='+json.dumps(h))
  native_click('.tour-project-motion');wait('document.querySelector("#tour-host").dataset.motionState==="paused"')
  record('live actual tab hide freezes environment, return resumes latest play choice',{'actualDocumentHiddenObserved':True,'timeWhileHidden':hidden_time,'readingHFrozen':h,'dialogAndLiveTabRetained':True})
  before=state();pic=image('native-live-before-loss.png');lose();assert evaluate('document.querySelector("[data-project-mode=native]").disabled&&document.querySelector(".tour-project-motion").disabled&&!document.querySelector(".tour-project-close").disabled')
  restore();wait('document.querySelector("#tour-host").dataset.renderState==="ready"');settled();assert state()==before and ImageChops.difference(pic,image('native-live-after-loss.png')).getbbox()is None
  record('live context restore keeps tab, camera and pixels while close remains available',{'pixelsExact':True,'tab':'live','sceneControlsDisabledDuringLoss':True,'closeEnabled':True})
  native_click('[data-project-view=archive]');wait('document.querySelector("#tour-host").dataset.projectView==="archive"');native_click('.tour-project-play');wait('document.querySelector("video")?.currentTime>.15&&!document.querySelector("video").paused')
  scene_time=evaluate('document.querySelector("#tour-host").dataset.sceneTime');other=hide();wait('document.querySelector("video").paused');paused=evaluate('document.querySelector("video").currentTime');time.sleep(.25);show(other);time.sleep(.3)
  assert evaluate('document.querySelector("video").paused')and abs(evaluate('document.querySelector("video").currentTime')-paused)<.05
  assert evaluate('document.querySelector("#tour-host").dataset.sceneTime')==scene_time
  record('archive actual video hides paused and remains paused on return',{'actualDocumentHiddenObserved':True,'videoPausedAt':paused,'staysPausedOnReturn':True,'backgroundTimeFrozen':scene_time,'usesRealProjectClip':True})
  lose();assert evaluate('document.querySelector(".tour-project-dialog").open&&document.querySelector("#tour-host").dataset.projectView==="archive"')
  restore();wait('!document.querySelector("[data-project-mode=native]").disabled');assert evaluate('document.querySelector("#tour-host").dataset.projectView==="archive"&&document.querySelector("video").paused')
  close_project();wait('document.querySelector("#tour-host").dataset.renderState==="ready"');assert evaluate('document.querySelectorAll("video").length===0&&Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.003')
  record('archive context restore preserves tab/video pause and close releases decoder',{'archiveTabPreserved':True,'videoRemainsPaused':True,'decoderReleased':True,'returnedH':10.05})
  native_click('[data-project-tab=live]');wait('document.querySelector("#tour-host").dataset.projectView==="live"');lose();close_project();assert abs(float(evaluate('document.querySelector("#tour-host").dataset.displayH'))-10.05)<.003
  restore();wait('document.querySelector("#tour-host").dataset.renderState==="ready"');settled();assert evaluate('document.querySelector("#tour-host").dataset.projectView==="closed"&&document.querySelectorAll("dialog[open]").length===0')
  record('close during active context loss returns to original station without deadlock',{'closedWhileLost':True,'restoredH':10.05,'dialogClosedAfterRestore':True})
  exceptions=[e['params']for e in events if e.get('method')=='Runtime.exceptionThrown'];assert not exceptions,exceptions
  diagnostics=[e['params']for e in events if e.get('method')=='Runtime.consoleAPICalled'and e.get('params',{}).get('type')in ['warning','error']]
  (OUT/'native-recovery.json').write_text(json.dumps({'engine':'native headed Chromium, Linux Xvfb/SwiftShader; direct CDP','method':'real Target.activateTarget; no document.hidden overrides or synthetic visibility events','checks':results,'unhandledExceptions':exceptions,'intentionalContextLossConsoleDiagnostics':diagnostics,'hardwareFPSProof':False,'passed':True},ensure_ascii=False,indent=2)+'\n')
  print('Seven native visibility/context recovery groups passed.',flush=True)
 finally:
  if socket:
   try:rpc('Browser.close')
   except Exception:pass
   socket.close()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  for attempt in range(20):
   try:shutil.rmtree(profile);break
   except FileNotFoundError:break
   except OSError:
    if attempt==19:raise
    time.sleep(.1)
