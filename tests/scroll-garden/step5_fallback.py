"""Decoration-unavailable, font fallback, and shader-cache budget checks."""
from pathlib import Path
from io import BytesIO
from types import SimpleNamespace
import ast,json,math
from PIL import Image
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-5'
# Reuse just the measured-background function, without launching another suite.
source=(Path(__file__).with_name('step5_browser.py')).read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='contrast')
namespace={'Image':Image,'BytesIO':BytesIO,'math':math,'OUT':OUT,'args':SimpleNamespace(engine='font-fallback')}
exec(compile(ast.Module(body=[node],type_ignores=[]),'<contrast helper>','exec'),namespace)
measure_contrast=namespace['contrast']
NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);results={};issues=[];diagnostics=[];font_views=[]
 for disabled in [True,False]:
  context=b.new_context(viewport={'width':1440,'height':900})
  if disabled:context.add_init_script(NO_2D)
  page=context.new_page();page.on('pageerror',lambda e:issues.append(str(e)));page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None);page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
  assert page.locator('#tour-host').get_attribute('data-magic-status')==('fallback'if disabled else'ready')
  page.evaluate('scrollTo({top:2.54/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');page.wait_for_function('document.querySelector("#tour-host").dataset.readingOpacity==="1.0000000"&&document.querySelector("#tour-host").dataset.stage==="A2"')
  frames=[]
  for mode in ['pixel','native','pixel']:
   page.get_by_role('button',name='像素预览'if mode=='pixel'else'正常画面',exact=True).click();page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');frames.append(json.loads(page.locator('#tour-host').get_attribute('data-renderer-stats')))
  if disabled:
   for width,height in [(1440,900),(1366,768),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}')
    for key,h,expected in [('A1',1.74,'战锤 40K'),('A2',2.54,'枫叶互动'),('A3',3.34,'Vibe Coding')]:
     page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
     article=page.locator('.pillar-reading article[aria-hidden=false]');article.locator('h2').evaluate("e=>e.style.fontFamily=\"'Missing Inscription Font', serif\"");article.locator('.pillar-reading-body').evaluate("e=>e.style.fontFamily=\"'Missing Inscription Font', serif\"");page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
     assert expected in article.inner_text()and page.locator('.pillar-reading').get_attribute('data-fits')=='true'
     assert article.locator('[data-reading-ink]').evaluate_all('es=>es.every(e=>{const p=e.closest(".pillar-reading").getBoundingClientRect(),r=e.getBoundingClientRect();return r.left>=p.left+12&&r.right<=p.right-12&&r.top>=p.top+12&&r.bottom<=p.bottom-12})')
     page.mouse.move(10,height/2);page.screenshot(path=str(OUT/f'decoration-font-fallback-{width}-{key}.png'));font_views.append({'viewport':[width,height],'station':key,'fits':True,'completeText':article.inner_text(),'contrast':measure_contrast(page,str(width)+'-'+key)})
   page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动'in page.locator('#about').inner_text()
  results['decorationUnavailable'if disabled else'normal']={'frames':frames,'textReadable':True,'fontFallbackTested':disabled,'referenceLinkChecked':disabled,'referenceUsable':True if disabled else None}
  context.close()
 for normal,base in zip(results['normal']['frames'],results['decorationUnavailable']['frames']):
  assert normal['geometries']-base['geometries']<=3 and normal['textures']-base['textures']<=2 and normal['programs']-base['programs']<=3,(normal,base)
 assert not issues
 assert all('Pillar decoration unavailable; reading remains available.'in d['text']for d in diagnostics),diagnostics
 (OUT/'decoration-fallback.json').write_text(json.dumps({'checks':results,'fontFallbackViews':font_views,'unhandledExceptions':issues,'expectedDecorationDiagnostics':diagnostics,'method':'disable Canvas2D only in test browser; WebGL and normal reading remain active; compare same-mode shader-cache budgets and all nine font-fallback layouts'},ensure_ascii=False,indent=2)+'\n');b.close();print('Decoration/font fallback at all nine layouts, reference link and same-mode cached shader budgets passed.')
