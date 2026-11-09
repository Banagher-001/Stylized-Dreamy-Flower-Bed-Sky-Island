"""Original-time actual full guide and native takeover/resume demonstrations.
No speed-up, artificial time injection, automatic work opening or fake footage.
"""
import argparse,json,subprocess,tempfile,time
from playwright.sync_api import sync_playwright
from step4_common import *

parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['full','takeover'],required=True);args=parser.parse_args()
build=json.loads((OUT/'build-verification.json').read_text());errors=[];actions=[]
TRACE=r'''(()=>{
 window.__guideTrace=[];
 const attach=()=>{const h=document.querySelector('#tour-host');if(!h)return false;let last='';
 const read=()=>{const d=h.dataset,key=[d.guidePhase,d.guideStation,d.guideReadyAt,d.guideState].join('|');if(key===last)return;last=key;
 const a=document.querySelector('article[data-flow-anchor="'+d.guideStation+'"]');
 window.__guideTrace.push({at:performance.now(),y:scrollY,guide:{...d},text:a?.innerText??'',article:a?{hidden:a.hidden,inert:a.inert,aria:a.getAttribute('aria-hidden')}:null});};
 new MutationObserver(read).observe(h,{attributes:true,attributeFilter:['data-guide-phase','data-guide-station','data-guide-state','data-guide-ready-at']});return true;};
 if(!attach()){const observer=new MutationObserver(()=>{if(attach())observer.disconnect()});observer.observe(document,{childList:true,subtree:true});}
})()'''
def metadata(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(path)],text=True))

with sync_playwright()as p:
    browser=launch(p)
    with tempfile.TemporaryDirectory(prefix='garden-step4-video-')as temporary:
        context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,record_video_dir=temporary,record_video_size={'width':1440,'height':900})
        context.add_init_script(probe);context.add_init_script(TRACE)
        page=context.new_page();watch(page,errors);wall_start=time.monotonic()
        load(page,'http://127.0.0.1:4177/'+(''if args.kind=='full'else'?waterTime=2'))
        def stamp(label):
            frames(page);row={'label':label,'wallSeconds':time.monotonic()-wall_start,'at':page.evaluate('performance.now()'),'y':page.evaluate('scrollY'),'guide':guide_data(page),'scene':data(page)};actions.append(row);print(args.kind,label,row['guide']['guideStation'],row['guide']['guidePhase'],flush=True)
        def wheel_to(h):
            for _ in range(140):
                target=page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)',h);delta=target-page.evaluate('scrollY')
                if abs(delta)<1.25:break
                page.mouse.move(1100,350);page.mouse.wheel(0,max(-140,min(140,delta)));page.wait_for_timeout(75)
            else:raise AssertionError('Native wheel did not arrive')
            page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
        if args.kind=='full':
            assert data(page)['guidePhase']=='manual';page.mouse.move(1260,49);page.locator('#tour-guide').click();page.mouse.move(10,450)
            stamp('explicit start from opening; environment remains playing')
            seen=set();deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                current=guide_data(page)
                if current['guidePhase']=='reading'and current['guideStation']not in seen:
                    seen.add(current['guideStation']);stamp('complete reading '+current['guideStation']);page.screenshot(path=str(OUT/f'full-tour-{current["guideStation"]}.png'))
                if current['guidePhase']=='finished':break
                assert current['guidePhase']not in ['paused','manual'],current
                assert current['guideState']!='blocked',current
                page.wait_for_timeout(120)
            else:raise AssertionError('Full real-time guide did not finish')
            page.wait_for_timeout(1400);stamp('finished naturally; no loop or automatic return')
            expected=['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99'];assert set(expected)==seen
            assert abs(float(data(page)['displayH'])-12.3)<.003 and page.locator('#tour-guide').inner_text()=='重新导览'
        else:
            page.locator('#tour-stop-about').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');wheel_to(2.54)
            guide_start(page);stamp('start at A2 with environment deliberately paused');page.wait_for_timeout(1200)
            page.mouse.move(1100,350);page.mouse.wheel(0,-160);manual_stays(page);stamp('actual reverse wheel takes over; no pullback')
            wheel_to(3.34);stamp('manual forward wheel to a new station A3')
            guide_start(page);stamp('explicit continue from actual A3, not old A2');page.wait_for_timeout(900)
            held=data(page)['guideDeadline'];page.locator('.tour-actions [data-mode=native]').click();page.locator('#tour-motion').click();page.wait_for_timeout(1200)
            assert data(page)['guideDeadline']==held and data(page)['guidePhase']=='reading';stamp('mode and environment settings retain current guide hold')
            page.locator('#tour-guide').click();t=float(data(page)['sceneTime']);page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>t+.1',arg=t);stamp('stop guide; water continues latest play choice')
            page.locator('#tour-motion').click();quiet=still(page);stamp('both stopped; native scene is quiet')
        trace=page.evaluate('window.__guideTrace');assert not errors,errors
        if args.kind=='full':
            reads=[r for r in trace if r['guide'].get('guidePhase')=='reading'];ids=[r['guide']['guideStation']for r in reads]
            assert ids==['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99'],ids
            for read in reads:
                d=read['guide'];assert float(d['guideDeadline'])-float(d['guideReadyAt'])>=float(d['guideReadSeconds'])*1000-.001
                if read['article']:assert not read['article']['hidden']and not read['article']['inert']and read['article']['aria']=='false'
        video=page.video;context.close();raw=Path(temporary)/'original.webm';video.save_as(str(raw));target=OUT/f'auto-guide-{args.kind}.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        original,output=metadata(raw),metadata(target);assert abs(float(original['format']['duration'])-float(output['format']['duration']))<.12
    save(OUT,f'auto-guide-recording-{args.kind}.json',{'passed':True,'candidateId':build['candidateId'],'file':target.name,'browser':browser.version,'viewport':[1440,900],'DPR':1,'kind':args.kind,
        'method':'actual production page and native controls; original-time capture andH264 conversion without speedup/time injection; full guide runs real original minimum holds; takeover clip uses actual bounded native wheel and controls; not hardware FPS proof',
        'actions':actions,'actualMutationTrace':trace,'originalMetadata':original,'outputMetadata':output,'errors':errors,'physicalDevice':False})
    print('PASS original-time',args.kind,output['format']['duration'],'seconds',flush=True);browser.close()
