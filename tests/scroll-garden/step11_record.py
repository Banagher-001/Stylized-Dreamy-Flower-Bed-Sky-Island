"""Unaccelerated recordings of the actual mobile/stable/large-text browser interactions."""
import hashlib,subprocess,tempfile
from playwright.sync_api import sync_playwright
from step11_common import *
RUNTIME={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']}
recordings=[]
def metadata(file):return json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(file)],check=True,capture_output=True,text=True).stdout)
with sync_playwright()as p:
 b=launch(p)
 for name,size in [('mobile-reading-demo',(390,844)),('landscape-large-text-demo',(844,390))]:
  with tempfile.TemporaryDirectory(prefix='step11-record-')as temporary:
   context=b.new_context(viewport={'width':size[0],'height':size[1]},device_scale_factor=1,has_touch=True,is_mobile=True,record_video_dir=temporary,record_video_size={'width':size[0],'height':size[1]});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');actions=[]
   def stamp(label):
    frames(page);actions.append({'label':label,'y':page.evaluate('scrollY'),'layout':page.locator('main').get_attribute('data-reading-mode'),'anchor':page.locator('main').get_attribute('data-flow-anchor'),'scene':data(page)});page.wait_for_timeout(500);print(name,label,flush=True)
   def wheel_to(target):
    for _ in range(200):
     current=page.evaluate('scrollY');delta=target()-current
     if abs(delta)<1.5:break
     page.mouse.move(size[0]-25,min(310,size[1]-90));page.mouse.wheel(0,max(-90,min(90,delta)));page.wait_for_timeout(75)
    else:raise AssertionError('native wheel did not reach target')
    frames(page)
   def block(key):wheel_to(lambda:page.locator(f'.tour-reading-flow [data-flow-anchor={key}]').evaluate('e=>scrollY+e.getBoundingClientRect().top-document.querySelector(".tour-header").getBoundingClientRect().bottom-16'))
   stamp('opening')
   page.locator('#tour-stop-about').tap();frames(page)
   if size[0]==390:
    settled(page,1.74);stamp('immersive-A1')
    wheel_to(lambda:2.54/12.3*page.evaluate('document.documentElement.scrollHeight-innerHeight'));settled(page,2.54);stamp('native-wheel-A2')
    page.locator('#tour-layout-toggle').tap();stamp('stable-A2-same-reading')
   else:
    block('A2');stamp('landscape-A2')
    page.evaluate('document.documentElement.style.fontSize="200%"');page.wait_for_function('document.documentElement.classList.contains("tour-large-text")');page.wait_for_timeout(350);stamp('200percent-rem-text-A2-anchor-preserved')
    assert page.locator('main').get_attribute('data-flow-anchor')=='A2'
   page.locator('#tour-stop-films').tap();stamp('stable-film-B1')
   page.locator('[data-film-station=B1] button').tap();page.wait_for_selector('.film-dialog[data-state=ready]');stamp('complete-sample-image-source-labelled');page.locator('.film-dialog-close').tap();stamp('image-return')
   page.locator('#tour-stop-experiments').tap();stamp('stable-C1');block('C2');stamp('native-wheel-C2')
   page.locator('[data-project-tab=live]').tap();stamp('single-canvas-live')
   if size[0]==390:
    before=data(page)['sceneTime'];page.locator('.tour-project-motion').tap();page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+.2',arg=before);page.wait_for_timeout(1000);page.locator('[data-project-mode=native]').tap();stamp('live-native-playing');page.locator('.tour-project-motion').tap()
   page.locator('[data-project-view=archive]').tap();stamp('project-archive')
   if size[0]==390:
    page.locator('.tour-project-play').tap();page.wait_for_function('document.querySelector("video")?.currentTime>.15');page.wait_for_timeout(850);stamp('actual-early-version-video')
   page.locator('.tour-project-close').tap();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');stamp('project-return-C2');assert not page.locator('video').count()
   if size[0]==390:
    page.locator('#tour-layout-toggle').tap();settled(page,10.05);stamp('explicit-return-to-immersive-C2');page.locator('#tour-stop-water').tap();settled(page,11.5);stamp('water-original-scene')
   else:
    page.locator('#tour-stop-water').tap();stamp('large-text-water')
   page.locator('#tour-stop-overview').tap();stamp('return-opening');assert not errors and page.locator('canvas').count()==1
   video=page.video;context.close();raw=Path(temporary)/'record.webm';video.save_as(str(raw));output=OUT/(name+'.mp4')
   subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(raw),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   recordings.append({'name':name,'viewport':list(size),'method':'actual native taps and bounded native mouse-wheel movement; original time, no speedup','textScaleMethod':'200% root rem layout simulation, native browser zoom separately proved in native-zoom.json'if size[0]==844 else'normal text','actions':actions,'sourceMetadata':metadata(raw),'outputMetadata':metadata(output),'decoderReleased':True,'exceptions':errors})
 b.close()
assert RUNTIME=={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']}
save('demo-recording.json',{'passed':True,'recordings':recordings,'runtimeSourceSha256':RUNTIME,'hardwareFPSProof':False})
