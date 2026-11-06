from pathlib import Path
from io import BytesIO
import json,time,gzip
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/step-9';runs=[];issues=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for i in range(3):
  c=b.new_context(viewport={'width':1440,'height':1000});q=c.new_page();q.on('pageerror',lambda e:issues.append(str(e)));q.on('console',lambda m:issues.append(m.text)if m.type in('warning','error')else None)
  cdp=c.new_cdp_session(q);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':93750,'connectionType':'cellular4g'})
  resources=[];q.on('response',lambda r:resources.append({'url':r.url.split('/')[-1],'status':r.status,'encoding':r.headers.get('content-encoding'),'cache':r.headers.get('cache-control'),'length':r.headers.get('content-length')}))
  start=time.monotonic();q.goto('http://127.0.0.1:4174/?waterTime=2',wait_until='domcontentloaded');q.wait_for_selector('#scene-host[data-render-state="ready"]');q.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');visible=time.monotonic()-start
  q.get_by_role('button',name='正常画面',exact=True).click();q.wait_for_function("document.querySelector('canvas').dataset.renderMode==='native'");interactive=time.monotonic()-start
  im=Image.open(BytesIO(q.locator('canvas').screenshot())).convert('RGB');assert len(im.getcolors(1000000))>32
  runs.append({'run':i+1,'sceneVisibleSeconds':visible,'firstModeSwitchSeconds':interactive,'resources':resources,'encodedResponseBodyBytes':sum(int(r['length']or 0)for r in resources),'canvasColors':len(im.getcolors(1000000))});print(json.dumps(runs[-1]),flush=True);c.close()
 b.close()
assets={str(p.relative_to(ROOT/'dist')):{'rawBytes':p.stat().st_size,'gzipBytes':len(gzip.compress(p.read_bytes()))}for p in(ROOT/'dist').rglob('*')if p.is_file()}
result={'network':{'downloadMbps':1.6,'latencyMs':150,'uploadMbps':.75,'browserHTTPCache':'disabled, new context each run','transportCompression':'real Content-Encoding:gzip from loopback production server','CPU':'cloud software rendering, no artificial CPU throttle'},'runs':runs,'assets':assets,'rawTotalBytes':sum(v['rawBytes']for v in assets.values()),'gzipTotalBytes':sum(v['gzipBytes']for v in assets.values()),'maxMeasuredEncodedBodyBytes':max(r['encodedResponseBodyBytes']for r in runs),'sceneVisibleWithin5s':all(r['sceneVisibleSeconds']<=5 for r in runs),'interactiveWithin5s':all(r['firstModeSwitchSeconds']<=5 for r in runs),'issues':issues}
assert not issues and result['gzipTotalBytes']<=200000
(OUT/'network-and-size.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['runs','assets']},indent=2),flush=True)
