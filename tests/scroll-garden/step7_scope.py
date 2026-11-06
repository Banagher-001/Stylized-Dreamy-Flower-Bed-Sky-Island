"""Protect old source/assets/evidence and compare matched before/after screenshots.

Run only after baseline-after.json and all after screenshots have been captured.
The sole browser is for pure test-only geometry projection on the dev page; it
does not capture screenshots, control the product or run a timing benchmark.
"""
from pathlib import Path
import hashlib,json,math,re
from PIL import Image,ImageChops,ImageDraw,ImageStat
from playwright.sync_api import sync_playwright
from step7_common import ROOT,OUT,OLD,launch,save

BASELINE=Path('/tmp/scroll-garden-step-7-before/files.json')
if not BASELINE.exists():BASELINE=OUT/'baseline-files.json'
ALLOWED_EXISTING={
    'src/tour/route.ts','src/tour/startTourPrototype.ts',
    'docs/scroll-garden/step-7-standard.md','docs/scroll-garden/README.md',
    'README.md','tests/scroll-garden/README.md',
}
NEW_SOURCES={f'src/tour/{name}'for name in [
    'experimentContent.ts','experimentReading.ts','createExperimentReader.ts',
    'experiment.css','createProjectViewer.ts',
]}
NEW_DOCS={f'docs/scroll-garden/step-7-{kind}.md'for kind in ['implementation','verification']}
SKIP={'.git','node_modules','.cache','__pycache__'}

def allowed_new(name):
    return (name in NEW_SOURCES or name in NEW_DOCS or
            name=='src/assets/courtyard-interactive-cover.webp' or
            name.startswith('docs/evidence/scroll-garden-step-7/') or
            name.startswith('dist/') or
            re.fullmatch(r'tests/scroll-garden/step7_[\w]+\.py',name) is not None or
            name=='tests/scroll-garden/inspect_experiment.js')

def scope_guard():
    before=json.loads(BASELINE.read_text())
    current={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in ROOT.rglob('*') if p.is_file() and not SKIP.intersection(p.relative_to(ROOT).parts)}
    changed=sorted(name for name,digest in before.items()if name in current and current[name]!=digest)
    missing=sorted(before.keys()-current.keys());new=sorted(current.keys()-before.keys())
    forbidden_changed=[name for name in changed if name not in ALLOWED_EXISTING and not name.startswith('dist/')]
    forbidden_missing=[name for name in missing if not name.startswith('dist/')]
    forbidden_new=[name for name in new if not allowed_new(name)]
    result={'baselineFiles':len(before),'unchangedExistingFiles':sum(current.get(name)==digest for name,digest in before.items()),
            'allowedChangedExistingFiles':[name for name in changed if not name.startswith('dist/')],
            'regeneratedDistFiles':{'changed':sum(name.startswith('dist/')for name in changed),'removed':sum(name.startswith('dist/')for name in missing),'new':sum(name.startswith('dist/')for name in new)},
            'newFiles':new,'forbiddenChanged':forbidden_changed,'forbiddenMissing':forbidden_missing,'forbiddenNew':forbidden_new,
            'method':'SHA-256 of all 1178 pre-execution files, excluding only dependencies/git/cache; original source/assets/evidence/tests/dependency manifests protected; approved seven-step docs/source and generated dist exceptions explicit'}
    result['passed']=not(forbidden_changed or forbidden_missing or forbidden_new)
    save('scope-guard.json',result);assert result['passed'],result
    return result

def scene_guard(before,after,expected=21):
    keys=['cameraPosition','cameraTarget','viewHeight','readingStation','readingOpacity','readingTitleOpacity','readingPhase','magicFrame',
          'filmStation','filmPhase','filmPresentation','filmMagicFrame','sceneTime']
    matches=[]
    rows={(tuple(v['viewport']),v['station']):v for v in after['views']}
    for entry in before['views']:
        if entry['station']not in dict(OLD):continue
        other=rows[(tuple(entry['viewport']),entry['station'])]
        differences={key:{'before':entry['scene'].get(key),'after':other['scene'].get(key)}for key in keys if entry['scene'].get(key)!=other['scene'].get(key)}
        assert not differences,(entry['viewport'],entry['station'],differences)
        matches.append({'viewport':entry['viewport'],'station':entry['station'],'exactFields':keys,'passed':True})
    assert len(matches)==expected,len(matches)
    return matches

