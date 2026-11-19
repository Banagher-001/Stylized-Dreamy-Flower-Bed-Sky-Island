"""Exercise real touch on both page forms at the same visible canvas sizes."""
from pair_support import BOTTLE, BrowserRun, IFRAME, LANDSCAPE, LAWSON, PHONE, position


PROFILES = {
    LAWSON: {'panel': '#panel', 'fold': '#panel-collapse', 'canvas': '#viewport', 'slider': '#time-slider',
             'bottom': '#btn-reset-cam',
             'pose': '() => [...__LAWSON__.debugDoor().cam,...__LAWSON__.api.project([3,1,2])]',
             'value': '__LAWSON__.api.getStats().timeOfDay'},
    BOTTLE: {'panel': '.panel-scroll', 'fold': '#panel-toggle', 'canvas': '#gl', 'slider': '#waveHeight',
             'bottom': '#pause-button',
             'pose': '() => {const c=__bottleOcean.cameraRig.getState();return [...c.position,...c.target,c.distance]}',
             'value': '__bottleOcean.state.waveHeight'},
}


def swipe(page, client, starts, ends):
    def send(event, progress):
        points = [{'x':x+(a-x)*progress, 'y':y+(b-y)*progress, 'id':i+1}
                  for i, ((x,y),(a,b)) in enumerate(zip(starts, ends))]
        client.send('Input.dispatchTouchEvent', {'type':event,'touchPoints':points if event!='touchEnd' else []})
    send('touchStart', 0)
    for count in range(1, 10):
        send('touchMove', count/9)
        page.wait_for_timeout(17)
    send('touchEnd', 1)
    page.wait_for_timeout(190)


def screen_bounds(page, embedded):
    low = 12
    if embedded:
        header = page.locator('.tour-header').bounding_box()
        low = max(low, header['y']+header['height']+10)
    return low, page.viewport_size['height']-17


def control_point(page, client, control, embedded, fraction=.5, room=0):
    for _ in range(6):
        box = control.bounding_box()
        assert box and box['height'] > 0
        x, y = box['x']+box['width']*fraction, box['y']+box['height']/2
        low, high = screen_bounds(page, embedded)
        if low+room <= y <= high-room:
            return x, y
        assert embedded, (control, x, y)
        shift = (low+high)/2-y
        start = low+9 if shift>0 else high-7
        end = max(low+2, min(high-2, start+shift))
        previous = page.evaluate('scrollY')
        swipe(page, client, [(7,start)], [(7,end)])
        page.wait_for_function('y=>Math.abs(scrollY-y)>2', arg=previous, timeout=3500, polling=100)
    raise AssertionError(('Control outside the visible scene window', control, y))


