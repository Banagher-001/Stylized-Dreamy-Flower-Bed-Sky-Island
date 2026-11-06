"""Actual complete native-wheel journey in both directions, modes and media replay."""
import ast,hashlib,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step10_common import *
tree=ast.parse((ROOT/'tests/scroll-garden/step9_record.py').read_text())
FRAME_OBSERVER=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='FRAME_OBSERVER'for t in n.targets))
with tempfile.TemporaryDirectory(prefix='journey-demo-')as temporary:
 with sync_playwright()as p:
  b=launch(p);context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=temporary,record_video_size={'width':1280,'height':800});context.add_init_script(FRAME_OBSERVER);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');samples=[];playback=[]
  def wheel(target,label):
   moves=[]
   for _ in range(240):
    pos=page.evaluate('({y:scrollY,range:document.documentElement.scrollHeight-innerHeight})');distance=target/12.3*pos['range']-pos['y']
    if abs(distance)<1:break
    dy=max(-80,min(80,distance));page.mouse.move(1140,280);page.mouse.wheel(0,dy);moves.append(dy);page.wait_for_function('y=>Math.abs(scrollY-y)>.05',arg=pos['y']);page.wait_for_timeout(75)
   else:raise RuntimeError('nativewheel target missed')
   settled(page,target);frames(page);page.wait_for_timeout(240);samples.append({'label':label,'targetH':target,'actualH':data(page)['displayH'],'camera':data(page)['cameraPosition'],'time':data(page)['sceneTime'],'deltasCssPixels':moves});print(label,target,flush=True)
  def play_pause(selector,seconds):
   page.bring_to_front();page.wait_for_function('!document.hidden');before=data(page)['sceneTime'];page.locator(selector).click();page.wait_for_timeout(int(seconds*1000));page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+.2',arg=before,timeout=60000);page.locator(selector).click();after=data(page)['sceneTime'];page.wait_for_timeout(300);assert data(page)['sceneTime']==after;playback.append({'mode':page.locator('canvas').get_attribute('data-render-mode'),'before':before,'after':after,'wallMinimumSeconds':seconds,'pauseExact':True})
  page.wait_for_timeout(700)
  for key,target in VIEWS[1:]:
   wheel(target,'forward-'+key)
   if key=='W':play_pause('#tour-motion',4)
  page.wait_for_timeout(650);assert page.locator('#tour-percent').inner_text()=='100%'
  page.locator('.tour-actions [data-mode=native]').click()
  for key,target in reversed(VIEWS[:-1]):
   wheel(target,'reverse-'+key)
   if key=='W':play_pause('#tour-motion',3)
  page.keyboard.press('End');settled(page,12.3);page.wait_for_timeout(400);page.locator('[data-tour-replay=films]').click();settled(page,4.95);page.wait_for_timeout(550)
  page.locator('#tour-stop-experiments').click();settled(page,9.14);wheel(10.05,'visit-C2');beforeProject=data(page)['displayH'];page.locator('[data-project-tab=live]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=live]');page.wait_for_timeout(500);page.locator('[data-project-mode=pixel]').click();play_pause('.tour-project-motion',2)
  page.locator('[data-project-view=archive]').click();page.wait_for_selector('.tour-project-dialog[data-tab=archive]');page.wait_for_timeout(500);page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.2&&!document.querySelector("video").paused');page.wait_for_timeout(700);metadata=page.locator('video').evaluate('v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,time:v.currentTime})');page.locator('.tour-project-close').click();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');settled(page,float(beforeProject));assert not page.locator('video').count()
  page.keyboard.press('End');settled(page,12.3);page.wait_for_timeout(550);page.locator('[data-tour-replay=overview]').click();settled(page,0);page.wait_for_timeout(750);assert page.locator('canvas').count()==1 and data(page)['motionState']=='paused'and not errors
  gaps=page.evaluate('window.__orbFrameGaps');assert all(gaps.values());save('continuous-frame-diagnostics.json',{'method':'wrap existing RAF callbacks only during actual environment playback; deduplicate timestamps; independent software recording diagnostics, not hardwareFPS','rawFrameIntervalsMs':gaps,'summary':{mode:{'count':len(v),'meanMs':sum(v)/len(v),'p95LowerMs':sorted(v)[int((len(v)-1)*.95)],'maxMs':max(v)}for mode,v in gaps.items()},'hardwareFPSProof':False})
  video=page.video;context.close();source=Path(temporary)/'journey.webm';video.save_as(str(source));b.close();output=OUT/'complete-journey-demo.mp4'
  subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(source),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  probe=lambda f:json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(f)],capture_output=True,text=True,check=True).stdout)
  save('demo-recording.json',{'method':'actual bounded80px nativewheel complete forward pixel and reverse native route, opening/ten stations/five transfers/water/ending, both ending actions, live play/pause/mode, real early archive clip and return; original wall time, no speedup','viewport':[1280,800],'samples':samples,'playback':playback,'archiveClipMetadata':metadata,'projectReturnedH':beforeProject,'decoderReleased':True,'sourceMetadata':probe(source),'outputMetadata':probe(output),'unhandledExceptions':errors,'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']},'hardwareFPSProof':False});print('Recorded full actual journey',probe(output)['format']['duration'],flush=True)