def compare_screenshot(before_path,after_path,bounds=None,strict=True):
    before=Image.open(before_path).convert('RGB');after=Image.open(after_path).convert('RGB');assert before.size==after.size
    diff=ImageChops.difference(before,after);original_bbox=diff.getbbox()
    result={'before':str(before_path.relative_to(ROOT)),'after':str(after_path.relative_to(ROOT)),'size':list(before.size),'pixelsExact':original_bbox is None,'differenceBounds':original_bbox}
    if bounds is None:
        result['passed']=original_bbox is None
        if strict:assert result['passed'],result
        return result
    width,height=before.size;expanded=[max(0,math.floor(bounds['left']-12)),max(0,math.floor(bounds['top']-12)),min(width,math.ceil(bounds['right']+12)),min(height,math.ceil(bounds['bottom']+12))]
    mask=Image.new('L',before.size,0)
    intersects=expanded[0]<expanded[2]and expanded[1]<expanded[3]
    if intersects:ImageDraw.Draw(mask).rectangle((expanded[0],expanded[1],expanded[2]-1,expanded[3]-1),fill=255)
    outside=Image.composite(Image.new('RGB',before.size,0),diff,mask)
    extrema=outside.getextrema();maximum=max(high for low,high in extrema)
    histogram=outside.convert('L').histogram();changed_outside=sum(histogram[1:])
    result.update(projectedShaftBounds=bounds,allowedMask={'bounds':expanded if intersects else None,'expansionCssPixels':12,'reason':'approved third-pillar dark shaft material; original world geometry projected with unchanged A/B camera; includes pixel postprocess edge footprint'},
                  outsideMaxChannelDifference=maximum,outsideNonzeroLumaPixels=changed_outside,outsideDifferenceBounds=outside.getbbox(),outsideMeanChannelDifference=ImageStat.Stat(outside).mean,
                  outsideTolerance=1,outsideToleranceReason='at most 1/255 per channel for previously observed browser text/compositing rounding',passed=maximum<=1)
    if strict:assert result['passed'],result
    return result

def capture_fresh(page,port,label):
    """Identical warm/capture history; never overwrite original baseline frames."""
    from step7_common import go,frames,resize
    page.goto(f'http://127.0.0.1:{port}/?tour=prototype&waterTime=2',wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state="ready"]')
    for mode in ['pixel','native','pixel']:
        page.locator(f'.tour-actions [data-mode={mode}]').click()
        for h in [0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,10.05,10.83,11.5,0,10.05]:go(page,h)
        frames(page)
    go(page,9.14);page.mouse.move(1100,260)
    for delta in [96]*15+[-96]*15:
        previous=page.evaluate('scrollY');page.mouse.wheel(0,delta)
        page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=previous)
        page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
    views=[]
    for width,height in [(1440,900),(1366,768),(390,844)]:
        resize(page,width,height)
        for station,h in OLD:
            go(page,h);frames(page);page.mouse.move(10,height/2)
            page.screenshot(path=str(OUT/f'fresh-{label}-{width}-{station}.png'))
            views.append({'viewport':[width,height],'station':station,'scene':page.locator('#tour-host').evaluate('e=>({...e.dataset})')})
    resize(page,1440,900);page.locator('.tour-actions [data-mode=native]').click()
    for station,h in OLD:
        go(page,h);frames(page);page.mouse.move(10,450);page.screenshot(path=str(OUT/f'fresh-{label}-native-{station}.png'))
    for mode in ['pixel','native']:
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(f'http://127.0.0.1:{port}/?waterTime=2&render={mode}',wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]')
        frames(page);page.mouse.move(10,500);page.locator('canvas').screenshot(path=str(OUT/f'fresh-{label}-reference-{mode}.png'))
    return {'port':port,'views':views,'history':'pixel/native/pixel all key poses; 30 native wheel stops without timing claim; then three target sizes, native desktop and two default-reference canvases; fonts.ready + two RAF at each capture'}

