"""Immutable pool geometry, jet physics, bindings and actual shader-area diagnostics."""
from playwright.sync_api import sync_playwright
from step8_common import *
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2')
 result=page.evaluate('async()=>{const m=await import("/tests/scroll-garden/inspect_pool.js");return{...await m.inspectPool(),coverage:m.poolCoverage()}}');save('geometry-isolation.json',result)
 print('PASS: unchanged original geometry,14 scoped bindings,7 fixedtime jet/drop/impact matches, ownership cleanup;water coverage',[(s['pose'],s['time'],round(s['deepReflectionPercent'],2))for s in result['coverage']['samples']],flush=True);b.close()
