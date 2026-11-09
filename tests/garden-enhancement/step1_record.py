"""Record the existing orb, using actual viewer controls and original time.

Run after standalone latency sampling. Needs Playwright browser video support,
ffmpeg/ffprobe and the sibling historical browser helpers. No app changes.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/scroll-garden'))
from step11_common import PROBE, launch, ready, go, frames, data

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:4176')
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-1')
args = parser.parse_args()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
version = json.loads((OUT / 'baseline-version.json').read_text())

def metadata(file):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_name,width,height', '-of', 'json', str(file)], text=True))

actions, errors = [], []
with sync_playwright() as p:
    browser = launch(p)
    browser_version = browser.version
    with tempfile.TemporaryDirectory(prefix='garden-step1-record-') as temporary:
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1,
            record_video_dir=temporary, record_video_size={'width': 1440, 'height': 900})
        context.add_init_script(PROBE)
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        started = time.monotonic()
        def stamp(label):
            frames(page)
            actions.append({'label': label, 'elapsedWallSeconds': time.monotonic() - started,
                'scene': data(page), 'scrollY': page.evaluate('scrollY')})
            print(label, flush=True)
        ready(page, args.url.rstrip('/') + '/?waterTime=2&render=native')
        page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"')
        page.locator('#tour-stop-water').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled" && Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-11.5)<.003')
        stamp('current W view, native, paused time2')
        page.wait_for_timeout(800)
        page.locator('#tour-motion').click()
        page.wait_for_timeout(2400)
        stamp('native current orb playing; no new surface effect implemented')
        page.locator('.tour-actions [data-mode=pixel]').click()
        page.wait_for_timeout(2400)
        stamp('pixel384 current orb playing; same environment clock')
        assert float(data(page)['sceneTime']) > 2.1
        page.locator('#tour-motion').click()
        page.wait_for_timeout(300)
        paused = data(page)['sceneTime']
        stamp('explicit environment pause')
        page.wait_for_timeout(1000)
        assert data(page)['sceneTime'] == paused
        stamp('paused time remains identical')
        assert not errors, errors
        video = page.video
        context.close()
        raw = Path(temporary) / 'orb-baseline.webm'
        video.save_as(str(raw))
        output = OUT / 'water-orb-baseline.mp4'
        subprocess.run(['ffmpeg', '-y', '-i', str(raw), '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raw_meta, output_meta = metadata(raw), metadata(output)
        assert abs(float(raw_meta['format']['duration']) - float(output_meta['format']['duration'])) < .12
    browser.close()
report = {'passed': True, 'gitCommit': version['gitCommit'], 'applicationCandidateId': version['applicationCandidateId'],
    'sourceArchiveSha256': version['sourceArchiveSha256'], 'browser': browser_version,
    'file': output.name, 'viewport': [1440, 900], 'DPR': 1,
    'method': 'Actual water chapter / environment play-pause / render-mode button clicks in extracted baseline. Original time, no speedup, no synthetic animation.',
    'originalMetadata': raw_meta, 'outputMetadata': output_meta, 'actions': actions,
    'physicalDevice': False, 'hardwareFPSProof': False, 'newOrbEffectImplemented': False, 'exceptions': errors}
(OUT / 'water-orb-recording.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('PASS original-time orb baseline', output_meta['format']['duration'], 'seconds', flush=True)
