"""Re-run actual previous narrative/media assertions; old files/evidence untouched."""
import sys
from pathlib import Path
from step9_common import ROOT,OUT
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
 source=source.replace('STEP 07','STEP 09').replace('courtyard-interactive-cover','courtyard-orb-cover')
 # ResizeObserver may schedule the necessary final live-view frame after opening.
 # Bound that setup explicitly; the following original 250ms ZERO-draw assertion stays.
 source=source.replace("draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(250)","layout_trace=page.evaluate(PAUSED_PROJECT_TRACE);save(f'project-pause-layout-{args.engine}.json',layout_trace);assert layout_trace['settled'],layout_trace;draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(250)",1)
else:
 source=(ROOT/'tests/scroll-garden'/('step6_about_regression.py'if suite=='about'else'step6_browser.py')).read_text()
 source=source.replace("OUT=ROOT/'docs/evidence/scroll-garden-step-6'",f'OUT=Path({str(folder)!r})').replace('STEP 06','STEP 09')
 source=source.replace('.count()==15','.count()==18').replace("'disabledGraphControls':15","'disabledGraphControls':18").replace("'disabledSceneControls':15","'disabledSceneControls':18")
 source=source.replace("('geometries',56)","('geometries',58)").replace("('textures',5)","('textures',6)").replace("('programs',11)","('programs',13)").replace("page.locator('dialog').count()==1","page.locator('dialog').count()==2")
 source=source.replace("(OUT/'route-before.json')","(ROOT/'docs/evidence/scroll-garden-step-6/route-before.json')")
 source=source.replace("OUT/f'before-reference-{mode}.png'","ROOT/f'docs/evidence/scroll-garden-step-9/before-reference-{mode}.png'")
exec(compile(source,f'<Step9 {suite} current-regression>','exec'),globals())
