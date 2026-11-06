"""Measure the actual material's white contribution in a test-only depth render."""
from playwright.sync_api import sync_playwright
from step9_common import *
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2')
 result=page.evaluate('async()=>(await import("/tests/scroll-garden/inspect_orb.js")).orbHighlightCoverage()')
 save('highlight-coverage.json',result)
 assert all(10<=s['whiteDominantPercent']<=20 for s in result['samples']),result
 print('PASS: visible white-dominant highlight percentages',[(s['time'],s['pose'],round(s['whiteDominantPercent'],2))for s in result['samples']],flush=True);b.close()
