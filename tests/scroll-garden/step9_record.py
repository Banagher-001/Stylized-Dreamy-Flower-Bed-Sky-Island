"""Actual orb playback/pause, both modes and native two-way wheel, original timing."""
import hashlib,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step9_common import *
FRAME_OBSERVER='''(()=>{
 window.__orbFrameGaps={pixel:[],native:[]};const raf=requestAnimationFrame.bind(window);let last,tag;
 window.requestAnimationFrame=callback=>raf(timestamp=>{
  const host=document.querySelector('#tour-host'),mode=document.querySelector('canvas')?.dataset.renderMode;
  if(host?.dataset.motionState==='running'&&!document.hidden&&(mode==='pixel'||mode==='native')){
   if(tag===mode&&last!==undefined&&timestamp!==last)window.__orbFrameGaps[mode].push(timestamp-last);
   tag=mode;last=timestamp;
  }else{last=undefined;tag=undefined;}
  callback(timestamp);
 });
})()'''
with tempfile.TemporaryDirectory(prefix='orb-demo-')as temporary:
 with sync_playwright()as p:
  b=launch(p);context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=temporary,record_video_size={'width':1280,'height':800});context.add_init_script(FRAME_OBSERVER);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');go(page,10.83);samples=[]
  def wheel(target):
   moves=[]
   for _ in range(120):
    pos=page.evaluate('({y:scrollY,range:document.documentElement.scrollHeight-innerHeight})');distance=target/12.3*pos['range']-pos['y']
    if abs(distance)<1:break
    dy=max(-65,min(65,distance));page.mouse.move(1150,270);page.mouse.wheel(0,dy);moves.append(dy);page.wait_for_function('y=>Math.abs(scrollY-y)>.05',arg=pos['y']);page.wait_for_timeout(75)
   else:raise RuntimeError('wheel target missed')
   page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=target);frames(page);samples.append({'targetH':target,'actualH':data(page)['displayH'],'wheelDeltas':moves})
  wheel(11.5);page.wait_for_timeout(700);before=data(page)['sceneTime'];page.bring_to_front();page.locator('#tour-motion').click();page.wait_for_timeout(8500);page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+5',arg=before,timeout=60000);page.locator('#tour-motion').click();after=data(page)['sceneTime'];assert float(after)>float(before)+5
  paused=data(page)['sceneTime'];page.wait_for_timeout(700);assert data(page)['sceneTime']==paused
  page.locator('.tour-actions [data-mode=native]').click();page.locator('#tour-motion').click();page.wait_for_timeout(3500);page.locator('#tour-motion').click();page.wait_for_timeout(650)
  wheel(10.83);page.wait_for_timeout(500);wheel(11.5);page.wait_for_timeout(900);assert data(page)['motionState']=='paused'and not errors
  gaps=page.evaluate('window.__orbFrameGaps');assert all(gaps.values())
  save('continuous-frame-diagnostics.json',{'method':'test observer wraps existing RAF callbacks, no additional RAF loop; deduplicate equal timestamps while actual environment is playing; software graphics with recording; not hardwareFPS','rawFrameIntervalsMs':gaps,'summary':{mode:{'count':len(values),'meanMs':sum(values)/len(values),'p95LowerMs':sorted(values)[int((len(values)-1)*.95)],'maxMs':max(values)}for mode,values in gaps.items()},'hardwareFPSProof':False})
  video=page.video;context.close();source=Path(temporary)/'orb.webm';video.save_as(str(source));b.close();output=OUT/'orb-motion-demo.mp4'
  subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(source),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  probe=lambda f:json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(f)],capture_output=True,text=True,check=True).stdout)
  save('demo-recording.json',{'method':'setup atC3, then actual bounded nativewheel C3→W, minimum8.5sec wall-time pixel playback, actual shared-clock advance>5, thenpause, real3.5sec native playback/pause, reverse C3 thenW; no speedup','viewport':[1280,800],'samples':samples,'environmentTimeBefore':before,'environmentTimeAfterPixelPlayback':after,'pausedTimeFixed':True,'sourceMetadata':probe(source),'outputMetadata':probe(output),'unhandledExceptions':errors,'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*.ts')},'hardwareFPSProof':False});print('Recorded actual orb demo',probe(output)['format']['duration'],flush=True)