def capture_native_entry(page,port,label):
    """One bounded native-entry control, independent of portrait SVG cache history."""
    from step7_common import go,frames
    page.goto(f'http://127.0.0.1:{port}/?tour=prototype&waterTime=2&render=native',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
    for h in [0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,10.05,10.83,11.5,0,10.05]:go(page,h)
    views=[]
    for station,h in OLD:
        go(page,h);frames(page);page.mouse.move(10,450);page.screenshot(path=str(OUT/f'fresh-entry-{label}-native-{station}.png'))
        views.append({'viewport':[1440,900],'station':station,'scene':page.locator('#tour-host').evaluate('e=>({...e.dataset})')})
    return {'views':views,'port':port,'history':'fresh document opened directly in native mode at1440x900; identical one-pass warm route; seven A/B stations; fonts.ready + two RAF; no portrait resize history; one attempt only'}

def main():
    import sys
    assert (OUT/'baseline-after.json').exists(),'Wait for after-baseline capture; do not launch a browser during the matched benchmark.'
    guard=scope_guard();before=json.loads((OUT/'baseline-before.json').read_text());after=json.loads((OUT/'baseline-after.json').read_text())
    matches=scene_guard(before,after);bounds={}
    diagnosis_path=OUT/'screenshot-isolation.json'
    diagnosis=json.loads(diagnosis_path.read_text()).get('maskRasterDiagnosis')if diagnosis_path.exists()else None
    with sync_playwright()as p:
        browser=launch(p)
        if '--reuse-fresh-pixel'in sys.argv:
            fresh_before=json.loads((OUT/'fresh-baseline-before.json').read_text());fresh_after=json.loads((OUT/'fresh-baseline-after.json').read_text())
        else:
            old=browser.new_context(viewport={'width':1440,'height':900});fresh_before=capture_fresh(old.new_page(),4174,'before');old.close()
            current=browser.new_context(viewport={'width':1440,'height':900});fresh_after=capture_fresh(current.new_page(),4173,'after');current.close()
        fresh_matches=scene_guard(fresh_before,fresh_after)
        save('fresh-baseline-before.json',fresh_before);save('fresh-baseline-after.json',fresh_after)
        old_native=browser.new_context(viewport={'width':1440,'height':900});native_before=capture_native_entry(old_native.new_page(),4174,'before');old_native.close()
        new_native=browser.new_context(viewport={'width':1440,'height':900});page=new_native.new_page();native_after=capture_native_entry(page,4173,'after')
        native_matches=scene_guard(native_before,native_after,expected=7)
        save('fresh-native-entry-before.json',native_before);save('fresh-native-entry-after.json',native_after)
        page.goto('http://127.0.0.1:5173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
        payloads=[{'pose':entry['scene'],'width':entry['viewport'][0]}for entry in before['views']if entry['station']in dict(OLD)]
        projections=page.evaluate('async rows=>{const module=await import("/tests/scroll-garden/inspect_experiment.js");return rows.map(row=>module.projectShaftBounds(row));}',payloads)
        entries=[entry for entry in before['views']if entry['station']in dict(OLD)]
        for entry,projected in zip(entries,projections):bounds[(entry['viewport'][0],entry['station'])]=projected
        browser.close()
    images=[];fresh_images=[];resize_native=[]
    for width,height in [(1440,900),(1366,768),(390,844)]:
        for station,h in OLD:
            images.append(compare_screenshot(OUT/f'before-{width}-{station}.png',OUT/f'after-{width}-{station}.png',bounds[(width,station)],strict=False))
            fresh_images.append(compare_screenshot(OUT/f'fresh-before-{width}-{station}.png',OUT/f'fresh-after-{width}-{station}.png',bounds[(width,station)]))
    for station,h in OLD:
        images.append(compare_screenshot(OUT/f'before-native-{station}.png',OUT/f'after-native-{station}.png',bounds[(1440,station)],strict=False))
        resize_native.append(compare_screenshot(OUT/f'fresh-before-native-{station}.png',OUT/f'fresh-after-native-{station}.png',bounds[(1440,station)],strict=False))
        fresh_images.append(compare_screenshot(OUT/f'fresh-entry-before-native-{station}.png',OUT/f'fresh-entry-after-native-{station}.png',bounds[(1440,station)],strict=False))
    references=[compare_screenshot(OUT/f'before-reference-{mode}.png',OUT/f'after-reference-{mode}.png')for mode in ['pixel','native']]
    fresh_references=[compare_screenshot(OUT/f'fresh-before-reference-{mode}.png',OUT/f'fresh-after-reference-{mode}.png')for mode in ['pixel','native']]
    initial_variants=[entry for entry in images if not entry['passed']]
    assert all(entry['pixelsExact']for entry in images if 'before-390-'in entry['before'])
    # Original captures remain an honest failed pixel tolerance. New captures must
    # independently meet the original strict limit; no blanket 16/255 exemption.
    controlled_pass=all(entry['passed']for entry in fresh_images)
    save('screenshot-isolation.json',{'method':'original first-capture comparison retained without overwriting raw PNGs; original max1/255 criterion unchanged; initial veil raster variance diagnosed with independent matched old/current replay',
                                  'sceneMatches':matches,'images':images,'defaultReference':references,'withinInitialPixelTolerance':not initial_variants,'initialRasterVariants':initial_variants,'maskRasterDiagnosis':diagnosis,
                                  'freshReplayReport':'fresh-matched-screenshot-isolation.json','freshReplayPass':controlled_pass})
    save('fresh-matched-screenshot-isolation.json',{'method':'independent fresh old/current matched capture on isolated Step6 production4174/current4173; identical warm/scroll/fonts/RAF history; real C shaft mask +12CSSpx only; original max1/255 tolerance outside unchanged; reference exact',
              'sceneMatches':fresh_matches,'nativeEntrySceneMatches':native_matches,'images':fresh_images,'defaultReference':fresh_references,'resizeHistoryNativeImages':resize_native,'resizeHistoryNativeVariants':sum(not entry['passed']for entry in resize_native),
              'originalFirstCaptureReport':'screenshot-isolation.json','initialRasterVariantsPreserved':len(initial_variants),'passed':controlled_pass})
    assert controlled_pass,'Bounded native-entry control did not meet strict tolerance; inspect saved report. Do not repeat until pass.'
    print('PASS: source scope',guard['unchangedExistingFiles'],'unchanged files; 21 exact replay narrative states; 28 fresh A/B images; two exact fresh/default reference canvases; original veil variants retained:',len(initial_variants),flush=True)

if __name__=='__main__':
    import sys
    if '--scope-only'in sys.argv:
        result=scope_guard();print('PASS: source scope;',result['unchangedExistingFiles'],'original files unchanged',flush=True)
    else:main()
