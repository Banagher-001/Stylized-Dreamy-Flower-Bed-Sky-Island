"""Original-time bird flight and user-control footage; no clock/pose overrides.
`birds=inspect` exposes passive state only and does not add engineering UI.
"""
import argparse,json,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step6_common import *

parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['overview','controls'],required=True);args=parser.parse_args()
build=json.loads((OUT/'build-verification.json').read_text());errors=[];actions=[];trace=[]
def metadata(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(path)],text=True))
def pose_only(state):return [{k:v for k,v in b.items()if k!='screen'}for b in state['poses']]
with sync_playwright()as p:
    browser=launch(p)
    with tempfile.TemporaryDirectory(prefix='garden-step6-video-')as temporary:
        context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,record_video_dir=temporary,record_video_size={'width':1440,'height':900})
        context.add_init_script(probe);page=context.new_page();watch(page,errors);wall=time.monotonic()
        load(page,'http://127.0.0.1:4181/?birds=inspect'+(''if args.kind=='overview'else'&waterTime=8'))
        def stamp(label,shot=True):
            frames(page);row={'label':label,'wallSeconds':time.monotonic()-wall,'performanceNow':page.evaluate('performance.now()'),'guide':guide_data(page),'scene':data(page)};actions.append(row)
            if shot:page.screenshot(path=str(OUT/f'record-{args.kind}-{len(actions):02d}.png'))
            print(args.kind,label,'environment',row['scene']['sceneTime'],'wall',round(row['wallSeconds'],2),flush=True)
        def sample():
            d=data(page);state=json.loads(d['birdState'])
            trace.append({'wallSeconds':time.monotonic()-wall,'time':state['time'],'visible':state['visible'],'birds':[{k:b[k]for k in ['id','phase','flap','leftWing','rightWing','bank']}for b in state['poses']]})
            return state
        def until_scene(target):
            deadline=time.monotonic()+600
            while float(data(page)['sceneTime'])<target:
                assert time.monotonic()<deadline and data(page)['motionState']=='running'
                sample();page.wait_for_timeout(180)
            sample()
        if args.kind=='overview':
            assert data(page)['motionState']=='running'and data(page)['guideState']=='manual'
            stamp('normal visitor overview; original environment running; guide manual')
            start=float(actions[0]['scene']['sceneTime']);sample()
            for target in [start+8,start+18,start+32,start+48,start+62.5]:
                until_scene(target);stamp(f'original environment reaches {target:.3f}; full real flight')
            pause(page);frozen=json.loads(data(page)['birdState']);quiet=still(page);page.wait_for_timeout(650)
            assert json.loads(data(page)['birdState'])==frozen
            stamp('explicit environment pause freezes all wing and world poses')
            assert float(actions[-2]['scene']['sceneTime'])-start>61
            cycles=[]
            for i in range(3):
                rows=[r['birds'][i]for r in trace]
                wraps=sum(abs(b['phase']-a['phase'])>.5 for a,b in zip(rows,rows[1:]))
                assert wraps>=1 and any(r['flap']>.8 for r in rows)and any(r['flap']==0 for r in rows)
                cycles.append({'bird':i,'actualPhaseWraps':wraps,'flapAndGlideObserved':True,'minWing':min(r['leftWing']for r in rows),'maxWing':max(r['leftWing']for r in rows)})
        else:
            cycles=[];stamp('explicit existing initial time8 URL; environment paused')
            initial=json.loads(data(page)['birdState']);playing(page);until_scene(13);pause(page);held=json.loads(data(page)['birdState']);still(page)
            assert pose_only(held)!=pose_only(initial)
            stamp('play then pause after actual wing and flight progression')
            page.locator('#tour-stop-about').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            assert pose_only(json.loads(data(page)['birdState']))==pose_only(held)
            stamp('original About navigation moves camera while bird world and wing poses stay frozen')
            guide_start(page);deadline=data(page)['guideDeadline'];page.locator('.tour-actions [data-mode=native]').click();frames(page)
            assert data(page)['guideDeadline']==deadline and pose_only(json.loads(data(page)['birdState']))==pose_only(held)
            stamp('guide running and normal mode selected; environment independently paused')
            playing(page);until_scene(float(held['time'])+2.5)
            page.mouse.move(1100,350);page.mouse.wheel(0,120);manual_stays(page)
            assert data(page)['motionState']=='running'
            stamp('real native wheel takes over guide; birds and environment keep playing')
            pause(page);held=json.loads(data(page)['birdState']);page.locator('#tour-stop-experiments').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            delta=page.evaluate('10.05/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
            page.mouse.move(1100,350);page.mouse.wheel(0,delta)
            page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.03&&document.querySelector("#tour-host").dataset.cameraState==="settled"')
            page.locator('[data-project-tab=live]').click();frames(page)
            assert page.locator('canvas').count()==1 and pose_only(json.loads(data(page)['birdState']))==pose_only(held)
            stamp('live project uses the same canvas and retained bird poses')
            page.locator('.tour-project-motion').click();until_scene(float(held['time'])+3)
            page.locator('.tour-project-motion').click();frames(page);held=json.loads(data(page)['birdState'])
            stamp('live pane play and pause continue the original flight timeline')
            page.locator('.tour-project-close').click();frames(page)
            assert pose_only(json.loads(data(page)['birdState']))==pose_only(held)
            page.locator('#tour-stop-water').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            playing(page);until_scene(float(held['time'])+4);pause(page)
            stamp('water closeup retains cloud and fluid motion with bird timeline continuous')
            page.locator('#tour-stop-overview').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            stamp('return to overview; explicit pause retained without a restart')
        assert not errors,errors
        video=page.video;context.close();original=Path(temporary)/'original.webm';video.save_as(str(original))
        target=OUT/f'birds-{args.kind}.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(original),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        source_metadata,output_metadata=metadata(original),metadata(target)
        assert abs(float(source_metadata['format']['duration'])-float(output_metadata['format']['duration']))<.12
    save(OUT,f'birds-recording-{args.kind}.json',{'passed':True,'candidateId':build['candidateId'],'kind':args.kind,'file':target.name,'browser':browser.version,'viewport':[1440,900],'DPR':1,
        'method':'actual production normal visitor UI; passive birds=inspect state only; original environment/controller clocks and input; full unmodified viewport; original-duration H264 conversion only; no speedup, interpolation, clock override or forced poses',
        'actions':actions,'flightTrace':trace,'cycles':cycles,'originalMetadata':source_metadata,'outputMetadata':output_metadata,'errors':errors,'hardwareFPSProof':False,'physicalDevice':False})
    browser.close();print('PASS original-time birds',args.kind,output_metadata['format']['duration'],'seconds',flush=True)
