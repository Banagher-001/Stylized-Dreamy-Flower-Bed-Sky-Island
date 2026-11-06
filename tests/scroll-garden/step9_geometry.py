"""Actual orb shape, clearance, independent trajectories and pixel visibility."""
from playwright.sync_api import sync_playwright
from step9_common import *
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2');aspects=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  resize(page,w,h);aspects.append({'viewport':[w,h],'aspect':float(data(page)['aspect']),'sampleWidth':float(page.locator('canvas').get_attribute('data-sample-width'))})
 result=page.evaluate('async aspects=>(await import("/tests/scroll-garden/inspect_orb.js")).inspectOrb(aspects)',aspects);save('geometry-physics.json',result);print('PASS:',result['geometrySamples'],'shape samples;pedestalgap',result['minPedestalGap'],'dropclearance',result['minOrbDropClearance'],'flightpoints',result['flightSamples'],'pixel diameters',[(x['pose'],round(x['minSamplePixelDiameter'],2))for x in result['frames']],flush=True);b.close()
