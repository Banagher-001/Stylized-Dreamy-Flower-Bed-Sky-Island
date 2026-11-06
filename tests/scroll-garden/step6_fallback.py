"""Decoration/font/no-WebGL fallback and real image failures, isolated from normal diagnostics."""
from pathlib import Path
from io import BytesIO
from types import SimpleNamespace
import ast,json,math
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-6';args=SimpleNamespace(engine='font-fallback')
s=(ROOT/'tests/scroll-garden/step5_browser.py').read_text();n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name=='contrast');exec(compile(ast.get_source_segment(s,n).replace('.pillar-reading','.film-reading').replace('data-reading-ink','data-film-ink'),'<contrast>','exec'))
NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""
def go(page,h):page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def frames(page):page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);results={};font_views=[];errors=[]
 for disabled in [True,False]:
  context=b.new_context(viewport={'width':1440,'height':900})
  if disabled:context.add_init_script(NO_2D)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');assert page.locator('#tour-host').get_attribute('data-film-magic-status')==('fallback'if disabled else'ready')
  for h in [1.74,3.34,4.95,5.95,6.84,7.64]:go(page,h)
  frames_by_mode=[]
  for mode in ['pixel','native','pixel']:
   page.get_by_role('button',name='像素预览'if mode=='pixel'else'正常画面',exact=True).click();frames(page);frames_by_mode.append(json.loads(page.locator('#tour-host').get_attribute('data-renderer-stats')))
  if disabled:
   for width,height in [(1440,900),(1366,768),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}')
    for key,h in [('B1',4.95),('B2',5.95),('B3',6.84),('B4',7.64)]:
     go(page,h);page.wait_for_function('()=>[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.complete&&i.naturalWidth>0)');a=page.locator('.film-reading article:not([hidden])');a.locator('h2').evaluate("e=>e.style.fontFamily=\"'Missing Film Font', serif\"");a.locator('.film-body').evaluate("e=>e.style.fontFamily=\"'Missing Film Font', serif\"");frames(page)
     assert page.locator('.film-reading').get_attribute('data-fits')=='true';assert a.locator('h2,[data-film-ink]').evaluate_all('es=>es.every(e=>{const p=e.closest(".film-reading").getBoundingClientRect(),r=e.getBoundingClientRect();return r.left>=p.left+10&&r.right<=p.right-10&&r.top>=p.top+10&&r.bottom<=p.bottom-10})')
     page.mouse.move(10,height/2);page.screenshot(path=str(OUT/f'font-fallback-{width}-{key}.png'));font_views.append({'viewport':[width,height],'station':key,'fits':True,'contrast':contrast(page,f'{width}-{key}')})
   page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动'in page.locator('#about').inner_text()
  results['decorationUnavailable'if disabled else'normal']={'frames':frames_by_mode,'textAndReferencePass':True,'fontFallbackTested':disabled};context.close()
 assert not errors
 (OUT/'decoration-fallback.json').write_text(json.dumps({'checks':results,'fontFallbackViews':font_views,'unhandledExceptions':errors,'mechanism':'Canvas2D disabled only in test, both pillars; 12 real font fallback layouts'},ensure_ascii=False,indent=2)+'\n');b.close();print('Twelve decoration/font fallback layouts and shader caches passed.',flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-webgl']);page=b.new_page(viewport={'width':1280,'height':800});errors=[];diagnostics=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
 page.goto('http://127.0.0.1:4173/?tour=prototype',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="error"]');assert page.get_by_role('alert').inner_text()and page.locator('canvas').count()==0
 assert page.locator('[data-stop]:disabled,[data-reading-stop]:disabled,.mode-controls button:disabled,#tour-motion:disabled').count()==15
 assert page.locator('.film-reading').get_attribute('aria-hidden')=='true'and page.locator('.pillar-reading').get_attribute('aria-hidden')=='true'
 page.screenshot(path=str(OUT/'no-webgl.png'));page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动'in page.locator('#about').inner_text()and not errors
 (OUT/'fallback.json').write_text(json.dumps({'noWebGL':True,'readableAlert':True,'disabledGraphControls':15,'bothReadingLayersHidden':True,'referenceUsable':True,'unhandledExceptions':errors,'expectedInitializationDiagnostics':diagnostics},ensure_ascii=False,indent=2)+'\n');b.close();print('No-WebGL fallback and reference link passed.',flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':390,'height':844});errors=[];diagnostics=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
 page.route('**/signal-garden-*.webp',lambda route:route.abort());page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');go(page,5.95);page.wait_for_selector('[data-film-station=B2] [data-image-state=error]');frames(page)
 placeholders=page.locator('[data-film-station=B2] .film-image-placeholder').evaluate_all('es=>es.map(e=>{const p=e.parentElement.getBoundingClientRect(),r=document.createRange();r.selectNodeContents(e);return {text:e.textContent,clipped:[...r.getClientRects()].some(b=>b.left<p.left||b.right>p.right||b.top<p.top||b.bottom>p.bottom)}})')
 page.screenshot(path=str(OUT/'image-error-390.png'));before=page.locator('#tour-host').get_attribute('data-display-h');page.locator('[data-film-station=B2] button').first.click();page.wait_for_selector('.film-dialog[open][data-state=error]');assert page.get_by_role('button',name='重新载入',exact=True).is_visible()
 page.screenshot(path=str(OUT/'image-error-dialog.png'));page.unroute('**/signal-garden-*.webp');page.get_by_role('button',name='重新载入',exact=True).click();page.wait_for_selector('.film-dialog[open][data-state=ready]');assert page.locator('.film-dialog img').evaluate('i=>i.complete&&i.naturalWidth===1672');page.keyboard.press('Escape');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');assert page.locator('#tour-host').get_attribute('data-display-h')==before and not errors
 result={'previewPlaceholders':placeholders,'fullViewerErrorReadable':True,'retryLoadsOriginal':True,'closeRestoresProgress':True,'unhandledExceptions':errors,'expectedAbortedImageDiagnostics':diagnostics}
 (OUT/'image-error.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert all(not x['clipped']for x in placeholders),placeholders;b.close();print('Actual image failures, retry and progress restoration passed.',flush=True)
