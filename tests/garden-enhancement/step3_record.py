"""Matched before/after original-time water-orb demos. No scene time injection
after load, no speed-up, no replacement assets, no automatic camera tour.
"""
import argparse
import json
import subprocess
import tempfile
import time
from playwright.sync_api import sync_playwright
from step3_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['before', 'after'], required=True)
args = parser.parse_args()
port = 4176 if args.phase == 'before' else 4177
identity = json.loads((OUT / ('baseline-version.json' if args.phase == 'before' else 'build-verification.json')).read_text())['candidateId']
actions, errors = [], []

def metadata(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(path)],text=True))

with sync_playwright() as p:
    browser = launch(p)
    with tempfile.TemporaryDirectory(prefix='garden-step3-video-') as temporary:
        context = browser.new_context(viewport={'width':1440,'height':900}, device_scale_factor=1,
            record_video_dir=temporary, record_video_size={'width':1440,'height':900})
        context.add_init_script(probe)
        page = context.new_page()
        watch(page, errors)
        wallStart = time.monotonic()
        load(page, f'http://127.0.0.1:{port}/?waterTime=2')
        def stamp(label):
            frames(page)
            actions.append({'label':label,'wallSeconds':time.monotonic()-wallStart,'scene':data(page)})
            print(args.phase,label,actions[-1]['scene']['sceneTime'],flush=True)
        def view_play(label, minimum_sim=7.4, minimum_wall=8.0):
            start=float(data(page)['sceneTime']);begin=time.monotonic()
            page.locator('#tour-motion').click()
            stamp(label+' play start')
            page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>=t',arg=start+minimum_sim,timeout=90000)
            remaining=minimum_wall-(time.monotonic()-begin)
            if remaining>0:page.wait_for_timeout(remaining*1000)
            page.locator('#tour-motion').click()
            stamp(label+' play end / paused')
            assert float(data(page)['sceneTime'])>=start+minimum_sim
            still(page)
        page.locator('#tour-stop-water').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-11.5)<.003')
        page.locator('.tour-actions [data-mode=native]').click()
        stamp('W original native view, frozen t2')
        page.wait_for_timeout(800)
        view_play('W native')
        frozen=data(page)['sceneTime']
        page.locator('.tour-actions [data-mode=pixel]').click()
        stamp('W pixel mode at same paused time')
        assert data(page)['sceneTime']==frozen
        still(page)
        view_play('W pixel')
        page.locator('#tour-stop-overview').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&Number(document.querySelector("#tour-host").dataset.displayH)<.003')
        view_play('O default pixel overview',minimum_sim=2,minimum_wall=3)
        page.locator('#tour-stop-experiments').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-9.14)<.003')
        # This short native wheel action moves to C2; it is manual browsing.
        target=page.evaluate('10.05/12.3*(document.documentElement.scrollHeight-innerHeight)')
        while abs(target-page.evaluate('scrollY'))>1.25:
            delta=max(-140,min(140,target-page.evaluate('scrollY')))
            page.mouse.move(1090,330);page.mouse.wheel(0,delta);page.wait_for_timeout(75)
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.003')
        page.locator('[data-project-tab=live]').click()
        page.locator('[data-project-mode=native]').click()
        live_start=float(data(page)['sceneTime']);live_wall=time.monotonic()
        page.locator('.tour-project-motion').click()
        stamp('C2 live native, one original canvas')
        page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>=t+2',arg=live_start,timeout=60000)
        remaining=3-(time.monotonic()-live_wall)
        if remaining>0:page.wait_for_timeout(remaining*1000)
        page.locator('.tour-project-motion').click()
        stamp('C2 live paused')
        assert page.locator('canvas').count()==1 and not errors
        video=page.video
        context.close()
        raw=Path(temporary)/'orb.webm';video.save_as(str(raw))
        target=OUT/f'water-orb-{args.phase}.mp4'
        subprocess.run(['ffmpeg','-y','-i',str(raw),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        original,output=metadata(raw),metadata(target)
        assert abs(float(original['format']['duration'])-float(output['format']['duration']))<.12
    save(OUT,f'water-orb-recording-{args.phase}.json',{'passed':True,'candidateId':identity,'phase':args.phase,
        'file':target.name,'browser':browser.version,'viewport':[1440,900],'DPR':1,
        'method':'actual production app and controls; fixed initial t2; W native and pixel each >=7.4 simulation seconds and >=8 wall seconds; O and C2 live representatives; manual navigation/wheel only; original-time H264, no speedup or fake animation; automatic tour remains unimplemented',
        'actions':actions,'originalMetadata':original,'outputMetadata':output,'errors':errors,'hardwareFPSProof':False})
    print('PASS',args.phase,'original-time demo',output['format']['duration'],'seconds',flush=True)
    browser.close()
