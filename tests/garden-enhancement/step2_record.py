"""Original-time demonstration of actual wheel input across the first pillar."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time
from playwright.sync_api import sync_playwright
from step2_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:4177')
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-2')
args = parser.parse_args()
OUT = args.out.resolve()
build = json.loads((OUT / 'build-verification.json').read_text())

def metadata(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_name,width,height', '-of', 'json', str(path)], text=True))

actions, errors = [], []
with sync_playwright() as p:
    browser = launch(p)
    version = browser.version
    with tempfile.TemporaryDirectory(prefix='garden-enhancement-step2-video-') as temporary:
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1,
            record_video_dir=temporary, record_video_size={'width': 1440, 'height': 900})
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        started = time.monotonic()
        load(page, args.url + '/?waterTime=2')
        def stamp(label):
            frames(page)
            actions.append({'label': label, 'elapsedWallSeconds': time.monotonic() - started,
                'scrollY': page.evaluate('scrollY'), 'scene': data(page), 'background': about(page)})
            page.wait_for_timeout(650)
            print(label, flush=True)
        def wheel_to(h):
            for _ in range(100):
                target = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)', h)
                delta = target - page.evaluate('scrollY')
                if abs(delta) < 1.25:
                    break
                page.mouse.move(1120, 350)
                page.mouse.wheel(0, max(-90, min(90, delta)))
                page.wait_for_timeout(75)
            else:
                raise AssertionError('Native wheel did not reach destination.')
            page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}', arg=h)
        page.locator('#tour-stop-about').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-1.74)<.003')
        stamp('A1 identity, pixel, complete feather')
        wheel_to(2.54)
        stamp('native forward wheel to A2 experience')
        wheel_to(3.34)
        stamp('native forward wheel to A3 practice')
        wheel_to(2.54)
        stamp('native reverse wheel to A2')
        page.locator('.tour-actions [data-mode=native]').click()
        stamp('native render mode, same reading and environment time')
        wheel_to(1.74)
        stamp('native reverse wheel to A1')
        assert not errors, errors
        video = page.video
        context.close()
        raw = Path(temporary) / 'about.webm'
        video.save_as(str(raw))
        target = OUT / 'about-feather-demo.mp4'
        subprocess.run(['ffmpeg', '-y', '-i', str(raw), '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        original, output = metadata(raw), metadata(target)
        assert abs(float(original['format']['duration']) - float(output['format']['duration'])) < .12
    browser.close()
save(OUT, 'about-feather-recording.json', {'passed': True, 'candidateId': build['candidateId'],
    'browser': version, 'file': target.name, 'viewport': [1440, 900], 'DPR': 1,
    'method': 'actual chapter/render buttons and bounded native wheel forward/reverse; original time, no speedup, no synthetic animation; this is manual browsing, automatic tour remains unimplemented',
    'actions': actions, 'originalMetadata': original, 'outputMetadata': output,
    'exceptions': errors, 'hardwareFPSProof': False, 'physicalDevice': False})
print('PASS original-time about demo', output['format']['duration'], 'seconds', flush=True)
