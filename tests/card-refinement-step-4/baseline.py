"""Capture how Step 3 couples a live mouse click to the automatic preference."""
from reading_support import DESKTOP, Run, detail_button, hover_card, midpoint, ready_automatic, tool_state

r = Run()


def baseline(page):
    ready_automatic(r, page)
    running = tool_state(page)
    card = hover_card(page, phase='either')
    held = tool_state(page)
    target = detail_button(page, card)
    x, y = midpoint(target)
    page.mouse.move(x, y)
    page.mouse.down()
    down = tool_state(page)
    page.mouse.up()
    page.wait_for_timeout(450)
    after = tool_state(page)
    assert running['trackEnabled'] == held['trackEnabled'] == 'true'
    assert down['trackEnabled'] == 'false' and after['trackEnabled'] == 'false'
    return {'card': card, 'before': running, 'hover': held, 'mouseDown': down, 'afterClick': after}


try:
    r.case('original-preview-press-disables-automatic', baseline, size=DESKTOP)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
