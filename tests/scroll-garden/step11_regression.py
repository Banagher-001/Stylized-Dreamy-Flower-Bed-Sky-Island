"""Re-run actual previous narrative/media assertions; old files/evidence untouched."""
import json,sys
from pathlib import Path
from PIL import ImageChops
from step11_common import ROOT,OUT
def assert_same_snapshot(before_state,before_picture,after_state,after_picture,label):
 diff=ImageChops.difference(before_picture,after_picture)
 if before_state!=after_state or diff.getbbox()is not None:
  before_picture.save(OUT/f'{label}-before.png');after_picture.save(OUT/f'{label}-after.png');diff.save(OUT/f'{label}-difference.png')
  (OUT/f'{label}-diagnostics.json').write_text(json.dumps({'before':before_state,'after':after_state,'bbox':diff.getbbox(),'channelMaximum':[v[1]for v in diff.getextrema()]},ensure_ascii=False,indent=2)+'\n')
  raise AssertionError((label,'state/image changed',diff.getbbox(),{k:[v,after_state[k]]for k,v in before_state.items()if v!=after_state[k]}))
def assert_fixed_read(page,before_state,before_picture,label):
 after_state=state(page);after_picture=picture(page);diff=ImageChops.difference(before_picture,after_picture)
 if after_state!=before_state or diff.getbbox()is not None:
  before_picture.save(OUT/f'{label}-before.png');after_picture.save(OUT/f'{label}-after.png');diff.save(OUT/f'{label}-difference.png')
  save(f'{label}-diagnostics.json',{'before':before_state,'after':after_state,'bbox':diff.getbbox(),'channelMaximum':[v[1]for v in diff.getextrema()]})
  raise AssertionError((label,'held reading changed',diff.getbbox(),{k:[v,after_state[k]]for k,v in before_state.items()if v!=after_state[k]}))
PAUSED_PROJECT_TRACE='''()=>new Promise(resolve=>{
 const rows=[],start=performance.now();let last='',stable=0;
 function sample(){
  const d=document.querySelector('#tour-host').dataset,r=document.querySelector('.tour-project-live-space').getBoundingClientRect();
  const state={draws:window.__tourProbe.draws,time:d.sceneTime,camera:d.cameraPosition,height:d.viewHeight,live:[r.x,r.y,r.width,r.height]};
  const key=JSON.stringify(state),elapsed=performance.now()-start;stable=key===last?stable+1:0;last=key;rows.push({elapsed,...state});
  if(stable>=3&&elapsed>=120){resolve({settled:true,rows});return;}
  if(elapsed>2000){resolve({settled:false,rows});return;}
  requestAnimationFrame(sample);
 }requestAnimationFrame(sample);
})'''
index=sys.argv.index('--suite');suite=sys.argv[index+1];del sys.argv[index:index+2]
folder=OUT/('regression-'+suite);folder.mkdir(parents=True,exist_ok=True)
if suite=='chapter':
 source=(ROOT/'tests/scroll-garden/step7_browser.py').read_text()
 source=source.replace('from step7_common import *',f'from step7_common import *\nimport step7_common as shared\nshared.OUT=Path({str(folder)!r});OUT=shared.OUT')
 source=source.replace('STEP 07','张辰翰').replace('courtyard-interactive-cover','courtyard-orb-cover')
 source=source.replace('assert state(page)==a and ImageChops.difference(pic,picture(page)).getbbox()is None;plateaus.append',"assert_fixed_read(page,a,pic,f'plateau-{start}');plateaus.append",1)
 # ResizeObserver may schedule the necessary final live-view frame after opening.
 # Bound that setup explicitly; the following original 250ms ZERO-draw assertion stays.
 source=source.replace("draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(250)","layout_trace=page.evaluate(PAUSED_PROJECT_TRACE);save(f'project-pause-layout-{args.engine}.json',layout_trace);assert layout_trace['settled'],layout_trace;draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(250)",1)
