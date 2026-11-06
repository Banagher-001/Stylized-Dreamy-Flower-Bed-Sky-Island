"""Real native-wheel C chapter recording, single-scene controls, archive clip and return."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step7_common import ROOT,OUT,launch,data,frames

with tempfile.TemporaryDirectory(prefix='step7-recording-') as temporary:
 with sync_playwright() as p:
  b=launch(p);context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=temporary,record_video_size={'width':1280,'height':800})
  page=context.new_page();errors=[];diagnostics=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
  page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');assert 'STEP 07'in page.title()
  page.mouse.move(1190,280);samples=[];actions=[];start=time.monotonic()
  def snapshot():
   return page.locator('#tour-host').evaluate('e=>({h:Number(e.dataset.displayH),station:e.dataset.experimentStation,phase:e.dataset.experimentPhase,sceneTime:Number(e.dataset.sceneTime),motion:e.dataset.motionState,project:e.dataset.projectView??"closed",cameraPosition:JSON.parse(e.dataset.cameraPosition),cameraTarget:JSON.parse(e.dataset.cameraTarget),viewHeight:Number(e.dataset.viewHeight),targetH:Number(e.dataset.targetH),nativeH:scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3,scrollY,scrollHeight:document.documentElement.scrollHeight,innerHeight,presentation:JSON.parse(e.dataset.experimentPresentation),renderMode:document.querySelector("canvas").dataset.renderMode,canvasCount:document.querySelectorAll("canvas").length})')
  def action(name):
   actions.append({'action':name,'wallSeconds':time.monotonic()-start,'actual':snapshot()});print('record action',name,flush=True)
  def wheel_to(target,hold):
   moves=[]
   for _ in range(200):
    current=page.evaluate('({y:scrollY,range:document.documentElement.scrollHeight-innerHeight})');distance=target/12.3*current['range']-current['y']
    if abs(distance)<1:break
    delta=max(-80,min(80,distance));page.mouse.wheel(0,delta);moves.append(delta)
    page.wait_for_function('y=>Math.abs(scrollY-y)>.05',arg=current['y']);page.wait_for_timeout(75)
   else:raise RuntimeError('Wheel did not reach '+str(target))
   page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=target);frames(page);page.wait_for_timeout(hold)
   state=snapshot();assert abs(state['h']-target)<.003,state
   samples.append({'requestedH':target,'actual':state,'wheelDeltas':moves,'wallSeconds':time.monotonic()-start});print('record target',target,'actual',state['h'],flush=True)
  for target,hold in [(7.64,450),(9.14,900),(9.42,500),(10.05,1000),(10.83,900),(11.5,600),(10.83,650),(10.05,650),(9.14,650),(10.05,800)]:wheel_to(target,hold)
  before=float(data(page)['displayH']);page.locator('[data-project-tab=live]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=live]');frames(page);page.wait_for_timeout(700);action('open actual live single-scene overview')
  page.locator('[data-project-mode=native]').click();page.wait_for_function('document.querySelector("canvas").dataset.renderMode==="native"');page.wait_for_timeout(600);action('switch actual scene to native')
  page.locator('[data-project-mode=pixel]').click();page.wait_for_function('document.querySelector("canvas").dataset.renderMode==="pixel"');page.wait_for_timeout(600);action('switch actual scene to pixel')
  scene_before=float(data(page)['sceneTime']);page.locator('.tour-project-motion').click();page.wait_for_function('document.querySelector("#tour-host").dataset.motionState==="running"');page.wait_for_timeout(1200);page.locator('.tour-project-motion').click();page.wait_for_function('document.querySelector("#tour-host").dataset.motionState==="paused"');assert float(data(page)['sceneTime'])>scene_before+.5;action('play and pause actual environment')
  assert float(data(page)['displayH'])==before and page.locator('canvas').count()==1
  page.locator('[data-project-view=archive]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]');page.wait_for_timeout(650);action('switch to version-labelled archive')
  page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.15&&!document.querySelector("video").paused');page.wait_for_timeout(1100)
  media=page.locator('video').evaluate('v=>({duration:v.duration,currentTime:v.currentTime,width:v.videoWidth,height:v.videoHeight,paused:v.paused})');assert media['currentTime']>1 and abs(media['duration']-12)<.1;action('play actual twelve-second fixed-view project clip')
  page.locator('.tour-project-close').click();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');frames(page);assert abs(float(data(page)['displayH'])-before)<.003 and page.locator('video').count()==0
  assert data(page)['motionState']=='paused'and page.locator('canvas').get_attribute('data-render-mode')=='pixel';page.mouse.move(1190,280);page.wait_for_timeout(900);action('return to original C2 with latest chosen settings')
  wall=time.monotonic()-start;assert not errors and not diagnostics,(errors,diagnostics)
  video=page.video;context.close();source=Path(temporary)/'interactive-reading-demo.webm';video.save_as(str(source));b.close()
  output=OUT/'interactive-reading-demo.mp4'
  subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(source),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  def metadata(path):return json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,avg_frame_rate','-of','json',str(path)],check=True,capture_output=True,text=True).stdout)
  (OUT/'demo-recording.json').write_text(json.dumps({'method':'actual native wheel input in both directions, followed by real live controls, actual archive playback and return; conversion preserves recorded timing','viewport':[1280,800],'initialEnvironmentTime':2,'wallSeconds':wall,'maximumAbsoluteWheelDelta':80,'samples':samples,'actions':actions,'archiveClip':media,'returnsToSameH':True,'latestExplicitSettingsPreserved':True,'singleCanvas':True,'output':'interactive-reading-demo.mp4','sourceRecordingMetadata':metadata(source),'outputMetadata':metadata(output),'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in (ROOT/'src/tour').glob('*')if f.suffix in ['.ts','.css']},'unhandledExceptions':errors,'browserDiagnostics':diagnostics,'hardwareFPSProof':False},ensure_ascii=False,indent=2)+'\n')
  print('Recorded',len(samples),'real wheel stops and',len(actions),'project actions; wall seconds',round(wall,2),flush=True)
