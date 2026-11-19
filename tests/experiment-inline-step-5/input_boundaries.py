"""Exercise real input in the scene window and on the surrounding site."""
from pathlib import Path
import sys

from playwright.sync_api import Error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'about-refresh-final'))
from support import Run


STAGE = '.experiment-window-stage'
FRAME = f'{STAGE} iframe'
SCENE = 'article[data-experiment-station=C2]'
ARCHIVE = '.experiment-project-archive'
GUIDE = '#tour-guide'
LAWSON = 'lawson'
BOTTLE = 'bottle-ocean'
PROFILES = {
    LAWSON: {'canvas': '#viewport', 'panel': '#panel', 'toggle': '#panel-collapse', 'slider': '#time-slider',
             'camera': '() => ({position:__LAWSON__.debugDoor().cam, projection:__LAWSON__.api.project([3,1,2])})'},
    BOTTLE: {'canvas': '#gl', 'panel': '.panel-scroll', 'toggle': '#panel-toggle', 'slider': '#waveHeight',
             'camera': '() => __bottleOcean.cameraRig.getState()'},
}
r = Run()


def snapshot(page):
    return page.evaluate('''() => {
      const h=document.querySelector('#tour-host');
      return {url:location.href, y:scrollY, h:h.dataset.displayH, target:h.dataset.targetH,
        camera:h.dataset.cameraPosition, lookAt:h.dataset.cameraTarget, anchor:document.querySelector('main').dataset.flowAnchor??null};
    }''')


def tab(page, project):
    return page.locator(f'[data-project-select="{project}"]')


def enter(page):
    r.go(page, 'C2')
    if page.locator('main').get_attribute('data-reading-mode') == 'stable':
        page.locator(SCENE).evaluate('''article => scrollBy({
          top: article.getBoundingClientRect().top-document.querySelector('.tour-header').getBoundingClientRect().bottom-16,
          behavior:'instant'
        })''')


def choose(page, project):
    if tab(page, project).get_attribute('aria-selected') != 'true':
        r.activate(tab(page, project))
    return r.wait_scene(page, project)


def at_control(frame, profile):
    assert frame.evaluate('''s => [document.documentElement, document.body, document.querySelector(s)].every(
      e => getComputedStyle(e).overscrollBehavior === 'contain')''', profile['panel'])


def native_audit(frame):
    frame.evaluate('''() => {
      window.__testSceneInput=[];
      for (const type of ['pointerdown','pointerup','pointercancel','pointermove','wheel','focusin','keydown','input']) {
        document.addEventListener(type,e=>{
          if(e.isTrusted) window.__testSceneInput.push({type, id:e.target?.id, x:e.clientX, y:e.clientY,
            pointer:e.pointerType, key:e.key, wheel:e.deltaY});
        },{capture:true,passive:true});
      }
    }''')


def frame_box(page):
    box = page.locator(FRAME).bounding_box()
    assert box
    return box


def in_frame(page, point):
    return page.evaluate('([x,y])=>document.elementFromPoint(x,y)?.matches(".experiment-scene-mount iframe")===true', point)


def canvas_point(page, frame, profile, room=0):
    box = frame_box(page)
    viewport_height = page.evaluate('innerHeight')
    header_end = page.locator('.tour-header').bounding_box()['height']
    points = frame.evaluate('''({selector,top,bottom,room})=>{
      const canvas=document.querySelector(selector), points=[];
      const y0=Math.max(24,top), y1=Math.min(innerHeight-28,bottom);
      for(const y of [.45,.28,.65,.13,.82].map(p=>y0+(y1-y0)*p)) {
        for(const x of [.31,.22,.41,.14,.08,.5].map(p=>innerWidth*p)) {
          if ([x,x-room,x+room].every(a=>document.elementFromPoint(a,y)===canvas)) points.push([x,y]);
        }
      }
      return points;
    }''', {'selector': profile['canvas'], 'top': header_end+12-box['y'], 'bottom': viewport_height-18-box['y'], 'room': room})
    for x, y in points:
        point = (box['x'] + x, box['y'] + y)
        if 0 <= point[1] <= viewport_height and in_frame(page, point):
            return point
    raise AssertionError(('No visible canvas point', box, profile['canvas'], room))