def touch_controls(page, scene, side, project):
    embedded = side == 'embedded'
    profile = PROFILES[project]
    if project == LAWSON:
        for _ in range(2):
            if scene.evaluate('__LAWSON__.state.quality') == 'low':
                break
            scene.locator('#btn-settings').tap()
    scene.evaluate('''() => {
      window.__touchParity=[];
      for(const kind of ['input','pointerdown','click']) document.addEventListener(kind,e=>{
        if(e.isTrusted) window.__touchParity.push({kind,id:e.target.id,source:e.pointerType||null,value:e.target.value||null});
      },true);
    }''')
    client = page.context.new_cdp_session(page)

    def tap(selector, fraction=.5):
        point = control_point(page, client, scene.locator(selector), embedded, fraction)
        before = position(page)
        page.touchscreen.tap(*point)
        assert position(page) == before

    def set_fold(folded):
        fold = scene.locator(profile['fold'])
        is_folded = 'e=>e.closest("aside").classList.contains("collapsed")'
        if fold.evaluate(is_folded) != folded:
            tap(profile['fold'])
            assert fold.evaluate(is_folded) == folded
            fold.evaluate('''async e=>{
              const panel=e.closest('aside');panel.getBoundingClientRect();
              await Promise.allSettled(panel.getAnimations({subtree:true})
                .filter(a=>Number.isFinite(a.effect.getComputedTiming().endTime)).map(a=>a.finished));
            }''')

    def canvas_center():
        canvas = scene.locator(profile['canvas']).bounding_box()
        lo, hi = screen_bounds(page, embedded)
        lo, hi = max(lo,canvas['y']+80), min(hi,canvas['y']+canvas['height']-42)
        if hi-lo<25 and embedded:
            control_point(page, client, scene.locator(profile['canvas']), embedded)
            return canvas_center()
        x, y = canvas['x']+canvas['width']*.37,(lo+hi)/2
        frame = page.locator(IFRAME).bounding_box() if embedded else {'x':0,'y':0}
        for offset in (-56,0,56):
            hit = scene.evaluate('p=>document.elementFromPoint(p.x,p.y)?.matches(p.canvas)',
                                 {'x':x+offset-frame['x'],'y':y-frame['y'],'canvas':profile['canvas']})
            assert hit,(project, side, canvas, [x+offset,y])
        return x, y

    def motion(starts, ends):
        before = position(page)
        pose = scene.evaluate(profile['pose'])
        swipe(page, client, starts, ends)
        scene.wait_for_function(f'pose=>JSON.stringify(({profile["pose"]})())!==JSON.stringify(pose)',
                                arg=pose, timeout=30000, polling=100)
        after = scene.evaluate(profile['pose'])
        assert position(page) == before
        return [pose, after]

    try:
        set_fold(True)
        x, y = canvas_center()
        drag = motion([(x,y)], [(x+48,y+35)])
        x, y = canvas_center()
        pinch = motion([(x-21,y),(x+21,y)], [(x-55,y),(x+55,y)])
        set_fold(False)
        slider = scene.locator(profile['slider'])
        original = float(slider.input_value())
        tap(profile['slider'], .30 if project == LAWSON else .73)
        changed = float(slider.input_value())
        assert changed != original
        scene.wait_for_function(f'n=>Math.abs(({profile["value"]})-n)<.025', arg=changed, timeout=65000, polling=100)
        assert scene.evaluate('id=>window.__touchParity.some(e=>e.kind==="input"&&e.id===id)', profile['slider'][1:])

        if project == LAWSON:
            tap('[data-preset=night]')
            scene.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-22)<.02', timeout=60000, polling=100)
        panel = scene.locator(profile['panel'])
        control_point(page, client, panel, embedded, room=24)
        scroll = 'e=>[e.scrollTop,e.scrollHeight-e.clientHeight]'
        start, maximum = panel.evaluate(scroll)
        before = position(page)
        for _ in range(20):
            if panel.evaluate(scroll)[0] >= maximum-1:
                break
            box = panel.bounding_box()
            lo, hi = screen_bounds(page, embedded)
            y0 = max(lo+2,box['y']+(36 if project==LAWSON else 8))
            y1 = min(hi-2,box['y']+box['height']-8)
            assert y1-y0 > 35, (project, side, box, lo, hi)
            swipe(page, client, [(box['x']+12,y1)], [(box['x']+12,y0)])
            assert position(page) == before
        end = panel.evaluate(scroll)[0]
        assert maximum > 0 and end >= maximum-1, (project, start, end, maximum)
        tap(profile['bottom'])
        if project == LAWSON:
            assert scene.evaluate('__LAWSON__.state.cameraMode') == 'hero'
        else:
            assert scene.evaluate('__bottleOcean.state.paused')
        events = scene.evaluate('window.__touchParity')
        assert any(event['kind']=='pointerdown' and event['source']=='touch' for event in events)
        page.screenshot(path=str(r.out/f'{project}-{page.viewport_size["width"]}-{side}.png'),timeout=20000)
        return {'comparison':{'touchDrag':True,'pinch':True,'nativeSlider':True,'panelEndControl':True},
                'poseAfterTouch':{'drag':drag,'pinch':pinch},'slider':[original,changed],
                'panelScroll':[start,end,maximum],'events':events}
    finally:
        client.detach()


def bottle_keys(page, scene, side):
    canvas = scene.locator('#gl').bounding_box()
    page.mouse.click(canvas['x']+120,canvas['y']+185)
    initial = position(page)
    page.keyboard.press('h')
    assert scene.evaluate('document.body.classList.contains("ui-hidden")')
    page.keyboard.press('h')
    assert not scene.evaluate('document.body.classList.contains("ui-hidden")')
    scene.locator('#waveHeight').focus()
    page.keyboard.press('h')
    page.keyboard.press('Space')
    assert not scene.evaluate('document.body.classList.contains("ui-hidden") || __bottleOcean.state.paused')
    page.mouse.click(canvas['x']+120,canvas['y']+185)
    page.keyboard.press('Space')
    assert scene.evaluate('__bottleOcean.state.paused')
    page.keyboard.press('Space')
    assert not scene.evaluate('__bottleOcean.state.paused')
    scene.locator('#pause-button').focus()
    page.keyboard.press('Space')
    assert scene.evaluate('__bottleOcean.state.paused')
    page.keyboard.press('Space')
    assert not scene.evaluate('__bottleOcean.state.paused')
    scene.locator('[data-edit=rock]').click()
    assert scene.evaluate('__bottleOcean.state.editMode==="rock"')
    scene.locator('#waveHeight').focus()
    page.keyboard.press('Escape')
    assert scene.evaluate('__bottleOcean.state.editMode===null') and position(page)==initial
    return {'comparison':{'hHidesAndRestores':True,'spacePausesAndResumes':True,'spaceButtonOnce':True,
                          'escapeExitsEdit':True,'inputFocusProtected':True}}


r = BrowserRun()
try:
    for form, host in (('portrait',PHONE), ('landscape',LANDSCAPE)):
        for project in (LAWSON,BOTTLE):
            r.pairs(f'{project}-{form}-touch',project,
                    lambda page, scene, side, project=project: touch_controls(page,scene,side,project),host=host,touch=True)
    r.pairs('bottle-original-keys',BOTTLE,bottle_keys)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
