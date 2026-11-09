"""Original-time normal overview and near-cycle/water/control demonstrations.
No benchmark hooks, forced uniforms, altered clock or video speed changes.
The second clip explicitly uses the existing initial waterTime URL near a loop.
"""
import argparse,json,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step5_common import *

parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['overview','loop-water'],required=True);args=parser.parse_args()
build=json.loads((OUT/'build-verification.json').read_text());errors=[];actions=[]
def metadata(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(path)],text=True))
with sync_playwright()as p:
    browser=launch(p)
    with tempfile.TemporaryDirectory(prefix='garden-step5-video-')as temporary:
        context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,record_video_dir=temporary,record_video_size={'width':1440,'height':900})
        context.add_init_script(probe);page=context.new_page();watch(page,errors);wall=time.monotonic()
        load(page,'http://127.0.0.1:4179/'+(''if args.kind=='overview'else'?waterTime=144'))
        def stamp(label,shot=False):
            frames(page);row={'label':label,'wallSeconds':time.monotonic()-wall,'performanceNow':page.evaluate('performance.now()'),'guide':guide_data(page),'scene':data(page)};actions.append(row)
            if shot:page.screenshot(path=str(OUT/f'record-{args.kind}-{len(actions):02d}.png'))
            print(args.kind,label,'environment',row['scene']['sceneTime'],'wall',round(row['wallSeconds'],2),flush=True)
        def until_scene(t):
            deadline=time.monotonic()+600
            while float(data(page)['sceneTime'])<t:
                assert time.monotonic()<deadline,'Original environment did not progress'
                assert data(page)['motionState']=='running'
                page.wait_for_timeout(150)
        if args.kind=='overview':
            assert data(page)['motionState']=='running'and data(page)['guideState']=='manual'
            assert json.loads(data(page)['cloudShadows'])['enabled']
            stamp('normal root: original environment playing, guide default manual',True)
            end=max(64,float(actions[0]['scene']['sceneTime'])+62)
            for t in [10,18,32,48,end]:
                until_scene(t);stamp(f'actual original environment reaches {t} seconds',True)
            pause(page);frozen=still(page);page.wait_for_timeout(900);stamp('explicit pause freezes cloud and whole environment',True)
            assert data(page)['sceneTime']==frozen['time']
            assert float(actions[-2]['scene']['sceneTime'])-float(actions[0]['scene']['sceneTime'])>60
        else:
            assert float(data(page)['sceneTime'])==144
            stamp('explicit initial URL time144, paused near cloud repeat145.4545; no time acceleration',True)
            playing(page);until_scene(145.46);stamp('actual normal playback crosses cloud cycle boundary',True)
            until_scene(149);pause(page);stamp('pause after boundary; shape and position remain continuous',True)
            held=data(page)['sceneTime'];page.locator('#tour-stop-water').click()
            page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            page.locator('.tour-actions [data-mode=native]').click();frames(page)
            assert data(page)['sceneTime']==held
            stamp('manual original navigation to water and normal mode; cloud time retained',True)
            playing(page);until_scene(float(held)+6);stamp('water closeup, actual cloud and orb movement',True)
            guide_start(page);assert data(page)['guideStation']=='W'
            deadline=data(page)['guideDeadline'];pause(page);quiet=still(page)
            assert data(page)['guideDeadline']==deadline and data(page)['guidePhase']=='reading'
            stamp('guide reading continues with environment explicitly paused',True)
            page.mouse.move(1100,350);page.mouse.wheel(0,120);manual_stays(page)
            stamp('real native wheel interrupts guide; frozen clouds stay in world',True)
            t=data(page)['sceneTime'];guide_start(page,reading=False)
            page.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="S99"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=30000)
            assert data(page)['sceneTime']==t;guide_stop(page);stamp('explicit continue from new position to ending with environment still frozen',True)
        assert not errors,errors
        video=page.video;context.close();original=Path(temporary)/'original.webm';video.save_as(str(original))
        target=OUT/f'clouds-{args.kind}.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(original),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        source_metadata,output_metadata=metadata(original),metadata(target)
        assert abs(float(source_metadata['format']['duration'])-float(output_metadata['format']['duration']))<.12
    save(OUT,f'clouds-recording-{args.kind}.json',{'passed':True,'candidateId':build['candidateId'],'kind':args.kind,'file':target.name,'browser':browser.version,'viewport':[1440,900],'DPR':1,
        'method':'actual production page and original environment/controller time; overview normal default root covers full garden crossing; loop-water begins with existing explicit initial waterTime144 URL then uses original real play/pause, mode, native navigation/wheel and guide controls; original-duration H264 conversion only, no speedup or interpolation; passive draw/scroll observation only, no forced shader/uniform or benchmark clock controls',
        'actions':actions,'originalMetadata':source_metadata,'outputMetadata':output_metadata,'errors':errors,'hardwareFPSProof':False,'physicalDevice':False})
    browser.close();print('PASS original-time',args.kind,output_metadata['format']['duration'],'seconds',flush=True)
