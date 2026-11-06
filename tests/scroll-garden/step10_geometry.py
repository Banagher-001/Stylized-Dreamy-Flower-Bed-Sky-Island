from playwright.sync_api import sync_playwright
from step10_common import *
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2');aspects=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:resize(page,w,h);aspects.append(page.locator('#tour-host').evaluate('e=>{const r=e.getBoundingClientRect();return r.width/r.height}'))
 baseline=json.loads((OUT/'baseline-before.json').read_text())['views']
 result=page.evaluate('async args=>(await import("/tests/scroll-garden/inspect_journey.js")).inspectJourney(...args)',[aspects,baseline]);save('geometry-continuity.json',result)
 print('PASS:',result['geometricSamples'],'camera samples; clearance',result['minimumClearance'],'max jump',result['maximumJump'],'derivative difference',result['maximumDerivativeDifference'],'fixed views',len(result['protectedViews']),flush=True);b.close()