def camera_change(frame, profile, initial):
    frame.wait_for_function(f'''initial => {{
      const now=({profile['camera']})();
      return now.position.some((v,i)=>Math.abs(v-initial.position[i])>.025);
    }}''', arg=initial, timeout=7000)
    return frame.evaluate(profile['camera'])


def wheel_canvas(page, frame, profile, delta=390):
    before = frame.evaluate(profile['camera'])
    page.mouse.move(*canvas_point(page, frame, profile))
    page.mouse.wheel(0, delta)
    after = camera_change(frame, profile, before)
    return [before, after]


def drag_canvas(page, frame, profile):
    old = frame.evaluate(profile['camera'])
    x, y = canvas_point(page, frame, profile)
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(frame_box(page)['x']-10, y+25, steps=12)
    page.mouse.up()
    return [old, camera_change(frame, profile, old)]


def scroll_values(locator):
    return locator.evaluate('e=>[e.scrollTop,e.scrollHeight-e.clientHeight]')


def wheel_panel(page, panel):
    box = panel.bounding_box()
    assert box and box['height'] > 40
    point = (box['x']+17, box['y']+box['height']/2)
    page.mouse.move(*point)
    _, limit = scroll_values(panel)
    assert limit > 25, (panel, limit)
    def wheel_to(direction):
        for _ in range(3):
            page.mouse.wheel(0, direction*(limit+240))
            reached = panel.evaluate('''(e,down)=>new Promise(resolve=>{
              const expected=down?e.scrollHeight-e.clientHeight:0, end=performance.now()+1100;
              function wait(){
                const reached=Math.abs(e.scrollTop-expected)<=1;
                if(reached||performance.now()>end) resolve(reached); else requestAnimationFrame(wait);
              }
              wait();
            })''', direction > 0)
            if reached:
                return scroll_values(panel)
        raise AssertionError((direction, scroll_values(panel)))

    bottom = wheel_to(1)
    page.mouse.wheel(0, 420)
    page.wait_for_timeout(245)
    assert scroll_values(panel) == bottom
    top = wheel_to(-1)
    page.mouse.wheel(0, -420)
    page.wait_for_timeout(245)
    assert scroll_values(panel) == top
    return {'top': top, 'bottom': bottom}


def desktop(page, project):
    enter(page)
    frame = choose(page, project)
    profile = PROFILES[project]
    native_audit(frame)
    before = snapshot(page)
    zoom = wheel_canvas(page, frame, profile)
    assert snapshot(page) == before
    drag = drag_canvas(page, frame, profile)
    assert snapshot(page) == before

    panel = frame.locator(profile['panel'])
    panel_scroll = wheel_panel(page, panel)
    assert snapshot(page) == before
    audit = frame.evaluate('window.__testSceneInput')
    assert any(e['type'] == 'pointerup' and e['x'] < 0 for e in audit), audit[-16:]
    assert sum(e['type'] == 'wheel' for e in audit) >= 5, audit[-10:]
    at_control(frame, profile)
    r.checkpoint(page, project)
    r.go(page, 'C3')
    page.locator(FRAME).wait_for(state='detached')
    assert frame.is_detached()
    r.go(page, 'water')
    after = snapshot(page)
    assert abs(float(after['h'])-11.5) < .006 and after['y'] > before['y']
    return {'nativeDrag': drag, 'nativeZoom': zoom, 'controlPanel': panel_scroll,
            'parentBeforeAndAfterInnerInput': before, 'parentAfterOutsideWheel': after, 'crossBorderPointerUp': True}


def focus_state(page, frame):
    return [page.evaluate('document.activeElement?.matches(".experiment-scene-mount iframe")===true'),
            frame.evaluate('''() => {const e=document.activeElement;return {id:e.id,tag:e.tagName,tabIndex:e.tabIndex};}''')]


