"""Run unchanged Step 6 assertions against Step 7, with explicit integration-budget updates.

Old scripts/evidence remain intact. Only title, debug count, extra dialog and the
approved +2 geometry/+1 texture allowance are changed for this current run.
"""
import sys
from step7_common import ROOT,OUT
suite='about'if '--about'in sys.argv else 'films'
if '--about'in sys.argv:sys.argv.remove('--about')
name='step6_about_regression.py'if suite=='about'else'step6_browser.py'
source=(ROOT/'tests/scroll-garden'/name).read_text()
destination=OUT/('regression-'+suite);destination.mkdir(parents=True,exist_ok=True)
source=source.replace("OUT=ROOT/'docs/evidence/scroll-garden-step-6'",f'OUT=Path({str(destination)!r})')
source=source.replace('STEP 06','STEP 07').replace('.count()==15','.count()==18').replace("'disabledGraphControls':15","'disabledGraphControls':18").replace("'disabledSceneControls':15","'disabledSceneControls':18")
source=source.replace("('geometries',56)","('geometries',58)").replace("('textures',5)","('textures',6)").replace("page.locator('dialog').count()==1","page.locator('dialog').count()==2")
source=source.replace("(OUT/'route-before.json')", "(ROOT/'docs/evidence/scroll-garden-step-6/route-before.json')")
source=source.replace("OUT/f'before-reference-{mode}.png'", "(ROOT/'docs/evidence/scroll-garden-step-7')/f'before-reference-{mode}.png'")
exec(compile(source,str(ROOT/'tests/scroll-garden'/name),'exec'),globals())
