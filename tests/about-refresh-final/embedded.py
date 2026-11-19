"""Original controls, in-place archives, iframe isolation and native downloads."""
from support import Run
import hashlib, struct

r = Run()
PICK = r'''()=>{const b=__bottleOcean,T=b.THREE,e=b.environment,ray=new T.Raycaster(),v=new T.Vector3();const blocked=new Set([e.ocean,...e.lighthouse.hitObjects]),targets=[e.terrain,e.rocks].filter(Boolean);for(const o of e.raycastTargets)if(o&&!blocked.has(o)&&!blocked.has(o.parent)&&o.name!=='birds'&&o.name!=='seaBirds'&&!o.material?.transparent&&!targets.includes(o))targets.push(o);for(const z of[4,2,6,0,8,-2,-5])for(const x of[-3,-1,1,3,-5,5,8,-8]){v.set(x,e.getSandHeight(x,z),z).project(b.camera);const px=(v.x+1)*innerWidth/2,py=(1-v.y)*innerHeight/2;if(px<20||py<80||px>innerWidth-20||py>innerHeight-25||document.elementFromPoint(px,py)!==b.renderer.domElement)continue;ray.setFromCamera(new T.Vector2(px/innerWidth*2-1,1-py/innerHeight*2),b.camera);const h=ray.intersectObjects(targets,true)[0];if(h&&!b.bottle.isInsideCavity(h.point,.02))return{x:px,y:py,point:h.point.toArray()}}return null}'''
PROPS = '()=>{let a=[];__bottleOcean.scene.traverse(o=>{if(o.userData.propKind)a.push(o.userData.propKind)});return a}'

def download(page, frame, label):
    with page.expect_download(timeout=30000) as event:
        frame.locator('[data-action=screenshot]').click()
    d = event.value
    path = r.out / (label + '.png')
    d.save_as(str(path))
    raw = path.read_bytes()
    assert not d.failure() and raw[:8] == b'\x89PNG\r\n\x1a\n' and len(raw) > 10000
    return {'name': d.suggested_filename, 'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'size': list(struct.unpack('>II', raw[16:24]))}

def archive(page, identifier, frame):
    details = page.locator('.experiment-project-archive')
    summary = details.locator('summary')
    summary.click()
    content = details.locator(f'.experiment-archive-content[data-project-id="{identifier}"]')
    content.wait_for()
    page.wait_for_function('document.querySelector(".experiment-archive-content img")?.naturalWidth>0')
    assert content.locator('.experiment-archive-features section').count() == 3
    assert not frame.is_detached() and len(page.context.pages) == 1
    assert not page.locator('dialog[open]').count()
    summary.click()


def original_pages(page):
    r.go(page, 'C2')
    before = r.state(page)
    law = r.wait_scene(page, 'lawson')
    assert law.locator('button,input,.toggle').count() == 41
    bounds = page.locator('iframe').bounding_box()
    assert bounds == page.locator('.experiment-window-stage').bounding_box()
    law.locator('[data-preset=night]').click()
    law.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-22)<.02', timeout=60000)
    law.locator('#lights-all-off').click()
    assert not any(law.evaluate('Object.values(__LAWSON__.state.lights)'))
    law.locator('#lights-all-on').click()
    law.locator('#btn-roof').click()
    assert not law.evaluate('__LAWSON__.state.roofVisible')
    law.locator('[data-cam=interior]').click()
    assert law.evaluate('__LAWSON__.state.cameraMode') == 'interior'
    law.locator('#btn-help').click()
    assert law.locator('#help').is_visible()
    law.locator('#help-close').click()
    law.locator('#panel-collapse').click()
    assert law.locator('#panel').evaluate('e=>e.classList.contains("collapsed")')
    law.locator('#panel-collapse').click()
    original_law = law.evaluate('__LAWSON__.api.getState()')
    r.checkpoint(page, 'lawson-controls')
    archive(page, 'lawson', law)
    after_law = r.state(page)
    assert abs(after_law['y'] - before['y']) < 3
    assert after_law['host']['displayH'] == before['host']['displayH']
    bottle = r.open_scene(page, 'bottle-ocean')
    assert law.is_detached()
    assert bottle.locator('button,input').count() == 34
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 35
    bottle.locator('[data-quality=retro]').click()
    assert bottle.evaluate('__bottleOcean.post.getState().scale') == 3.8
    bottle.locator('#waveHeight').press('End')
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    bottle.locator('[data-toggle=dust]').click()
    assert not bottle.evaluate('__bottleOcean.environment.dust.visible')
    bottle.locator('[data-preset=top]').click()
    bottle.wait_for_function('Math.abs(__bottleOcean.cameraRig.getState().fov-44)<.01', timeout=60000)
    bottle.locator('[data-edit=rock]').click()
    point = bottle.evaluate(PICK)
    assert point, 'No actual unobscured raycast target'
    box = page.locator('iframe').bounding_box()
    page.mouse.click(box['x'] + point['x'], box['y'] + point['y'])
    bottle.wait_for_function('()=>{let n=0;__bottleOcean.scene.traverse(o=>{if(o.userData.propKind)n++});return n===1}')
    placed = bottle.evaluate(PROPS)
    assert placed == ['rock']
    bottle.locator('[data-action=undoProp]').click()
    assert bottle.evaluate(PROPS) == []
    bottle.locator('#waveHeight').focus()
    page.keyboard.press('Escape')
    assert bottle.evaluate('__bottleOcean.state.editMode') is None
    assert not page.locator('dialog[open]').count()
    bottle.locator('[data-action=pause]').click()
    assert bottle.evaluate('__bottleOcean.state.paused')
    paused_a = bottle.evaluate('__bottleOcean.getDiagnostics().simTime')
    page.wait_for_timeout(700)
    paused_b = bottle.evaluate('__bottleOcean.getDiagnostics().simTime')
    assert paused_a == paused_b
    native_download = download(page, bottle, 'bottle-native-export')
    r.checkpoint(page, 'bottle-controls')
    archive(page, 'bottle-ocean', bottle)
    r.go(page, 'C3')
    page.wait_for_function('!document.querySelector(".experiment-window-stage iframe")')
    assert bottle.is_detached()
    bottle2 = r.open_scene(page, 'bottle-ocean')
    defaults = bottle2.evaluate('({...__bottleOcean.state})')
    assert defaults['waveHeight'] == 35 and defaults['dust'] and not defaults['paused']
    r.open_project(page, 'courtyard', 'archive')
    page.locator('.tour-project-play').click()
    page.wait_for_function('document.querySelector(".tour-project-dialog video")?.currentTime>0', timeout=30000)
    clip = page.locator('.tour-project-dialog video').evaluate('e=>({t:e.currentTime,duration:e.duration,controls:e.controls})')
    assert clip['controls'] and clip['duration'] > 0
    r.close_project(page)
    assert page.locator('video,iframe').count() == 0
    return {'lawson': original_law, 'iframeBounds': bounds, 'actualPlacement': {'point': point, 'props': placed}, 'simulationPaused': [paused_a, paused_b], 'nativeDownload': native_download, 'reopenedOriginalDefaults': defaults, 'courtyardArchivePlayback': clip, 'returned': r.state(page)}

try:
    r.case('original-pages-isolation-and-downloads', original_pages)
finally:
    good = r.finish()
raise SystemExit(0 if good else 1)
