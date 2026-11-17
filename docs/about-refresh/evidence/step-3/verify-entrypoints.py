"""Development URL smoke check. Standalone HTTP is covered by the 49-case suite."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
record={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'directFileNavigation':'Not adopted: cloud browser blocks file:// with ERR_BLOCKED_BY_ADMINISTRATOR; see entrypoints-first.json','standaloneHTTPAcceptance':'matrix-1/browser.json'}
process=subprocess.Popen(['node',str(OUT/'serve-dev.mjs')],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
browser_closed=False
try:
 port=json.loads(process.stdout.readline())['port']
 record['server']={'pid':process.pid,'port':port,'scope':'Existing Vite config, isolated /dev/about-refresh/index.html'}
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  try:
   page=browser.new_page(viewport={'width':1440,'height':900})
   page.on('pageerror',lambda error:record['events'].append(str(error)))
   page.goto(f'http://127.0.0.1:{port}/dev/about-refresh/index.html',wait_until='networkidle');page.wait_for_function('!!window.__aboutRefreshPreview')
   page.locator('[data-preview-station=A3]').click();page.wait_for_timeout(120)
   page.locator('[data-category=G5]').click();page.wait_for_timeout(100)
   assert page.locator('.ar-tool-slot').count()==3
   page.locator('[data-action=all]').click();page.wait_for_timeout(100)
   assert page.locator('.ar-catalog .ar-tool-card').count()==22
   page.locator('.ar-all-tools [data-action=return]').first.click();page.wait_for_timeout(100)
   assert page.locator('.ar-tool-slot').count()==3
   assert page.locator('.ar-tools-browser').get_attribute('data-category')=='G5'
   record['checks'].append({'id':'development-entry','status':'通过','scenario':'A3 → G5/3 → all/22 → return/G5/3'})
   page.close();assert not record['events'],record['events'];record['complete']=True
  finally:browser.close();browser_closed=True
finally:
 process.terminate()
 try:process.wait(timeout=10)
 except subprocess.TimeoutExpired:process.kill();process.wait()
 record['serverExitCode']=process.returncode
 record['cleanup']={'ownDevServerClosed':process.poll() is not None,'browserClosed':browser_closed,'otherServicesStopped':False}
 record['serverStderr']=process.stderr.read()
 record['htmlSHA256']=hashlib.sha256((ROOT/'docs/about-refresh/step-3-preview.html').read_bytes()).hexdigest()
 (OUT/'entrypoints.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(record,ensure_ascii=False))