def keys(page):
    enter(page)
    results = []
    for project, profile in PROFILES.items():
        frame = choose(page, project)
        before = snapshot(page)
        tab(page, project).focus()
        for n in range(1, 5):
            page.keyboard.press('Tab')
            inside, first = focus_state(page, frame)
            if inside and first['tag'] in ('BUTTON', 'INPUT', 'A'):
                break
        else:
            raise AssertionError((project, 'first original control unreachable', first))
        for back in range(1, 5):
            page.keyboard.press('Shift+Tab')
            if tab(page, project).evaluate('e=>e===document.activeElement'):
                break
        else:
            raise AssertionError((project, 'failed to return to selected tab'))
        inner_path = []
        for i in range(85):
            page.keyboard.press('Tab')
            if page.locator(f'{ARCHIVE} summary').evaluate('e=>e===document.activeElement'):
                break
            in_child, focus = focus_state(page, frame)
            assert in_child, focus
            inner_path.append(focus['id'] or focus['tag'])
        else:
            raise AssertionError((project, 'failed to leave original controls', inner_path))
        assert len(inner_path) >= 20

        slider = frame.locator(profile['slider'])
        initial = float(slider.input_value())
        slider.press('ArrowRight')
        changed = float(slider.input_value())
        assert changed > initial and tab(page, project).get_attribute('aria-selected') == 'true'
        native_escape = None
        if project == BOTTLE:
            frame.locator('[data-edit=rock]').press('Enter')
            assert frame.evaluate('__bottleOcean.state.editMode') == 'rock'
            page.keyboard.press('Escape')
            assert frame.evaluate('__bottleOcean.state.editMode') is None
            assert focus_state(page, frame)[0]
            native_escape = 'bottle edit cancelled'
        assert snapshot(page) == before
        results.append({'project': project, 'firstOriginalControl': first, 'backwardTabCount': back,
                        'forwardTabCount': len(inner_path)+1, 'lastOriginalControl': inner_path[-1],
                        'slider': [initial, changed], 'escape': native_escape})
    # Live layout measurements must leave the actual child control focused.
    slider = frame.locator('#waveHeight')
    slider.focus()
    width = frame_box(page)['width']
    page.set_viewport_size({'width':1464,'height':900})
    page.wait_for_function('''w=>{
      const m=document.querySelector('main');
      const c=JSON.parse(m.dataset.readingCapacity).stations.find(s=>s.id==='C2');
      return Math.round(c.bounds[2]-28)===Math.round(w+24);
    }''', arg=width)
    assert r.wait_scene(page, BOTTLE) == frame
    assert focus_state(page, frame)[1]['id'] == 'waveHeight'
    wave = float(slider.input_value())
    page.keyboard.press('ArrowLeft')
    assert float(slider.input_value()) < wave
    return {'keyboardPaths': results, 'parent': snapshot(page), 'focusedControlAfterLayoutMeasurement': 'waveHeight'}


def guide_at_window(page):
    page.locator(GUIDE).click()
    page.wait_for_function('''() => {
      const h=document.querySelector('#tour-host');
      return h.dataset.guideStation==='C2'&&h.dataset.guidePhase==='reading';
    }''', timeout=10000)
    assert page.locator(GUIDE).get_attribute('aria-pressed') == 'true'


def assert_guide_handover(page, before):
    host = page.locator('#tour-host')
    page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="paused"', timeout=4500)
    assert host.get_attribute('data-guide-reason') == '已交还场景操作，可从当前位置继续导览。'
    assert host.get_attribute('data-guide-deadline') == ''
    assert snapshot(page) == before


def guide_input(page):
    enter(page)
    frame = choose(page, BOTTLE)
    profile = PROFILES[BOTTLE]
    guide_at_window(page)
    before = snapshot(page)
    page.mouse.move(*canvas_point(page, frame, profile))
    page.wait_for_timeout(330)
    assert page.locator(GUIDE).get_attribute('aria-pressed') == 'true'
    zoom = wheel_canvas(page, frame, profile)
    assert_guide_handover(page, before)

    guide_at_window(page)
    drag = drag_canvas(page, frame, profile)
    assert_guide_handover(page, before)

    # Start through the existing control without relocating focus from the child.
    slider = frame.locator('#waveHeight')
    slider.focus()
    page.locator(GUIDE).evaluate('button=>button.click()')
    page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"')
    assert focus_state(page, frame)[1]['id'] == 'waveHeight'
    start = float(slider.input_value())
    page.keyboard.press('ArrowRight')
    assert float(slider.input_value()) > start
    assert_guide_handover(page, before)
    assert frame.evaluate('__bottleOcean.state.paused') is False

    guide_at_window(page)
    assert snapshot(page) == before
    page.locator(GUIDE).click()
    return {'hoverKeptGuide': True, 'handoverInputs': ['wheel', 'drag', 'ArrowRight'],
            'nativeZoom': zoom, 'nativeDrag': drag, 'resumedGuideFromSamePosition': before}


