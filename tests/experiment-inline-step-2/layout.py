"""Measure the scene window and exercise the original controls at its exact size."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiment-inline-step-1'))
from verify import Run, choice, position, tab, two_columns


WINDOW = '.experiment-project-window'
STAGE = '.experiment-window-stage'


def geometry(page):
    return page.evaluate('''() => {
      const box = sel => { const {left,top,right,bottom,width,height} = document.querySelector(sel).getBoundingClientRect();
        return {left,top,right,bottom,width,height}; };
      const main=document.querySelector('main');
      return {mode:main.dataset.readingMode, viewport:[innerWidth,innerHeight], stage:box('.experiment-window-stage'),
        header:box('.tour-header'), nav:box('.tour-stops'), footer:box('.tour-footer'),
        window:box('.experiment-project-window'), reader:box('.experiment-reading'),
        controls:box('.experiment-entry-actions'), overflow:document.documentElement.scrollWidth-innerWidth,
        capacity:JSON.parse(main.dataset.readingCapacity).stations.find(s=>s.id==='C2')};
    }''')


def same_stage(first, second):
    assert all(abs(first['stage'][key]-second['stage'][key]) <= 1 for key in first['stage']), (first['stage'],second['stage'])


def align_window(page):
    page.locator(WINDOW).evaluate('e=>e.scrollIntoView({block:"start",behavior:"instant"})')
    page.wait_for_function('''() => document.querySelector('.experiment-project-selector').getBoundingClientRect().top >=
        document.querySelector('.tour-header').getBoundingClientRect().bottom''')


def visible_control(control):
    control.scroll_into_view_if_needed()
    hit = control.evaluate('''e => {
      const b=e.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const target=document.elementFromPoint(x,y);
      return {reachable:b.width>0 && b.height>0 && x>=0 && x<innerWidth && y>=0 && y<innerHeight && e.contains(target),
        center:[x,y],hit:target?.id || target?.className || target?.tagName, viewport:[innerWidth,innerHeight]};
    }''')
    assert hit['reachable'], (control,hit)


def original_controls(context, origin, size, activate):
    results = []
    for identifier in ('lawson','bottle-ocean'):
        original = context.new_page()
        faults = []
        original.on('pageerror', lambda e: faults.append(str(e)))
        try:
            original.set_viewport_size(size)
            original.goto(f'{origin}experiments/{identifier}/index.html', wait_until='domcontentloaded')
            lawson = identifier == 'lawson'
            ready = 'window.__LAWSON__?.ready===true' if lawson else 'window.__bottleOcean?.ready===true'
            original.wait_for_function(ready, timeout=90000)
            original.locator('#loader').wait_for(state='hidden', timeout=30000)
            assert original.evaluate('() => [innerWidth,innerHeight]') == [size['width'],size['height']]
            panel = original.locator('#panel' if lawson else '#control-panel')
            toggle = original.locator('#panel-collapse' if lawson else '#panel-toggle')
            if not panel.evaluate('e=>e.classList.contains("collapsed")'):
                activate(toggle)
            assert panel.evaluate('e=>e.classList.contains("collapsed")')
            activate(toggle)
            assert not panel.evaluate('e=>e.classList.contains("collapsed")')
            panel.evaluate('''async e => {
              e.getBoundingClientRect();
              await Promise.allSettled(e.getAnimations({subtree:true}).filter(animation =>
                Number.isFinite(animation.effect?.getComputedTiming().endTime)).map(animation=>animation.finished));
            }''')
            if lawson:
                visible_control(original.locator('#btn-reset-cam'))
                before = original.evaluate('__LAWSON__.state.roofVisible')
                activate(original.locator('#btn-roof'))
                assert original.evaluate('__LAWSON__.state.roofVisible') is not before
                scroller = panel
                tested = '重置视角与屋顶'
            else:
                slider = original.locator('#waveHeight')
                visible_control(slider)
                slider.press('End')
                assert original.evaluate('__bottleOcean.state.waveHeight') == 100
                visible_control(original.locator('[data-action="resetProps"]'))
                visible_control(original.locator('[data-action="screenshot"]'))
                scroller = original.locator('.panel-scroll')
                tested = '波高、恢复装饰及截图'
            scroll = scroller.evaluate('e=>({top:e.scrollTop,height:e.clientHeight,contentHeight:e.scrollHeight})')
            assert scroll['height'] > 0 and (scroll['top'] > 0 or scroll['height'] + 1 >= scroll['contentHeight']), scroll
            assert not faults, faults
            results.append({'project':identifier,'viewport':size,'nativeToggle':True,'tested':tested,'scroll':scroll})
        finally:
            original.close()
    return results


def exit_window(page):
    snapshot = geometry(page)
    if snapshot['mode'] == 'immersive':
        target = 10.83
        delta = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY', target)
        page.mouse.move(7, min(315, snapshot['viewport'][1]-40))
        page.mouse.wheel(0, delta)
        page.wait_for_function('document.querySelector(".experiment-reading").dataset.station==="C3"')
        page.wait_for_function('''() => Math.abs(Number(document.querySelector('#tour-host').dataset.displayH)-10.83)<.006 &&
            document.querySelector('.experiment-reading').getBoundingClientRect().width <= 500''')
    else:
        before = page.evaluate('scrollY')
        y = snapshot['viewport'][1] - 44
        if r.touch:
            client = page.context.new_cdp_session(page)
            client.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':7,'y':y}]})
            for offset in range(20, 161, 20):
                client.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':7,'y':y-offset}]})
            client.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
            client.detach()
        else:
            page.mouse.move(7,y)
            page.mouse.wheel(0,180)
        page.wait_for_function('y=>scrollY>y+25', arg=before)
        r.go(page, 'C3')
    page.locator('[data-stop="water"]').click()
    if snapshot['mode'] == 'immersive':
        page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-11.5)<.007')
    else:
        page.wait_for_function('document.querySelector("main").dataset.flowAnchor==="water"')


def layout(page, name, immersive):
    if name == 'desktop-1440':
        r.go(page, 'A2')
        r.go(page, 'C1')
        assert page.locator('.experiment-reading').get_attribute('data-layout') == 'side'
    r.go(page, 'C2')
    choice(page, 'lawson')
    snapshot = geometry(page)
    assert snapshot['mode'] == ('immersive' if immersive else 'stable'), snapshot
    if immersive:
        panel = snapshot['reader']
        assert snapshot['capacity']['fits'] and snapshot['nav']['left'] - panel['right'] >= 16, snapshot
        assert panel['top'] >= snapshot['header']['bottom'] + 16 and panel['bottom'] <= snapshot['footer']['top'] - 15.5, snapshot
        assert 558 <= snapshot['stage']['height'] <= 660, snapshot
        assert snapshot['stage']['width'] >= (1260 if name == 'desktop-1652' else 1100), snapshot
    else:
        align_window(page)
        snapshot = geometry(page)
        assert snapshot['stage']['width'] >= snapshot['viewport'][0]-65 and snapshot['stage']['height'] >= 380, snapshot
        if name == 'phone-390':
            assert 430 <= snapshot['stage']['height'] <= 500, snapshot
    two_columns(page)
    initial_position = position(page)
    page.screenshot(path=str(r.out/f'{name}-lawson.png'))

    held = []
    image_glob = '**/bottle-ocean-cover*.png'
    def hold_image(route):
        held.append(route)

    page.route(image_glob, hold_image)
    try:
        with page.expect_request(image_glob):
            r.activate(tab(page, 'bottle-ocean'))
        page.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="loading"')
        during_load = geometry(page)
        assert held
        same_stage(snapshot, during_load)
    finally:
        for route in held:
            route.continue_()
        page.unroute(image_glob)
    choice(page, 'bottle-ocean')
    between = geometry(page)
    same_stage(snapshot, between)
    two_columns(page)
    page.screenshot(path=str(r.out/f'{name}-bottle.png'))
    r.activate(tab(page, 'lawson'))
    choice(page, 'lawson')
    same_stage(snapshot, geometry(page))
    assert position(page) == initial_position

    size = {axis: round(snapshot['stage'][axis]) for axis in ('width','height')}
    originals = original_controls(page.context, r.origin, size, r.activate)
    exit_window(page)
    return {'window':snapshot,'loadingSecond':during_load,'loadedSecond':between,'originals':originals,'leftForWater':True}


if __name__ == '__main__':
    r = Run()
    try:
        for name, size, immersive, touch in [
            ('desktop-1440',(1440,900),True,False), ('desktop-1652',(1652,949),True,False),
            ('compact-907',(907,836),False,False), ('phone-390',(390,844),False,True),
            ('landscape-844',(844,390),False,True),
        ]:
            r.case(name, lambda page: layout(page,name,immersive), size=size, touch=touch)
    finally:
        passed = r.finish()
    raise SystemExit(0 if passed else 1)
