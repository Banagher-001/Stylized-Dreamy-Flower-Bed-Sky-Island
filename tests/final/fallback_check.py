from pathlib import Path
import json
from playwright.sync_api import sync_playwright
out=(Path(__file__).resolve().parents[2]/'docs/evidence/step-9')
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-webgl']);q=b.new_page(viewport={'width':390,'height':844});diagnostics=[];exceptions=[]
 q.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in('warning','error')else None);q.on('pageerror',lambda e:exceptions.append(str(e)))
 q.goto('http://127.0.0.1:4174/',wait_until='networkidle');q.wait_for_selector('#scene-host[data-render-state="error"]');assert q.get_by_role('alert').is_visible()and q.locator('button:enabled').count()==0 and q.locator('canvas').count()==0
 message=q.get_by_role('alert').inner_text();assert '刷新'in message and not exceptions
 q.screenshot(path=str(out/'webgl-unavailable.png'),full_page=True);r={'method':'Chromium launched with --disable-webgl','message':message,'controlsDisabled':True,'remainingCanvas':0,'unhandledExceptions':exceptions,'expectedFailureDiagnostics':diagnostics,'passed':True};(out/'no-webgl-fallback.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2),flush=True);b.close()