def guide_touch(page):
    enter(page)
    frame = choose(page, LAWSON)
    before = snapshot(page)
    guide_at_window(page)
    control = frame.locator('#panel-collapse')
    initial = frame.locator('#panel').evaluate('e=>e.classList.contains("collapsed")')
    control.tap()
    assert frame.locator('#panel').evaluate('e=>e.classList.contains("collapsed")') != initial
    assert_guide_handover(page, before)
    return {'handoverInput': 'native control touch', 'parent': before, 'panelChanged': True}


def fallback(page):
    attempts = []

    def route_entry(route):
        attempts.append(route)
        if len(attempts) <= 2:
            return
        if len(attempts) < 5:
            route.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Invalid scene test document</title>')
        else:
            route.continue_()

    page.route('**/experiments/lawson/index.html', route_entry)
    exited = []
    for state in ('loading', 'slow', 'error'):
        enter(page)
        page.locator(FRAME).wait_for(state='attached')
        page.locator(f'{STAGE}[data-scene-state={state}]').wait_for()
        assert not page.locator(FRAME).is_visible()
        box = page.locator(STAGE).bounding_box()
        before = snapshot(page)
        delta = page.evaluate('10.83/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
        page.mouse.move(box['x']+box['width']*.26, box['y']+box['height']*.42)
        page.mouse.wheel(0, delta)
        page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.83)<.006')
        page.locator(FRAME).wait_for(state='detached')
        if state in ('loading', 'slow'):
            try:
                attempts[-1].fulfill(status=200, content_type='text/html', body='<!doctype html><title>Late test response</title>')
            except Error:
                pass
        exited.append({'state': state, 'before': before, 'after': snapshot(page)})
    enter(page)
    page.locator(f'{STAGE}[data-scene-state=error]').wait_for()
    before = snapshot(page)
    old = page.locator(FRAME).element_handle().content_frame()
    page.locator('.experiment-scene-retry').click()
    recovered = r.wait_scene(page, LAWSON)
    assert old.is_detached() and len(attempts) == 5
    zoom = wheel_canvas(page, recovered, PROFILES[LAWSON])
    slider = recovered.locator('#time-slider')
    value = float(slider.input_value())
    slider.press('ArrowRight')
    assert float(slider.input_value()) > value
    assert snapshot(page) == before
    bottle = choose(page, BOTTLE)
    assert recovered.is_detached()
    new_zoom = wheel_canvas(page, bottle, PROFILES[BOTTLE])
    assert snapshot(page) == before
    return {'coverWheel': exited, 'retryKeptParent': before, 'entryAttempts': len(attempts),
            'nativeZoomAfterRetry': zoom, 'nativeZoomAfterSwitch': new_zoom}


def archive(page):
    enter(page)
    choose(page, LAWSON)
    toggle = page.locator(f'{ARCHIVE} summary')
    toggle.click()
    content = page.locator(f'{ARCHIVE} .experiment-archive-content')
    content.wait_for()
    before = snapshot(page)
    inner = wheel_panel(page, content)
    assert snapshot(page) == before
    content.focus()
    page.keyboard.press('Escape')
    assert toggle.evaluate('e=>e===document.activeElement')
    r.stable(page)
    enter(page)
    toggle.click()
    content.scroll_into_view_if_needed()
    box = content.bounding_box()
    h = page.evaluate('innerHeight')
    y = min(h-48, box['y']+box['height']/2)
    flow_before = snapshot(page)['y']
    page.mouse.move(box['x']+box['width']/2, y)
    page.mouse.wheel(0, 240)
    page.wait_for_function('y=>scrollY>y+35', arg=flow_before)
    after_wheel = snapshot(page)['y']
    page.wait_for_timeout(650)
    after_layout = snapshot(page)['y']
    assert after_layout > flow_before+35, (flow_before, after_wheel, after_layout)
    return {'immersiveArchiveScroll': inner, 'parentKept': before, 'stableArchiveFlow': [flow_before, after_layout],
            'firstStableWheel': after_wheel, 'scrollRetainedAfterLayout': True}


