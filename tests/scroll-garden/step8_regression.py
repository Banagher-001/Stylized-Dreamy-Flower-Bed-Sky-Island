"""Re-run actual previous narrative/media assertions; old files/evidence untouched."""
import sys
from pathlib import Path
from step8_common import ROOT,OUT
index=sys.argv.index('--suite');suite=sys.argv[index+1];del sys.argv[index:index+2]
folder=OUT/('regression-'+suite);folder.mkdir(parents=True,exist_ok=True)
if suite=='chapter':
 source=(ROOT/'tests/scroll-garden/step7_browser.py').read_text()
 source=source.replace('from step7_common import *',f'from step7_common import *\nimport step7_common as shared\nshared.OUT=Path({str(folder)!r});OUT=shared.OUT')
 source=source.replace('STEP 07','STEP 08').replace('courtyard-interactive-cover','courtyard-water-cover')
else:
 source=(ROOT/'tests/scroll-garden'/('step6_about_regression.py'if suite=='about'else'step6_browser.py')).read_text()
 source=source.replace("OUT=ROOT/'docs/evidence/scroll-garden-step-6'",f'OUT=Path({str(folder)!r})').replace('STEP 06','STEP 08')
 source=source.replace('.count()==15','.count()==18').replace("'disabledGraphControls':15","'disabledGraphControls':18").replace("'disabledSceneControls':15","'disabledSceneControls':18")
 source=source.replace("('geometries',56)","('geometries',58)").replace("('textures',5)","('textures',6)").replace("('programs',11)","('programs',12)").replace("page.locator('dialog').count()==1","page.locator('dialog').count()==2")
 source=source.replace("(OUT/'route-before.json')","(ROOT/'docs/evidence/scroll-garden-step-6/route-before.json')")
 source=source.replace("OUT/f'before-reference-{mode}.png'","ROOT/f'docs/evidence/scroll-garden-step-8/before-reference-{mode}.png'")
exec(compile(source,f'<Step8 {suite} current-regression>','exec'),globals())
