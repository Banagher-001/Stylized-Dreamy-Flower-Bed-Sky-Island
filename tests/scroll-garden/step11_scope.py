"""Protect old source/assets/evidence and compare complete scene pixels without masks."""
import hashlib,os,sys
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step11_common import *
before=json.loads(Path('/tmp/scroll-garden-step-11-before-manifest.json').read_text());snapshot=Path('/tmp/scroll-garden-step-11-before')
allowed={'src/tour/startTourPrototype.ts','src/tour/createPillarReader.ts','src/tour/createFilmReader.ts','src/tour/createExperimentReader.ts','src/tour/createProjectViewer.ts','src/tour/presentation.ts','src/animation/createAnimationController.ts','src/rendering/createRenderer.ts','README.md','docs/scroll-garden/README.md','docs/scroll-garden/step-11-standard.md','tests/scroll-garden/README.md'}
newSources={'src/tour/createReadingLayout.ts','src/tour/readerFlow.ts','src/tour/readingLayout.css'}
changed=[];missing=[];added=[]
for name,digest in before.items():
 file=ROOT/name
 if not file.exists():
  if not name.startswith('dist/'):missing.append(name)
 elif hashlib.sha256(file.read_bytes()).hexdigest()!=digest:changed.append(name)
for folder,dirs,files in os.walk(ROOT):
 dirs[:]=[d for d in dirs if d not in {'.git','node_modules','.cache','__pycache__'}]
 for name in files:
  relative=str((Path(folder)/name).relative_to(ROOT))
  if relative not in before:added.append(relative)
assert not missing,missing
assert all(n in allowed or n.startswith('dist/')for n in changed),changed
assert all(not n.startswith('src/')or n in newSources for n in added),added
assert all(not n.startswith(('public/','release/'))for n in added),added
assert all(not n.startswith('docs/evidence/')or n.startswith('docs/evidence/scroll-garden-step-11/')for n in added),added
for name in ['src/tour/route.ts','src/tour/tour.css','src/tour/film.css','src/tour/experiment.css']:
 assert (ROOT/name).read_bytes()==(snapshot/name).read_bytes(),name
save('scope-guard.json',{'passed':True,'baselineFiles':len(before),'changedExistingOutsideDist':[n for n in changed if not n.startswith('dist/')],'newRuntimeSources':[n for n in added if n.startswith('src/')],'missingOutsideDist':missing,'baseRouteAndOriginalReadingCSSExact':True,'allOriginalSceneWaterOrbMagicAssetsDependenciesAndHistoricalEvidenceUnchanged':True,'defaultEntryAndReleaseUnchanged':True})
if '--scope-only'in sys.argv:print('PASS original',len(before),'files protected within explicit source/document scope');raise SystemExit
CSS=''' .tour-header,.tour-heading,.tour-stops,.tour-footer,.pillar-reading,.film-reading,.experiment-reading,.pillar-reading-link,.film-reading-link,.experiment-reading-link,.tour-flow-intro,.tour-flow-label,.tour-flow-water,.tour-flow-ending,.tour-skip{visibility:hidden!important} '''
def shot(page,path):
 page.bring_to_front();frames(page);page.mouse.move(10,page.viewport_size['height']/2);return Image.open(BytesIO(page.locator('canvas').screenshot(path=str(OUT/path)))).convert('RGB')
with sync_playwright()as p:
 b=launch(p);old=b.new_page(viewport={'width':1440,'height':900});new=b.new_page(viewport={'width':1440,'height':900})
 for page,port in [(old,4174),(new,4173)]:
  page.bring_to_front();ready(page,f'http://127.0.0.1:{port}/?tour=prototype&waterTime=2')
  if page==new:page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"')
  page.add_style_tag(content=CSS)
 results=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  for page in [old,new]:page.bring_to_front();resize(page,w,h)
  for render in ['pixel','native']:
   for page in [old,new]:page.bring_to_front();page.locator(f'.tour-actions [data-mode={render}]').evaluate('e=>e.click()')
   for key,at in VIEWS:
    pictures=[];states=[]
    for page,label in [(old,'before'),(new,'after')]:
     page.bring_to_front();go(page,at);frames(page);pictures.append(shot(page,f'paired-{w}-{render}-{key}-{label}.png'));states.append(data(page))
    diff=ImageChops.difference(*pictures)
    keys=['cameraPosition','cameraTarget','viewHeight','sceneTime','readingStation','magicFrame','filmStation','filmMagicFrame','experimentStation','experimentMagicFrame']
    stateChanges={k:[states[0][k],states[1][k]]for k in keys if states[0][k]!=states[1][k]}
    if diff.getbbox()or stateChanges:
     diff.save(OUT/f'paired-difference-{w}-{render}-{key}.png');save('paired-failure.json',{'viewport':[w,h],'mode':render,'pose':key,'bbox':diff.getbbox(),'changes':stateChanges});raise AssertionError((w,render,key,diff.getbbox(),stateChanges))
    results.append({'viewport':[w,h],'mode':render,'pose':key,'pixelsExact':True,'cameraTimeAndAllGPUInscriptionsExact':True,'maskUsed':False})
 references=[]
 for render in ['pixel','native']:
  pictures=[]
  for page,port in [(old,4174),(new,4173)]:
   page.bring_to_front();page.set_viewport_size({'width':1440,'height':1000});page.goto(f'http://127.0.0.1:{port}/?waterTime=2&render={render}',wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state=ready]');frames(page);pictures.append(shot(page,f'paired-reference-{render}-{port}.png'))
  assert ImageChops.difference(*pictures).getbbox()is None;references.append({'mode':render,'pixelsExact':True})
 save('paired-scene-isolation.json',{'passed':True,'pairs':results,'defaultReference':references,'method':'exact complete canvas at18 poses including5moving routes and W;three sizes/two modes;DOM ink hidden only;NO masks,zero channel tolerance,no scroll-range adjustment','viewportFramingChanged':False});b.close();print('PASS',len(results),'complete scene pairs,2default modes exact',flush=True)
