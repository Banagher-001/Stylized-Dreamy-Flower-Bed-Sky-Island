"""Third-step scene inspection using the approved first-step station CSV."""
from pathlib import Path
import argparse, csv, json, os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/scroll-garden-step-3'
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:5173');args=parser.parse_args()
rows=list(csv.DictReader((ROOT/'docs/scroll-garden/step-1-stations.csv').open(encoding='utf-8-sig')))
stations=[{'id':r['站点ID'],'y':float(r['阅读高度Y']),'stop':float(r['起点H'])+.55*(float(r['终点H'])-float(r['起点H'])),'fullStart':float(r['完整阅读起点H']),'fullEnd':float(r['完整阅读终点H'])}for r in rows if r['站点ID'].startswith('A')]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1440,'height':900});page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 aspects=[]
 for width,height in [(1440,900),(1366,768),(390,844)]:
  page.set_viewport_size({'width':width,'height':height})
  page.wait_for_function('()=>{const h=document.querySelector("#tour-host"),r=h.getBoundingClientRect();return Math.abs(Number(h.dataset.aspect)-r.width/r.height)<.00001}')
  aspects.append(page.locator('#tour-host').evaluate('e=>{const r=e.getBoundingClientRect();return r.width/r.height}'))
 result=page.evaluate('async o=>(await import("/tests/scroll-garden/inspect_reading.js")).inspectReading(o.aspects,o.stations)',{'aspects':aspects,'stations':stations})
 before=json.loads((OUT/'route-before.json').read_text())
 assert result['instances']==before['instances']
 assert result['stages']==before['stages'] and result['totalH']==before['totalH']
 for key in ['O','A','B','C','W']:assert result['poses'][key]==before['poses'][key]
 result.update(instanceBaselineMatches=True,timelineUnchanged=True,existingKeyPosesUnchanged=True,readingExpectationsSource='docs/scroll-garden/step-1-stations.csv')
 (OUT/'route-geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');b.close()
 print('Passed:',result['geometricSamples'],'route samples; 9 reading rays; 45 plateau samples; 1001 monotonic descent samples.')
