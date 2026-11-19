"""Verify the project window at 200% using Chromium's native zoom shortcut."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from playwright.sync_api import sync_playwright

from layout import WINDOW, align_window, choice, geometry, same_stage, tab, two_columns


def verify(page, origin, out):
    page.goto(origin, wait_until='domcontentloaded')
    page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"', timeout=90000)
    original = page.evaluate('() => ({width:innerWidth,dpr:devicePixelRatio})')
    keyboard = shutil.which('xdotool') or '/workspace/.cache/browser-deps/root/usr/bin/xdotool'
    window = subprocess.check_output([keyboard,'search','--onlyvisible','--class','chromium'], text=True).splitlines()[-1]
    subprocess.run([keyboard,'windowfocus','--sync',window,'key','--repeat','5','--delay','160','ctrl+equal'], check=True)
    page.wait_for_function('d=>Math.abs(devicePixelRatio/d-2)<.02', arg=original['dpr'], timeout=12000)
    page.wait_for_function('document.querySelector("main")?.dataset.readingMode==="stable"')
    align_window(page)
    choice(page,'lawson')
    before = geometry(page)
    two_columns(page)
    tab(page,'bottle-ocean').click()
    choice(page,'bottle-ocean')
    after = geometry(page)
    assert after['mode']=='stable' and after['overflow'] <= 1
    assert abs(after['viewport'][0]*2-original['width']) <= 3
    two_columns(page)
    same_stage(before,after)
    page.locator(WINDOW).evaluate('e=>e.scrollIntoView({block:"start",behavior:"instant"})')
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    subprocess.run(['import','-silent','-window',hex(int(window)),str(out/'browser-zoom-200.png')], check=True)
    page.locator('[data-project-tab="archive"]').click()
    page.wait_for_function('''() => {const d=document.querySelector('.tour-project-dialog');
      return d.open&&d.dataset.projectId==='bottle-ocean'&&d.dataset.tab==='archive'}''')
    page.locator('.tour-project-close').click()
    return {'beforeZoom':original,'zoom':page.evaluate('devicePixelRatio')/original['dpr'],
            'window':after,'archiveReached':True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--env-file',type=Path,required=True)
    parser.add_argument('--build-record',type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, executable_path=shutil.which('chromium'),
            args=['--no-sandbox','--disable-translate','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--window-size=1652,1010'])
        try:
            page = browser.new_context(no_viewport=True).new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            result = verify(page,args.origin,args.out)
            assert not errors, errors
            result.update(candidateId=json.loads(args.build_record.read_text())['candidateId'],engine=browser.version,complete=True)
            (args.out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print({'zoom':result['zoom'],'archiveReached':True},flush=True)
        finally:
            browser.close()
