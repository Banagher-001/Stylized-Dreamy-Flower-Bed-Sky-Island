from pathlib import Path
import os,json,hashlib,traceback,shutil,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];B=Path(__file__).parent;run=B/(sys.argv[1] if len(sys.argv)>1 else 'final-hit-testing');run.mkdir(exist_ok=False);s=json.loads((B/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
(run/'source-manifest.json').write_text(json.dumps([{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],indent=2)+'\n');shutil.copy2(__file__,run/'verify-hit-testing.py.txt')
report={'checks':[],'complete':False,'errors':[]}
with sync_playwright() as play:
 br=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 for id in ['midjourney','vibe-coding']:
  ctx=br.new_context(viewport={'width':1440,'height':900});p=ctx.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));entry={'id':id,'status':'失败'}
  try:
   p.goto(s['origin']+'/?waterTime=2');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackMode==="program"');p.wait_for_timeout(1200);p.locator('[data-action=auto]').click()
   if id=='vibe-coding':p.locator('[data-action=previous]').click()
   button=p.locator(f'.ar-tool-card[data-tool-id={id}] button');hit=button.evaluate('e=>{const r=e.getBoundingClientRect(),a=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {correct:a===e||e.contains(a),target:a.tagName,action:a.dataset.action}}');assert hit['correct'],hit
   button.click();p.wait_for_timeout(500);assert button.get_attribute('aria-expanded')=='true';assert button.evaluate('e=>e===document.activeElement');p.screenshot(path=str(run/(id+'.png')));entry.update(status='通过',hit=hit,expanded=True,focusPreserved=True)
  except Exception as e:entry.update(error=str(e),traceback=traceback.format_exc())
  finally:ctx.close();report['checks'].append(entry)
 br.close();report['browserClosed']=True;report['complete']=all(c['status']=='通过' for c in report['checks']) and not report['errors']
(run/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['complete'] else 1)
