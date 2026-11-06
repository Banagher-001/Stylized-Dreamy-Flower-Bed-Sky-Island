"""Decoration-unavailable, font fallback, and shader-cache budget checks."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-4'
NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);results={};issues=[]
 for disabled in [True,False]:
  context=b.new_context(viewport={'width':1440,'height':900})
  if disabled:context.add_init_script(NO_2D)
  page=context.new_page();page.on('pageerror',lambda e:issues.append(str(e)));page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
  assert page.locator('#tour-host').get_attribute('data-magic-status')==('fallback'if disabled else'ready')
  page.evaluate('scrollTo({top:2.54/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');page.wait_for_function('document.querySelector("#tour-host").dataset.readingOpacity==="1.0000000"&&document.querySelector("#tour-host").dataset.stage==="A2"')
  frames=[]
  for mode in ['pixel','native','pixel']:
   page.get_by_role('button',name='像素预览'if mode=='pixel'else'正常画面',exact=True).click();page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');frames.append(json.loads(page.locator('#tour-host').get_attribute('data-renderer-stats')))
  if disabled:
   article=page.locator('.pillar-reading article[aria-hidden=false]');article.locator('h2').evaluate("e=>e.style.fontFamily=\"'Missing Inscription Font', serif\"");article.locator('.pillar-reading-body').evaluate("e=>e.style.fontFamily=\"'Missing Inscription Font', sans-serif\"");page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   assert '枫叶互动'in article.inner_text()and page.locator('.pillar-reading').get_attribute('data-fits')=='true';page.screenshot(path=str(OUT/'decoration-font-fallback.png'))
   page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动'in page.locator('#about').inner_text()
  results['decorationUnavailable'if disabled else'normal']={'frames':frames,'textReadable':True,'fontFallbackTested':disabled,'referenceLinkChecked':disabled,'referenceUsable':True if disabled else None}
  context.close()
 for normal,base in zip(results['normal']['frames'],results['decorationUnavailable']['frames']):
  assert normal['geometries']-base['geometries']<=3 and normal['textures']-base['textures']<=2 and normal['programs']-base['programs']<=3,(normal,base)
 assert not issues
 (OUT/'decoration-fallback.json').write_text(json.dumps({'checks':results,'unhandledExceptions':issues,'method':'disable Canvas2D only in test browser; WebGL and normal reading remain active; compare same-mode shader-cache budgets'},ensure_ascii=False,indent=2)+'\n');b.close();print('Decoration/font fallback, reference link and same-mode cached shader budgets passed.')
