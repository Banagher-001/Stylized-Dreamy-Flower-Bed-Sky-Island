"""Protect old assets/source, verify scene-only paired pixels outside actual pool."""
from io import BytesIO
import hashlib,math,sys
from PIL import Image,ImageChops,ImageDraw
from playwright.sync_api import sync_playwright
from step8_common import *

manifest=Path('/tmp/scroll-garden-step-8-before/files.json')
if not manifest.exists():manifest=OUT/'baseline-files.json'
before=json.loads(manifest.read_text())
allowed={'src/scene/createScene.ts','src/tour/startTourPrototype.ts','src/tour/route.ts','src/tour/experimentContent.ts','README.md','docs/scroll-garden/README.md','docs/scroll-garden/step-8-standard.md','tests/scroll-garden/README.md'}
changed=[];missing=[]
for name,digest in before.items():
 f=ROOT/name
 if not f.exists():
  if not name.startswith('dist/'):missing.append(name)
 elif hashlib.sha256(f.read_bytes()).hexdigest()!=digest:changed.append(name)
assert not missing,missing
assert all(name in allowed or name.startswith('dist/')for name in changed),changed
newSources={'src/config/fountain.ts','src/materials/createRefinedWaterMaterial.ts','src/materials/createFountainStoneMaterial.ts','src/scene/createFountainAppearance.ts','src/assets/courtyard-water-cover.webp'}
newFiles=[str(p.relative_to(ROOT))for p in ROOT.rglob('*')if p.is_file()and not {'.git','node_modules','.cache','__pycache__'}.intersection(p.relative_to(ROOT).parts)and str(p.relative_to(ROOT))not in before]
assert all(not name.startswith('src/')or name in newSources for name in newFiles),newFiles

save('scope-guard.json',{'passed':True,'originalFiles':len(before),'changedExisting':[n for n in changed if not n.startswith('dist/')],'missingOutsideDist':missing,'unchangedExisting':len(before)-len(changed)-sum(not(ROOT/n).exists()for n in before),'oldAssetsAndEvidenceUnchanged':True,'dependenciesAndJetConfigUnchanged':True})
if '--scope-only'in sys.argv:print('PASS: final source scope and old files protected');raise SystemExit
CSS='.tour-prototype > :not(.tour-stage):not(.tour-scroll-space):not(.tour-viewport-probe){visibility:hidden!important;}'
def shot(page,name):
 page.bring_to_front();frames(page);page.mouse.move(10,page.viewport_size['height']/2);raw=page.locator('canvas').screenshot(path=str(OUT/name));return Image.open(BytesIO(raw)).convert('RGB')
with sync_playwright()as p:
 b=launch(p);old=b.new_page(viewport={'width':1440,'height':900});new=b.new_page(viewport={'width':1440,'height':900});legacy=b.new_page(viewport={'width':1440,'height':900})
 for page,url in [(old,'http://127.0.0.1:4174'),(new,'http://127.0.0.1:4173'),(legacy,'http://127.0.0.1:4173')]:
  ready(page,url+'/?tour=prototype&waterTime=2'+('&pool=legacy'if page==legacy else''));page.add_style_tag(content=CSS);frames(page)
 results=[];states=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  for page in [old,new,legacy]:resize(page,w,h)
  for mode in ['pixel','native']:
   for page in [old,new,legacy]:page.locator(f'.tour-actions [data-mode={mode}]').evaluate('e=>e.click()')
   for key,at in [('O',0),('W',11.5),('A1',1.74),('B2',5.95),('C2',10.05)]:
    for page in[old,new,legacy]:go(page,at);frames(page)
    a=shot(old,f'paired-{w}-{mode}-{key}-before.png');c=shot(new,f'paired-{w}-{mode}-{key}-after.png');d=shot(legacy,f'paired-{w}-{mode}-{key}-legacy.png')
    assert ImageChops.difference(a,d).getbbox()is None,(w,mode,key,'legacy changed')
    da,dc=data(old),data(new);keys=['cameraPosition','cameraTarget','viewHeight','readingStation','readingOpacity','readingTitleOpacity','magicFrame','filmStation','filmPresentation','filmMagicFrame','experimentStation','experimentPresentation','experimentMagicFrame','sceneTime'];assert all(da[k]==dc[k]for k in keys),(w,mode,key)
    pose={'pose':da,'width':w,'height':a.height}
    # The production page cannot import test modules. Use the dev helper page below.
    states.append({'viewport':[w,h],'mode':mode,'key':key,'pose':pose,'exactNarrative':True,'legacyPixelsExact':True,'before':f'paired-{w}-{mode}-{key}-before.png','after':f'paired-{w}-{mode}-{key}-after.png'})
 refs=[]
 for mode in['pixel','native']:
  images=[]
  for page,url in[(old,'http://127.0.0.1:4174'),(new,'http://127.0.0.1:4173')]:
   page.set_viewport_size({'width':1440,'height':1000});page.goto(url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');frames(page);page.mouse.move(10,500);images.append(Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB'))
  assert ImageChops.difference(*images).getbbox()is None,mode;refs.append({'mode':mode,'pixelsExact':True})
 ready(new,'http://127.0.0.1:5173/?tour=prototype&waterTime=2')
 projections=new.evaluate('async rows=>{const m=await import("/tests/scroll-garden/inspect_pool.js");return rows.map(r=>m.poolProjection(r.pose))}',states)
 for entry,box in zip(states,projections):
  a=Image.open(OUT/entry['before']).convert('RGB');c=Image.open(OUT/entry['after']).convert('RGB');diff=ImageChops.difference(a,c);mask=Image.new('L',a.size,0)
  rect=[max(0,math.floor(box['left']-12)),max(0,math.floor(box['top']-12)),min(a.width,math.ceil(box['right']+12)),min(a.height,math.ceil(box['bottom']+12))]
  if rect[0]<rect[2]and rect[1]<rect[3]:ImageDraw.Draw(mask).rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),fill=255)
  outside=Image.composite(Image.new('RGB',a.size,0),diff,mask);maximum=max(v[1]for v in outside.getextrema());assert maximum==0,(entry,maximum,outside.getbbox())
  results.append({k:v for k,v in entry.items()if k!='pose'}|{'poolBounds':box,'maskExpansionCssPixels':12,'outsidePoolMaximumChannelDifference':maximum,'wholeImageExact':diff.getbbox()is None})
 save('paired-scene-isolation.json',{'passed':True,'pairs':results,'defaultReference':refs,'method':'actual pure canvas pairs: hide only DOM chrome during capture; preserve 3D sigils; compare unchanged narrative fields and legacy pixels exactly; mask only projected unchanged pool bounds+12CSSpx, require ZERO difference outside; current/default reference both exact'});b.close();print('PASS:30paired scenes outside pool exact;30legacy scenes exact;2default references exact; source protected',flush=True)
