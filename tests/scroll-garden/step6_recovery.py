"""Native Chromium tabs via CDP: no Playwright focus/visibility emulation."""
from pathlib import Path
from io import BytesIO
import base64,json,os,shutil,signal,subprocess,tempfile,time
from PIL import Image,ImageChops
from websockets.sync.client import connect

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-6'
def luminance(rgb):
 v=[x/255 for x in rgb];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
 return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))

with tempfile.TemporaryDirectory(prefix='pillar-reading-native-') as profile:
 process=subprocess.Popen(['/usr/bin/chromium','--no-sandbox','--disable-background-networking','--disable-breakpad','--no-first-run','--no-default-browser-check','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1','--user-data-dir='+profile,'--window-size=1440,1000','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 socket=None
 try:
  portfile=Path(profile)/'DevToolsActivePort';deadline=time.monotonic()+10
  while not portfile.exists():
   if process.poll()is not None or time.monotonic()>deadline:raise RuntimeError('Native browser failed to start')
   time.sleep(.05)
  port,path=portfile.read_text().splitlines()[:2];socket=connect('ws://127.0.0.1:'+port+path,max_size=16*1024*1024)
  counter=0;events=[]
  def rpc(method,params=None,session=None):
   global counter
   counter+=1;request={'id':counter,'method':method,'params':params or {}}
   if session:request['sessionId']=session
   socket.send(json.dumps(request))
   while True:
    reply=json.loads(socket.recv(timeout=15))
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
   deadline=time.monotonic()+10
   while not evaluate(expression):
    if time.monotonic()>deadline:
     (OUT/'native-timeout-diagnostics.json').write_text(json.dumps(evaluate('({hidden:document.hidden,y:scrollY,range:document.documentElement.scrollHeight-innerHeight,data:document.querySelector("#tour-host")?.dataset})'),ensure_ascii=False,indent=2)+'\n');raise RuntimeError('Timed out: '+expression)
    time.sleep(.05)
  wait('document.querySelector("#tour-host")?.dataset.renderState==="ready"&&!document.hidden')
  wait('(()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001})()')
  evaluate('document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
  def go(h):
   evaluate(f'scrollTo({{top:{h}/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"}})')
   wait(f'(()=>{{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-{h})<.003}})()')
  def state():return evaluate('(()=>{const d=document.querySelector("#tour-host").dataset;return {position:d.cameraPosition,target:d.cameraTarget,height:d.viewHeight,station:d.filmStation,phase:d.filmPhase,presentation:d.filmPresentation,magic:d.filmMagicFrame,time:d.sceneTime,text:document.querySelector(".film-reading article:not([hidden])")?.innerText}})()')
  def image(name):
   evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   bounds=evaluate('(()=>{const r=document.querySelector("canvas").getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})()')
   raw=base64.b64decode(rpc('Page.captureScreenshot',{'format':'png','clip':bounds,'captureBeyondViewport':False},session)['data']);(OUT/name).write_bytes(raw)
   return Image.open(BytesIO(raw)).convert('RGB')
  go(5.95);wait('[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.complete&&i.naturalWidth>0)');before=state();picture=image('native-before-hide.png')
  other=rpc('Target.createTarget',{'url':'about:blank','newWindow':False})['targetId'];rpc('Target.activateTarget',{'targetId':other})
  wait('document.hidden&&document.querySelector("#tour-host").dataset.visibility==="hidden"');time.sleep(.5)
  rpc('Target.activateTarget',{'targetId':target});wait('!document.hidden&&document.querySelector("#tour-host").dataset.visibility==="visible"')
  assert state()==before and ImageChops.difference(picture,image('native-after-show.png')).getbbox()is None
  rpc('Target.closeTarget',{'targetId':other})
  visibility={'method':'native Chromium Target.activateTarget through direct CDP, without Playwright attachment','realTabSwitch':True,'documentHiddenObserved':True,'poseAndParagraphExact':True,'pausedTimeExact':True,'pixelsExact':True}
  go(6.30);before=state();picture=image('native-before-loss.png')
  evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()');wait('document.querySelector("#tour-host").dataset.renderState==="context-lost"')
  evaluate('window.__loss.restoreContext()');wait('document.querySelector("#tour-host").dataset.renderState==="ready"')
  assert state()==before and ImageChops.difference(picture,image('native-after-loss.png')).getbbox()is None
  descending={'h':6.30,'stateExact':True,'pixelsExact':True,'state':before}
  # Real hidden state while the production image dialog is open.
  go(6.84)
  def native_click(selector):
   box=evaluate('(()=>{const r=document.querySelector('+json.dumps(selector)+').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
   rpc('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**box},session)
   rpc('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**box},session)
  native_click('[data-film-station=B3] button')
  wait('document.querySelector(".film-dialog")?.open&&document.querySelector(".film-dialog").dataset.state==="ready"')
  wait('[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.parentElement.dataset.imageState==="ready")')
  wait('(()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001})()')
  evaluate('document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
  modal_before=state();other=rpc('Target.createTarget',{'url':'about:blank','newWindow':False})['targetId'];rpc('Target.activateTarget',{'targetId':other});wait('document.hidden');time.sleep(.25)
  rpc('Target.activateTarget',{'targetId':target});wait('!document.hidden')
  modal_after=state();modal_flags=evaluate('({open:document.querySelector(".film-dialog").open,overlay:document.querySelector("#tour-host").dataset.overlayState,hidden:document.hidden,active:document.activeElement?.outerHTML})')
  (OUT/'native-modal-debug.json').write_text(json.dumps({'before':modal_before,'after':modal_after,'flags':modal_flags},ensure_ascii=False,indent=2)+'\n')
  assert modal_after==modal_before and modal_flags['open']and modal_flags['overlay']=='open',{'changes':{k:[v,modal_after[k]]for k,v in modal_before.items()if v!=modal_after[k]},'flags':modal_flags}
  native_click('.film-dialog-close');wait('document.querySelector("#tour-host").dataset.overlayState==="closed"');assert abs(evaluate('Number(document.querySelector("#tour-host").dataset.displayH)')-6.84)<.003;rpc('Target.closeTarget',{'targetId':other})
  modal_recovery={'actualHiddenObserved':True,'dialogRemainsOpenOnReturn':True,'timePoseAndPresentationExact':True,'closeRestoresH':6.84}
  # Same public media-viewer component with an isolated, clearly labelled clip.
  fixture=rpc('Target.createTarget',{'url':'http://127.0.0.1:5173/tests/scroll-garden/media-fixture.html','newWindow':False})['targetId']
  session=rpc('Target.attachToTarget',{'targetId':fixture,'flatten':True})['sessionId'];rpc('Runtime.enable',session=session);rpc('Page.enable',session=session);rpc('Target.activateTarget',{'targetId':fixture});wait('document.body?.dataset.fixtureReady==="true"&&!document.hidden')
  native_click('#fixture-open');wait('document.querySelector("video")?.currentTime>.15&&!document.querySelector("video").paused')
  other=rpc('Target.createTarget',{'url':'about:blank','newWindow':False})['targetId'];rpc('Target.activateTarget',{'targetId':other});wait('document.hidden&&document.querySelector("video").paused')
  paused_time=evaluate('document.querySelector("video").currentTime');rpc('Target.activateTarget',{'targetId':fixture});wait('!document.hidden');time.sleep(.3)
  assert evaluate('document.querySelector("video").paused')and abs(evaluate('document.querySelector("video").currentTime')-paused_time)<.05
  native_click('.film-dialog-close');wait('!document.querySelector("dialog").open&&document.querySelectorAll("video").length===0')
  rpc('Target.closeTarget',{'targetId':other})
  video_hidden={'mechanismOnly':True,'realFilmIntegrated':False,'actualHiddenObserved':True,'pausedOnHide':True,'remainsPausedOnReturn':True,'decoderRemovedOnClose':True,'fixture':'12-second silent courtyard test clip'}
  exceptions=[e['params']for e in events if e.get('method')=='Runtime.exceptionThrown'];assert not exceptions
  (OUT/'native-recovery.json').write_text(json.dumps({'engine':'native headed Chromium on software Xvfb; direct CDP','visibility':visibility,'descendingContextRestore':descending,'imageDialogTabRecovery':modal_recovery,'videoHiddenMechanism':video_hidden,'unhandledExceptions':exceptions},ensure_ascii=False,indent=2)+'\n')
  print('Native exhibition hide/return, descending recovery, covered image view and real video hide/pause passed.',flush=True)

 finally:
  if socket:
   try:rpc('Browser.close')
   except Exception:pass  # Chromium may close the CDP socket before replying.
   socket.close()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  # Only remove this run's owned profile after browser shutdown. Retry brief
  # child-process writes, and still fail if it cannot be cleaned up.
  for attempt in range(20):
   try:shutil.rmtree(profile);break
   except FileNotFoundError:break
   except OSError:
    if attempt==19:raise
    time.sleep(.1)
