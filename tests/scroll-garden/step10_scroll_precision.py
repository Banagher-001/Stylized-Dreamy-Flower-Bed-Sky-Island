"""Observe rounded H reconstruction versus exact native scroll position in WebKit."""
from playwright.sync_api import sync_playwright
from step10_common import *
with sync_playwright()as p:
 b=launch(p,'webkit');page=b.new_page(viewport={'width':1440,'height':900});ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');rows=[]
 for h in [0,.35,.4,.45,.49,.5,.9,1.3,1.74,4.05,4.95,8.35,9.14,11.3,11.5,11.67,11.8,11.875,11.95,12.3]:
  go(page,h);frames(page);native=page.evaluate('scrollY');stored=float(data(page)['displayH']);alpha=float(page.locator('.tour-heading').get_attribute('data-opacity'));go(page,stored);frames(page);rounded={'y':page.evaluate('scrollY'),'h':data(page)['displayH'],'alpha':float(page.locator('.tour-heading').get_attribute('data-opacity'))}
  page.evaluate('y=>scrollTo({top:y,behavior:"instant"})',native);settled(page,stored);frames(page);restored={'y':page.evaluate('scrollY'),'h':data(page)['displayH'],'alpha':float(page.locator('.tour-heading').get_attribute('data-opacity'))}
  assert abs(restored['y']-native)<1e-7 and abs(restored['alpha']-alpha)<1e-6
  rows.append({'requestedH':h,'nativeY':native,'storedH':stored,'alpha':alpha,'viaRoundedH':rounded,'viaNativeY':restored})
 save('webkit-scroll-precision.json',{'passed':True,'method':'same actual physical scrollY must recover same UI; rounded seven-decimal diagnostic H is not a lossless native scroll coordinate','cases':rows,'roundedHChangesPixels':[r for r in rows if abs(r['viaRoundedH']['alpha']-r['alpha'])>=1e-6]});print('PASS: exact nativeY restores; rounded-H alpha changes',[(r['requestedH'],r['nativeY'],r['viaRoundedH']['y'])for r in rows if abs(r['viaRoundedH']['alpha']-r['alpha'])>=1e-6],flush=True);b.close()
