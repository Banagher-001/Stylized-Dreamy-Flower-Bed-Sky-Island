"""Final original-time guide and ten-minute interaction/endurance footage.
No benchmark hooks, forced uniforms or modified product clocks. Stress-route
setup scrolls are labelled; manual takeover is actual native wheel input.
"""
import argparse,ast,json,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step7_common import *
parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['full','controls'],required=True);args=parser.parse_args()
build=json.loads((OUT/'build-verification.json').read_text());errors=[];actions=[];flight=[];endurance=None
tree=ast.parse((ROOT/'tests/garden-enhancement/step4_record.py').read_text())
TRACE=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TRACE'for t in n.targets))
def metadata(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(path)],text=True))
def poses(state):return [{k:v for k,v in b.items()if k!='screen'}for b in state['poses']]
def state(page):return json.loads(data(page)['birdState'])
with sync_playwright()as p:
    browser=launch(p)
    with tempfile.TemporaryDirectory(prefix='garden-final-video-')as temporary:
        context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,record_video_dir=temporary,record_video_size={'width':1440,'height':900})
        context.add_init_script(probe);context.add_init_script(TRACE);page=context.new_page();watch(page,errors);wall=time.monotonic()
        load(page,'http://127.0.0.1:4183/?birds=inspect'+(''if args.kind=='full'else'&waterTime=8'))
        def stamp(label,shot=False):
            frames(page);row={'label':label,'wallSeconds':time.monotonic()-wall,'at':page.evaluate('performance.now()'),'y':page.evaluate('scrollY'),'scene':data(page)};actions.append(row)
            if shot:page.screenshot(path=str(OUT/f'record-{args.kind}-{len(actions):02d}.png'))
            print(args.kind,label,'time',row['scene']['sceneTime'],'wall',round(row['wallSeconds'],1),flush=True)
        def sample():
            s=state(page);flight.append({'wallSeconds':time.monotonic()-wall,'time':s['time'],'visible':s['visible'],'birds':[{k:b[k]for k in ['id','phase','flap','leftWing','bank']}for b in s['poses']]});return s
        def until_scene(target):
            deadline=time.monotonic()+600
            while float(data(page)['sceneTime'])<target:
                assert time.monotonic()<deadline and data(page)['motionState']=='running';sample();page.wait_for_timeout(180)
            sample()
        def nav(selector):
            page.locator(selector).click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
        if args.kind=='full':
            assert data(page)['guidePhase']=='manual'and data(page)['motionState']=='running'
            page.locator('#tour-guide').click();page.mouse.move(10,450);stamp('explicit full guide start; original environment playing',True)
            seen=set();deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                d=data(page);sample()
                if d['guidePhase']=='reading'and d['guideStation']not in seen:
                    seen.add(d['guideStation']);stamp('complete reading '+d['guideStation']);page.screenshot(path=str(OUT/f'full-tour-{d["guideStation"]}.png'))
                if d['guidePhase']=='finished':break
                assert d['guidePhase']not in ['paused','manual']and d['guideState']!='blocked',d
                page.wait_for_timeout(180)
            else:raise AssertionError('Full guide did not naturally finish')
            page.wait_for_timeout(1400);stamp('finished naturally; no automatic loop',True)
            assert seen==set(['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99'])
            assert abs(float(data(page)['displayH'])-12.3)<.003 and page.locator('#tour-guide').inner_text()=='重新导览'
            pause(page)
        else:
            stamp('existing initial time8 URL; paused environment',True);initial=state(page)
            playing(page);until_scene(13);pause(page);held=state(page);still(page);assert poses(held)!=poses(initial)
            stamp('actual flight followed by explicit pause',True)
            nav('#tour-stop-about');assert poses(state(page))==poses(held);stamp('camera navigation retains frozen full bird pose',True)
            guide_start(page);deadline=data(page)['guideDeadline'];page.locator('.tour-actions [data-mode=native]').click();frames(page)
            assert data(page)['guideDeadline']==deadline and poses(state(page))==poses(held);stamp('guide and mode continue independently of paused environment')
            playing(page);until_scene(held['time']+2.5);page.mouse.move(1100,350);page.mouse.wheel(0,120);manual_stays(page)
            assert data(page)['motionState']=='running';stamp('real native wheel takes over guide; environment continues',True)
            pause(page);held=state(page);nav('#tour-stop-experiments')
            delta=page.evaluate('10.05/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY');page.mouse.move(1100,350);page.mouse.wheel(0,delta)
            page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.03&&document.querySelector("#tour-host").dataset.cameraState==="settled"')
            page.locator('[data-project-tab=live]').click();frames(page);assert page.locator('canvas').count()==1 and poses(state(page))==poses(held)
            stamp('live pane opened with same canvas and retained wing pose',True)
            page.locator('.tour-project-motion').click();until_scene(held['time']+3);page.locator('.tour-project-motion').click();frames(page);held=state(page)
            stamp('live pane real play and pause',True);page.locator('.tour-project-close').click();frames(page);assert poses(state(page))==poses(held)
            nav('#tour-stop-water');playing(page);until_scene(held['time']+4);pause(page);stamp('water closeup with original fluid/cloud timeline',True)
            nav('#tour-stop-overview')
            # Warm all resource variants before counting the endurance period.
            for mode in ['native','pixel']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for _,h in VIEWS:visit(page,h)
                visit(page,10.05);page.locator('[data-project-tab=live]').click();frames(page)
                for live_mode in ['native','pixel']:page.locator(f'[data-project-mode={live_mode}]').click();frames(page)
                page.locator('.tour-project-close').click();frames(page)
            visit(page,10.05);page.locator('[data-project-tab=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.15');page.locator('.tour-project-close').click();frames(page)
            nav('#tour-stop-overview');pause(page);quiet=still(page);warm=json.loads(data(page)['rendererStats']);playing(page)
            begin=time.monotonic();start_time=float(data(page)['sceneTime']);samples=[];cycles=[];last_log=begin
            def observe():
                s=sample();d=data(page);stats=json.loads(d['rendererStats'])
                assert all(stats[k]==warm[k]for k in ['geometries','textures','programs']),(warm,stats)
                samples.append({'elapsedWall':time.monotonic()-begin,'time':s['time'],'stats':{k:stats[k]for k in ['geometries','textures','programs','calls','triangles']},'guide':d['guideState'],'motion':d['motionState']})
            stamp('ten-minute endurance begins after full variant/media warmup',True)
            # Actual original-time overview spans at least a full cloud field
            # cycle before repeated setup visits can affect visibility.
            while time.monotonic()-begin<240 or float(data(page)['sceneTime'])-start_time<150:
                assert time.monotonic()-begin<900
                observe()
                if time.monotonic()-last_log>=15:print('endurance overview',round(time.monotonic()-begin,1),'wall',data(page)['sceneTime'],'environment',flush=True);last_log=time.monotonic()
                page.wait_for_timeout(500)
            cloud_end=float(data(page)['sceneTime']);stamp('continuous original overview passed150 environment seconds; cloud and all bird cycles covered',True)
            for index in range(20):
                # Setup via existing native scroll API is labelled automation;
                # start/stop, viewer and mode actions use original real buttons.
                guide_start(page,2.54);guide_stop(page)
                for mode in ['native','pixel']:page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
                visit(page,10.05);page.locator('[data-project-tab=live]').click();frames(page)
                for mode in ['native','pixel']:page.locator(f'[data-project-mode={mode}]').click();frames(page)
                assert page.locator('canvas').count()==1
                page.locator('.tour-project-close').click();frames(page)
                page.locator('[data-project-tab=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.15')
                page.locator('.tour-project-close').click();frames(page);assert page.locator('video').count()==0
                nav('#tour-stop-overview');playing(page);observe();cycles.append(samples[-1]);print('endurance cycle',index+1,'resources stable',flush=True)
                if index%5==4:stamp(f'endurance completed{index+1} real interaction cycles',True)
            while time.monotonic()-begin<600:
                observe()
                if time.monotonic()-last_log>=15:print('endurance final overview',round(time.monotonic()-begin,1),'wall',flush=True);last_log=time.monotonic()
                page.wait_for_timeout(500)
            elapsed=time.monotonic()-begin;pause(page);frozen=state(page);quiet_end=still(page);page.wait_for_timeout(650);assert state(page)==frozen
            stamp('ten minutes complete; paused environment and wings retain exact state',True)
            cycle_rows=[]
            for i in range(3):
                rows=[r['birds'][i]for r in flight];wraps=sum(abs(b['phase']-a['phase'])>.5 for a,b in zip(rows,rows[1:]))
                assert wraps>=1 and any(r['flap']>.8 for r in rows)and any(r['flap']==0 for r in rows)
                cycle_rows.append({'bird':i,'observedPhaseWraps':wraps,'flapAndGlide':True})
            endurance={'passed':True,'candidateId':build['candidateId'],'wallSeconds':elapsed,'minimumWallSeconds':600,'continuousOverviewEnvironmentSpan':cloud_end-start_time,
                'cloudCycleSeconds':32/.22,'interactionCycles':len(cycles),'warmResources':warm,'samples':samples,'cycleSamples':cycles,'birdCycles':cycle_rows,
                'quietBefore':quiet,'quietAfter':quiet_end,'actualFinalFrozenBirdState':frozen,'method':'actual original clocks and native buttons;10min real-duration run after complete warmup; first continuous overview spans150environment seconds; repeated-route setup uses existing scroll API explicitly, not claimed trusted user input; no clock acceleration','hardwareFPSProof':False}
            save(OUT,'endurance.json',endurance)
        trace=page.evaluate('window.__guideTrace');assert not errors,errors
        if args.kind=='full':
            reads=[r for r in trace if r['guide'].get('guidePhase')=='reading'];assert[r['guide']['guideStation']for r in reads]==['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99']
            for r in reads:
                d=r['guide'];assert float(d['guideDeadline'])-float(d['guideReadyAt'])>=float(d['guideReadSeconds'])*1000-.001
                if r['article']:assert not r['article']['hidden']and not r['article']['inert']and r['article']['aria']=='false'
        video=page.video;context.close();raw=Path(temporary)/'original.webm';video.save_as(str(raw));target=OUT/('final-guide.mp4'if args.kind=='full'else'final-controls.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        original,output=metadata(raw),metadata(target);assert abs(float(original['format']['duration'])-float(output['format']['duration']))<.12
    save(OUT,f'recording-{args.kind}.json',{'passed':True,'candidateId':build['candidateId'],'kind':args.kind,'file':target.name,'browser':browser.version,'viewport':[1440,900],'DPR':1,
        'method':'actual production normal UI and original environment/controller time; passive birds=inspect only; unmodified full1440x900 capture; H264 conversion with original duration; no benchmark timing/forced shaders/poses; stress-route setup scrolls explicitly labelled',
        'actions':actions,'actualMutationTrace':trace,'flightTrace':flight,'originalMetadata':original,'outputMetadata':output,'errors':errors,'physicalDevice':False,'hardwareFPSProof':False})
    browser.close();print('PASS final original-time',args.kind,output['format']['duration'],'seconds',flush=True)
