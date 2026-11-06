"""Whole-scene equality at protected cameras; original source/assets/evidence guard."""
import hashlib,os,shutil,sys,tarfile
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step10_common import *
snapshot=Path('/tmp/scroll-garden-step-10-before');manifest=snapshot/'files.json'
if not manifest.exists():manifest=OUT/'baseline-files.json'
before=json.loads(manifest.read_text());allowed={'src/tour/route.ts','src/tour/startTourPrototype.ts','src/tour/tour.css','README.md','docs/scroll-garden/README.md','docs/scroll-garden/step-10-standard.md','tests/scroll-garden/README.md'}
changed=[];missing=[];added=[]
for name,digest in before.items():
 file=ROOT/name
 if not file.exists():
  if not name.startswith('dist/'):missing.append(name)
 elif hashlib.sha256(file.read_bytes()).hexdigest()!=digest:changed.append(name)
assert not missing,missing
assert all(n in allowed or n.startswith('dist/')for n in changed),changed
for directory,dirs,files in os.walk(ROOT):
 dirs[:]=[d for d in dirs if d not in {'.git','node_modules','.cache','__pycache__','.agents','.codex','.aws'}]
 for name in files:
  file=Path(directory)/name;relative=str(file.relative_to(ROOT))
  if not file.is_symlink()and relative not in before:added.append(relative)
assert all(not n.startswith('src/')or n=='src/tour/presentation.ts'for n in added),added
def original(name):
 if(snapshot/name).exists():return(snapshot/name).read_text()
 with tarfile.open(OUT/'baseline-step9-source.tar.gz')as archive:return archive.extractfile(name).read().decode()
old=original('src/tour/route.ts');new=(ROOT/'src/tour/route.ts').read_text()
for anchor,end in [('export const tourStages','interface Travel'),('/** Keep approved scene content',None)]:
 a=old[old.index(anchor):];b=new[new.index(anchor):]
 if end:a=a[:a.index(end)];b=b[:b.index(end)]
 assert a==b,anchor
assert (ROOT/'src/tour/tour.css').read_text().startswith(original('src/tour/tour.css')),'Original pillar rules modified'
save('scope-guard.json',{'passed':True,'originalFiles':len(before),'changedExisting':[n for n in changed if not n.startswith('dist/')],'missingOutsideDist':missing,'newRuntimeSources':[n for n in added if n.startswith('src/')],'protectedRouteStagesBasePosesAndAspectResolverExact':True,'originalPillarCSSPrefixExact':True,'allStep9WaterGeometryMaterialsAnimationAssetsAndPriorEvidenceUnchanged':True,'dependenciesAndReleaseUnchanged':True})
if '--scope-only'in sys.argv:print('PASS: original files and Step9 runtime protected; only approved journey sources changed');raise SystemExit
CSS='.tour-prototype > :not(.tour-stage):not(.tour-scroll-space):not(.tour-viewport-probe), .tour-prototype > :not(.tour-stage):not(.tour-scroll-space):not(.tour-viewport-probe) * {visibility:hidden!important;}'
def shot(page,name):
 page.bring_to_front();frames(page);page.mouse.move(10,page.viewport_size['height']/2);return Image.open(BytesIO(page.locator('canvas').screenshot(path=str(OUT/name)))).convert('RGB')
with sync_playwright()as p:
 b=launch(p);oldPage=b.new_page(viewport={'width':1440,'height':900});newPage=b.new_page(viewport={'width':1440,'height':900})
 for page,port in[(oldPage,4174),(newPage,4173)]:ready(page,f'http://127.0.0.1:{port}/?tour=prototype&waterTime=2');page.add_style_tag(content=CSS)
 rows=[]
 for w,h in[(1440,900),(1366,768),(390,844)]:
  for page in[oldPage,newPage]:resize(page,w,h)
  for mode in['pixel','native']:
   for page in[oldPage,newPage]:page.locator(f'.tour-actions [data-mode={mode}]').evaluate('e=>e.click()')
   for key,at in[('O',0),*STOPS,('W',11.5),('S99',12.3),('T01',.9),('T12',4.05),('T23',8.35)]:
    alignment=[]
    if key=='W':
     # W was a single mathematical point in Step9. Make its H physically
     # representable for this SAME-camera isolation only; do not alter app/input.
     for page in[oldPage,newPage]:
      alignment.append(page.evaluate('''()=>{const spacer=document.querySelector('#tour-scroll-space'),height=spacer.style.height,range=document.documentElement.scrollHeight-innerHeight,aligned=Math.ceil(range/123)*123;spacer.style.height=(aligned+innerHeight)+'px';return{originalHeight:height,originalRange:range,canonicalRange:document.documentElement.scrollHeight-innerHeight};}'''))
     assert all(entry['canonicalRange']%123==0 for entry in alignment),alignment
    for page in[oldPage,newPage]:go(page,at);frames(page)
    a=shot(oldPage,f'paired-{w}-{mode}-{key}-before.png');c=shot(newPage,f'paired-{w}-{mode}-{key}-after.png');diff=ImageChops.difference(a,c)
    da,dc=data(oldPage),data(newPage);keys=['cameraPosition','cameraTarget','viewHeight','readingStation','readingOpacity','readingTitleOpacity','magicFrame','filmStation','filmPresentation','filmMagicFrame','experimentStation','experimentPresentation','experimentMagicFrame','sceneTime'];changes={k:[da[k],dc[k]]for k in keys if da[k]!=dc[k]}
    if diff.getbbox()or changes:
     diff.save(OUT/f'paired-failure-{w}-{mode}-{key}.png');save('paired-failure.json',{'viewport':[w,h],'mode':mode,'pose':key,'bbox':diff.getbbox(),'dataChanges':changes});raise AssertionError((w,mode,key,diff.getbbox(),changes))
    rows.append({'viewport':[w,h],'mode':mode,'pose':key,'pixelsExact':True,'cameraReadingMagicAndTimeExact':True,'canonicalWScrollAlignment':alignment or None,'maskUsed':False})
    if alignment:
     for page,entry in zip([oldPage,newPage],alignment):page.locator('#tour-scroll-space').evaluate('(e,height)=>e.style.height=height',entry['originalHeight'])
 references=[]
 for mode in['pixel','native']:
  images=[]
  for page,port in[(oldPage,4174),(newPage,4173)]:
   page.set_viewport_size({'width':1440,'height':1000});page.goto(f'http://127.0.0.1:{port}/?waterTime=2&render={mode}',wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');frames(page);images.append(shot(page,f'default-reference-{mode}-{port}.png'))
  assert ImageChops.difference(*images).getbbox()is None;references.append({'mode':mode,'pixelsExact':True})
 save('paired-scene-isolation.json',{'passed':True,'pairs':rows,'defaultReference':references,'method':'hide DOM only, retain all 3D glyphs, compare complete canvas exactly with zero tolerance and NO masks at13 protected poses plus3 unchanged transitions, three sizes/two modes. Only canonical W samples temporarily align test scroll range to123px multiple for exact H11.5, then restore original. All input/performance/normal browser checks use original range. Changed T3W/WIDE/native W landing is separately documented'});b.close();print('PASS:',len(rows),'complete scene pairs and2default references exact; old source/assets protected',flush=True)