else:
 source=(ROOT/'tests/scroll-garden'/('step6_about_regression.py'if suite=='about'else'step6_browser.py')).read_text()
 source=source.replace("OUT=ROOT/'docs/evidence/scroll-garden-step-6'",f'OUT=Path({str(folder)!r})').replace('STEP 06','张辰翰')
 source=source.replace('.count()==15','.count()==18').replace("'disabledGraphControls':15","'disabledGraphControls':18").replace("'disabledSceneControls':15","'disabledSceneControls':18")
 source=source.replace("('geometries',56)","('geometries',58)").replace("('textures',5)","('textures',6)").replace("('programs',11)","('programs',12)").replace("page.locator('dialog').count()==1","page.locator('dialog').count()==2")
 source=source.replace("(OUT/'route-before.json')","(ROOT/'docs/evidence/scroll-garden-step-6/route-before.json')")
 source=source.replace("OUT/f'before-reference-{mode}.png'","ROOT/f'docs/evidence/scroll-garden-step-10/before-reference-{mode}.png'")
# Default visitor regressions use real native positioning; debug controls get their own suite.
source=source.replace('像素预览','像素画面')
if suite=='about':
 source=source.replace('go(page,2.54);before=state(page);pixel=image(page)','go(page,2.54);page.mouse.click(10,450);before=state(page);pixel=image(page)',1)
 source=source.replace('assert state(page)==before and ImageChops.difference(pixel,image(page)).getbbox()is None',"assert_same_snapshot(before,pixel,state(page),image(page),'about-mode-return')",1)
source=source.replace("page.locator('#tour-reference').focus()","page.locator('#tour-stop-about').focus()").replace("=='tour-reference'","=='tour-stop-about'")
for station,h in [('A2',2.54),('B4',7.64),('C3',10.83)]:
 source=source.replace(f"page.locator('.tour-inspector summary').click();page.locator('[data-reading-stop={station}]').click();settled(page,{h});page.locator('.tour-inspector summary').click()",f'go(page,{h});settled(page,{h})')
source=source.replace('native wheel and C chapter/debug stops','native wheel and C chapter positioning').replace('keyboard and debug navigation','keyboard and native navigation').replace('chapter and four debug stops','chapter and four native stops')
# The old reduced-motion camera contract is superseded by stable reading.
# Keep every immersive mobile assertion in normal-motion media; Step11's browser
# suite separately verifies real media-query stable reading and zero camera travel.
source=source.replace("'reduced_motion':'reduce'", "'reduced_motion':'no-preference'")
source=source.replace("assert json.loads(data(m)['magicFrame'])['dustVisible']==0", "assert json.loads(data(m)['magicFrame'])['dustVisible']==4")
source=source.replace("assert json.loads(data(m)['filmMagicFrame'])['dustVisible']==0", "assert json.loads(data(m)['filmMagicFrame'])['dustVisible']==4")
source=source.replace("and json.loads(data(m)['experimentMagicFrame'])['dustVisible']==0", "and json.loads(data(m)['experimentMagicFrame'])['dustVisible']==4")
source=source.replace('reduced-motion navigation','normal-motion navigation; reduced motion separately covered in Step11').replace('reduced motion, full content','normal motion, full content')
# Graphic recovery now preserves complete stable reading until explicit opt-in.
source=source.replace("#tour-motion:disabled').count()==18", "#tour-motion:disabled').count()==3")
source=source.replace("'disabledGraphControls':18", "'disabledGraphControls':3").replace("'disabledSceneControls':18", "'disabledSceneControls':3")
source=source.replace("page.evaluate('window.__loss.restoreContext()')", "page.evaluate('window.__loss.restoreContext()');page.wait_for_function('document.querySelector(\"main\").dataset.immersiveAvailable===\"true\"');assert page.locator('main').get_attribute('data-reading-mode')=='stable';assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10;page.locator('#tour-layout-toggle').click()")
exec(compile(source,f'<Step11 {suite} current-regression>','exec'),globals())
