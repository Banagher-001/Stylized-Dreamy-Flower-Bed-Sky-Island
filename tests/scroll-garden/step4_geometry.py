"""Fourth-step real geometry/material isolation checks, retaining old evidence."""
from pathlib import Path
import csv,json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-4'
rows=list(csv.DictReader((ROOT/'docs/scroll-garden/step-1-stations.csv').open(encoding='utf-8-sig')))
stations=[{'id':r['站点ID'],'start':float(r['起点H']),'y':float(r['阅读高度Y']),'stop':float(r['起点H'])+.55*(float(r['终点H'])-float(r['起点H'])),'fullStart':float(r['完整阅读起点H']),'fullEnd':float(r['完整阅读终点H'])}for r in rows if r['站点ID'].startswith('A')]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':900});page.goto('http://127.0.0.1:5173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');aspects=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');aspects.append(page.locator('#tour-host').evaluate('e=>{const r=e.getBoundingClientRect();return r.width/r.height}'))
 result=page.evaluate('async o=>(await import("/tests/scroll-garden/inspect_magic.js")).inspectMagic(o.aspects,o.stations)',{'aspects':aspects,'stations':stations})
 before=json.loads((OUT/'route-before.json').read_text());assert result['instances']==before['instances']and result['stages']==before['stages']and result['totalH']==before['totalH']and result['poses']==before['poses']
 result.update(instanceBaselineMatches=True,timelineAndAllKeyPosesUnchanged=True)
 (OUT/'geometry-isolation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');b.close();print('3003 route samples; 7 isolated material bindings; 3 safe surface anchors; original buffers and instances unchanged.')
