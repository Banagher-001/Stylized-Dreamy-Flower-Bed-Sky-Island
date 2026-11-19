"""Observe native horizontal drag before and after the mobile snap settles."""
from reading_support import Run, choose, tool_state

r = Run()


def touches(page):
    r.go(page, 'A3')
    choose(page, 'G6')
    rail = page.locator('.ar-tool-rail')
    rail.scroll_into_view_if_needed()
    page.wait_for_timeout(450)
    box = rail.bounding_box()
    x = min(box['x'] + box['width'] - 50, 330)
    y = box['y'] + min(130, box['height'] / 2)
    state = rail.evaluate('''e => ({x:e.scrollLeft, snap:getComputedStyle(e).scrollSnapType,
        pitch:e.querySelectorAll('.ar-tool-slot')[1].offsetLeft-e.querySelector('.ar-tool-slot').offsetLeft})''')
    assert state['snap'] == 'x mandatory' and state['pitch'] > 240
    client = page.context.new_cdp_session(page)

    def action(kind, point=None):
        client.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [] if point is None else [dict(x=point[0], y=point[1])]})

    # A deliberate swipe exceeds half of one card pitch. An undershoot is
    # allowed to move the rail during the gesture and snap back on release.
    action('touchStart', (x, y))
    samples = [state['x']]
    for step in range(1, 11):
        action('touchMove', (x - 24*step, y))
        page.wait_for_timeout(25)
        samples.append(rail.evaluate('e=>e.scrollLeft'))
    action('touchEnd')
    page.wait_for_timeout(650)
    snapped = rail.evaluate('e=>e.scrollLeft')
    assert max(samples) > state['pitch']/2 and snapped > state['x']+20, (state, samples, snapped)

    before_y = page.evaluate('scrollY')
    action('touchStart', (7, 550))
    for step in range(1, 8):
        action('touchMove', (7, 550 - 20*step))
        page.wait_for_timeout(25)
    action('touchEnd')
    page.wait_for_timeout(520)
    after_y = page.evaluate('scrollY')
    assert after_y > before_y+20
    t = tool_state(page)
    assert t['trackMode'] == 'native' and t['trackEnabled'] == 'false' and not t.get('detailPressed')
    return {'setup': state, 'duringHorizontalDrag': samples, 'settledX': snapped, 'pageY': [before_y, after_y], 'touchEmulation': True}


try:
    r.case('native-mobile-gesture-and-snap', touches, size=(390, 844), touch=True)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