def gesture(page, client, starts, ends):
    def send(kind, fraction):
        points = [{'x': a[0]+(b[0]-a[0])*fraction, 'y': a[1]+(b[1]-a[1])*fraction, 'id': i+1}
                  for i, (a,b) in enumerate(zip(starts,ends))]
        client.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [] if kind == 'touchEnd' else points})
    send('touchStart', 0)
    for step in range(1, 10):
        send('touchMove', step/9)
        page.wait_for_timeout(17)
    send('touchEnd', 1)
    page.wait_for_timeout(210)


def touch_limits(page):
    h = page.evaluate('innerHeight')
    header = page.locator('.tour-header').bounding_box()
    return [header['y']+header['height']+12, h-18]


def control_point(control, x_fraction=.5):
    b = control.bounding_box()
    assert b and b['height'] > 0, control
    return (b['x']+x_fraction*b['width'], b['y']+.5*b['height'])


def reveal_control(page, client, control, room=0, x_fraction=.5):
    for _ in range(5):
        lo, hi = touch_limits(page)
        point = control_point(control, x_fraction)
        if lo+room <= point[1] <= hi-room and in_frame(page, point):
            return point
        delta = (lo+hi)/2 - point[1]
        start = lo+10 if delta > 0 else hi-8
        end = max(lo+2, min(hi-2, start+delta))
        before = page.evaluate('scrollY')
        assert not in_frame(page, (7, start))
        gesture(page, client, [(7,start)], [(7,end)])
        page.wait_for_function('y=>Math.abs(scrollY-y)>2', arg=before, timeout=3000)
    raise AssertionError(('Control unreadable from the parent margin', control, point))


def collapsed(frame, profile):
    return frame.locator(profile['toggle']).evaluate('e=>e.closest("aside").classList.contains("collapsed")')


def set_panel(page, client, frame, profile, folded):
    if collapsed(frame, profile) == folded:
        return
    toggle = frame.locator(profile['toggle'])
    click = reveal_control(page, client, toggle)
    page.touchscreen.tap(*click)
    toggle.evaluate('''async e=>{
      const panel=e.closest('aside');panel.getBoundingClientRect();
      await Promise.allSettled(panel.getAnimations({subtree:true}).filter(a=>Number.isFinite(a.effect.getComputedTiming().endTime)).map(a=>a.finished));
    }''')
    assert collapsed(frame, profile) == folded


def touch_panel_to_end(page, client, frame, profile):
    panel = frame.locator(profile['panel'])
    reveal_control(page, client, panel, room=40)
    before = snapshot(page)
    start_scroll, maximum = scroll_values(panel)
    assert maximum > 20
    for _ in range(22):
        if scroll_values(panel)[0] >= maximum-1:
            break
        b = panel.bounding_box()
        lo, hi = touch_limits(page)
        header = 32 if profile['panel'] == '#panel' else 8
        y0, y1 = max(lo+2, b['y']+header), min(hi-2, b['y']+b['height']-8)
        x = b['x']+12
        assert y1-y0 >= 40 and in_frame(page,(x,y1)), (b, lo, hi)
        gesture(page, client, [(x,y1)], [(x,y0)])
        assert snapshot(page) == before
    end_scroll = scroll_values(panel)[0]
    assert end_scroll >= maximum-1, (profile['panel'], start_scroll, end_scroll, maximum)
    return [start_scroll, end_scroll]


