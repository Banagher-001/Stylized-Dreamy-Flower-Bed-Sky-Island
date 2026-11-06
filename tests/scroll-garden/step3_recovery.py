"""Native Chromium tabs via CDP: no Playwright focus/visibility emulation."""
from pathlib import Path
from io import BytesIO
import base64,json,subprocess,tempfile,time
from PIL import Image,ImageChops
from websockets.sync.client import connect

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-3'
def luminance(rgb):
 v=[x/255 for x in rgb];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
 return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))

with tempfile.TemporaryDirectory(prefix='pillar-reading-native-') as profile:
 process=subprocess.Popen(['/usr/bin/chromium','--no-sandbox','--disable-background-networking','--disable-breakpad','--no-first-run','--no-default-browser-check','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1','--user-data-dir='+profile,'--window-size=1440,1000','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
    if time.monotonic()>deadline:raise RuntimeError('Timed out: '+expression)
    time.sleep(.05)
  wait('document.querySelector("#tour-host")?.dataset.renderState==="ready"&&!document.hidden')
  def go(h):
   evaluate(f'scrollTo({{top:{h}/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"}})')
   wait(f'(()=>{{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-{h})<.003}})()')
  def state():return evaluate('(()=>{const d=document.querySelector("#tour-host").dataset;return {position:d.cameraPosition,target:d.cameraTarget,height:d.viewHeight,station:d.readingStation,opacity:d.readingOpacity,phase:d.readingPhase,time:d.sceneTime}})()')
  def image(name):
   evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   bounds=evaluate('(()=>{const r=document.querySelector("canvas").getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})()')
   raw=base64.b64decode(rpc('Page.captureScreenshot',{'format':'png','clip':bounds,'captureBeyondViewport':False},session)['data']);(OUT/name).write_bytes(raw)
   return Image.open(BytesIO(raw)).convert('RGB')
  go(2.54);before=state();picture=image('native-before-hide.png')
  other=rpc('Target.createTarget',{'url':'about:blank','newWindow':False})['targetId'];rpc('Target.activateTarget',{'targetId':other})
  wait('document.hidden&&document.querySelector("#tour-host").dataset.visibility==="hidden"');time.sleep(.5)
  rpc('Target.activateTarget',{'targetId':target});wait('!document.hidden&&document.querySelector("#tour-host").dataset.visibility==="visible"')
  assert state()==before and ImageChops.difference(picture,image('native-after-show.png')).getbbox()is None
  rpc('Target.closeTarget',{'targetId':other})
  visibility={'method':'native Chromium Target.activateTarget through direct CDP, without Playwright attachment','realTabSwitch':True,'documentHiddenObserved':True,'poseAndParagraphExact':True,'pausedTimeExact':True,'pixelsExact':True}
  go(2.08);before=state();picture=image('native-before-loss.png')
  evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()');wait('document.querySelector("#tour-host").dataset.renderState==="context-lost"')
  evaluate('window.__loss.restoreContext()');wait('document.querySelector("#tour-host").dataset.renderState==="ready"')
  assert state()==before and ImageChops.difference(picture,image('native-after-loss.png')).getbbox()is None
  descending={'h':2.08,'stateExact':True,'pixelsExact':True,'state':before}
  go(2.54);styles=evaluate('(()=>{const e=document.querySelector(".pillar-reading");return {background:getComputedStyle(e).backgroundColor,body:getComputedStyle(e.querySelector("[data-reading-station=A2] .pillar-reading-body")).color,title:getComputedStyle(e.querySelector("[data-reading-station=A2] h2")).color,opacity:getComputedStyle(e).opacity}})()')
  def rgb(s):return [int(x)for x in s.removeprefix('rgb(').removesuffix(')').split(',')]
  bg=luminance(rgb(styles['background']));ratios={n:(max(bg,luminance(rgb(styles[n])))+.05)/(min(bg,luminance(rgb(styles[n])))+.05)for n in ['body','title']}
  exceptions=[e['params']for e in events if e.get('method')=='Runtime.exceptionThrown'];assert styles['opacity']=='1'and min(ratios.values())>=4.5 and not exceptions
  (OUT/'recovery-contrast.json').write_text(json.dumps({'engine':'native headed Chromium on software Xvfb; direct CDP','visibility':visibility,'descendingContextRestore':descending,'fullReadContrast':{'computedStyles':styles,'ratios':ratios,'opaqueBackground':True,'condition':'full read only; transitional opacity excluded'},'unhandledExceptions':exceptions},ensure_ascii=False,indent=2)+'\n')
  print('Native tab hide/return, descending context restore and full-read contrast passed.',flush=True)
 finally:
  if socket:socket.close()
  process.terminate()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:process.kill();process.wait()
