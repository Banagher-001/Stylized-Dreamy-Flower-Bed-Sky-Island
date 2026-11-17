"""Review a completed 600s raw run whose only failure was a wrong scroll observable.
No edits to raw evidence. Independently confirm actual transformed card movement.
The raw directory must be alongside --out as stability-3 (this recovery check is
specific to the step-14 audit; the normal reusable runner is stability.py).
"""
from support import Run, save
from pathlib import Path
import hashlib,json
r=Run()
raw=r.out.parent/'stability-3'

def review(page):
    report=json.loads((raw/'browser.json').read_text())
    check=report['checks'][0]
    assert check['status']=='失败'
    assert "assert len({x['railX'] for x in rows}) >= 3" in check['traceback']
    assert not check['errors'] and not check['httpFailures'] and not check['externalAttempts']
    assert not [x for x in check['requestFailures'] if not(x['error']=='net::ERR_ABORTED' and x['type'] in ['image','media','document'])]
    data=json.loads((raw/'samples.json').read_text());samples=data['samples'];actions=data['actions']
    duration=samples[-1]['elapsedSeconds']-samples[0]['elapsedSeconds']
    assert duration>=600 and len(samples)>=21 and len(actions)==9
    distances=[float(s['tools']['trackDistance']) for s in samples if s['tools'].get('trackDistance') is not None]
    assert len(set(distances))>=3
    for s in samples:
        assert s['cards']==22 and s['canvas']==1 and s['frames']==0
        assert {k:s['resources'][k] for k in ['geometries','textures','programs']}=={k:samples[0]['resources'][k] for k in ['geometries','textures','programs']}
    assert float(samples[-1]['sceneTime'])-float(samples[0]['sceneTime'])>60
    final=json.loads((raw/'ten-minute-real-clock-stability-failure.json').read_text())
    assert len({c['id'] for c in final['cards']})==22 and final['canvas']==1 and final['frames']==0 and not final['dialogs'] and not final['focus']['hidden']
    r.go(page,'A3')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"')
    page.mouse.move(24,300)
    page.wait_for_timeout(350)
    card=page.locator('.ar-tool-card[data-tool-id=comfyui]')
    before={'box':card.bounding_box(),'state':r.state(page)}
    page.wait_for_timeout(1500)
    after={'box':card.bounding_box(),'state':r.state(page)}
    assert before['state']['tools']['trackMode']=='program' and after['state']['tools']['trackMode']=='program'
    assert abs(after['box']['x']-before['box']['x'])>5
    assert float(after['state']['tools']['trackDistance'])>float(before['state']['tools']['trackDistance'])+10
    r.checkpoint(page,'actual-transform-movement')
    return {'rawRecord':'../stability-3/browser.json','rawRecordSHA256':hashlib.sha256((raw/'browser.json').read_bytes()).hexdigest(),'rawSamples':'../stability-3/samples.json','rawSamplesSHA256':hashlib.sha256((raw/'samples.json').read_bytes()).hexdigest(),'actualWallSeconds':duration,'sampleCount':len(samples),'actionCount':len(actions),'actions':actions,'rawRunnerHadIncorrectNativeScrollAssertion':True,'reviewDidNotEditRawEvidence':True,'correctTrackDistanceDistinctSamples':len(set(distances)),'trackDistanceSamples':distances,'nativeScrollSamples':[s['railX'] for s in samples],'actualMovementBefore':before,'actualMovementAfter':after,'baselineResources':samples[0]['resources'],'finalResources':samples[-1]['resources'],'clockModified':False,'RAFModified':False,'hardwareFPSClaimed':False}

try:
    r.case('ten-minute-record-review-and-actual-track-movement',review)
finally:
    good=r.finish()
raise SystemExit(0 if good else 1)