def touch_scene(page):
    enter(page)
    result = []
    client = page.context.new_cdp_session(page)
    try:
        for project, profile in PROFILES.items():
            enter(page)
            frame = choose(page, project)
            at_control(frame, profile)
            native_audit(frame)
            set_panel(page, client, frame, profile, True)
            before_drag = snapshot(page)
            camera = frame.evaluate(profile['camera'])
            x, y = canvas_point(page, frame, profile)
            gesture(page, client, [(x,y)], [(frame_box(page)['x']-8,min(touch_limits(page)[1],y+32))])
            drift = camera_change(frame, profile, camera)
            assert snapshot(page) == before_drag
            captured = frame.evaluate('window.__testSceneInput.some(e=>e.type==="pointerup"&&e.pointer==="touch"&&e.x<0)')
            assert captured

            x, y = canvas_point(page, frame, profile, room=58)
            view = frame.evaluate(profile['camera'])
            gesture(page, client, [(x-24,y),(x+24,y)], [(x-54,y),(x+54,y)])
            pinch = camera_change(frame, profile, view)
            assert snapshot(page) == before_drag

            set_panel(page, client, frame, profile, False)
            slider = frame.locator(profile['slider'])
            point = reveal_control(page, client, slider, x_fraction=.3 if project == LAWSON else .72)
            initial = float(slider.input_value())
            before_slider = snapshot(page)
            page.touchscreen.tap(*point)
            changed = float(slider.input_value())
            assert changed != initial and snapshot(page) == before_slider
            to_end = touch_panel_to_end(page, client, frame, profile)

            bottom = '#btn-reset-cam' if project == LAWSON else '#pause-button'
            point = reveal_control(page, client, frame.locator(bottom))
            before_bottom = snapshot(page)
            page.touchscreen.tap(*point)
            if project == LAWSON:
                assert frame.evaluate('__LAWSON__.state.cameraMode') == 'hero'
            else:
                assert frame.evaluate('__bottleOcean.state.paused')
            assert snapshot(page) == before_bottom
            result.append({'project':project, 'viewport':frame.evaluate('() => [innerWidth,innerHeight]'),
                           'drag':[camera,drift], 'pinch':[view,pinch], 'slider':[initial,changed], 'panelScroll':to_end,
                           'controlAtBottom':bottom, 'crossBorderTouchUp':captured})
        before_outside = snapshot(page)
        lo, hi = touch_limits(page)
        box = frame_box(page)
        start_y = min(hi-4, box['y']+box['height']-48)
        assert start_y-90 > lo
        # The start is on the main document even though the path ends over the window.
        outside = (7,start_y)
        target = (box['x']+20,start_y-90)
        inner_starts = frame.evaluate('window.__testSceneInput.filter(e=>e.type==="pointerdown").length')
        assert not in_frame(page, outside)
        gesture(page, client, [outside], [target])
        page.wait_for_function('y=>scrollY>y+20', arg=before_outside['y'], timeout=4500)
        assert in_frame(page, target)
        assert frame.evaluate('window.__testSceneInput.filter(e=>e.type==="pointerdown").length') == inner_starts
        after = snapshot(page)
        r.go(page, 'water')
        page.locator(FRAME).wait_for(state='detached')
        return {'nativeTouch':result, 'outsideSwipe':[before_outside,after]}
    finally:
        client.detach()


def standalone_touch(page):
    results = []
    for project, profile in PROFILES.items():
        original = page.context.new_page()
        original.set_viewport_size({'width':337, 'height':473})
        try:
            original.goto(r.origin+f'experiments/{project}/index.html', wait_until='domcontentloaded')
            original.wait_for_function('window.__LAWSON__?.ready===true||window.__bottleOcean?.ready===true', timeout=60000)
            original.locator('#loader').wait_for(state='hidden')
            assert original.evaluate('() => [innerWidth, innerHeight]') == [337,473]
            point = original.evaluate('''selector=>{
              const canvas=document.querySelector(selector);
              for(const y of [40,45,52,150,210]) for(const x of [85,105,130]) {
                if([x-56,x,x+56].every(a=>document.elementFromPoint(a,y)===canvas)) return [x,y];
              }return null;
            }''', profile['canvas'])
            assert point, project
            x, y = point
            old = original.evaluate(profile['camera'])
            client = original.context.new_cdp_session(original)
            try:
                gesture(original, client, [(x-24,y),(x+24,y)], [(x-54,y),(x+54,y)])
            finally:
                client.detach()
            actual = camera_change(original, profile, old)
            results.append({'project':project, 'viewport':[337,473], 'pinch':[old,actual]})
        finally:
            original.close()
    return {'originalTouchReference':results}


try:
    r.case('desktop-lawson-input', lambda p: desktop(p, LAWSON))
    r.case('desktop-bottle-input', lambda p: desktop(p, BOTTLE))
    r.case('keyboard-scene-boundaries', keys)
    r.case('guide-child-input', guide_input)
    r.case('guide-child-touch', guide_touch, touch=True)
    r.case('cover-and-retry-input', fallback)
    r.case('archive-scroll-boundary', archive)
    r.case('portrait-touch-boundaries', touch_scene, size=(390, 844), touch=True)
    r.case('landscape-touch-boundaries', touch_scene, size=(844, 390), touch=True)
    r.case('standalone-native-pinch-reference', standalone_touch, size=(390, 844), touch=True)
finally:
    good = r.finish()
raise SystemExit(0 if good else 1)
