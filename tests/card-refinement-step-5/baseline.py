"""Baseline departures and seam behavior on the exact Step 4 bundle."""
from departure_support import DESKTOP, Run, enter_paused, phase, points, progress, ready_automatic, tool_state, paused_overflow

r = Run()


def baseline(page):
    ready_automatic(r, page)
    cycle0 = int(tool_state(page).get('trackCycles',0))
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(0, -480)
    page.wait_for_function('c=>Number(document.querySelector(".ar-tools-browser").dataset.trackCycles)<c', arg=cycle0)
    seam = tool_state(page)
    enter_paused(r, page)
    limit = paused_overflow(page)
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(limit-22, 0)
    page.wait_for_timeout(220)
    near = tool_state(page)
    assert 10 <= limit-near['x'] <= 25 and near['trackMode']=='native'
    page.mouse.wheel(0, 420)
    page.wait_for_timeout(380)
    stop = tool_state(page)
    assert stop['x']==limit and stop['camera']==near['camera'] and stop['departure']=='idle'
    progress(page, .85)
    phase(page, 'departed')
    down = tool_state(page)
    progress(page, .70)
    phase(page, 'idle')
    returned = tool_state(page)
    assert returned['x']==stop['x'] and returned['trackEnabled']=='false'
    progress(page, .54)
    page.wait_for_timeout(150)
    progress(page, .25)
    phase(page, 'departed')
    up = tool_state(page)
    assert down['departureDirection']=='1' and up['departureDirection']=='-1'
    progress(page, .55)
    phase(page, 'idle')
    return {'seam':seam,'nearEnd':near,'end':stop,'down':down,'up':up,'returned':tool_state(page)}

try:
    r.case('original-edge-and-two-directions', baseline, size=DESKTOP)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
