"""Reproduce the pre-change behavior on the exact Step 2 build."""
from observe import Run, DESKTOP, enter_paused, points, snapshot

r = Run()


def baseline(page):
    enter_paused(r, page)
    outcomes = []
    for name in ('face', 'gap', 'left', 'right'):
        r.go(page, 'A3')
        x, y = points(page)[name]
        page.mouse.move(x, y)
        before = snapshot(page)
        page.mouse.wheel(0, 120)
        page.wait_for_function('y => scrollY > y+1', arg=before['y'])
        after = snapshot(page)
        assert after['x'] == before['x'] and before['mode'] == 'native' and not before['enabled'], (name, before, after)
        outcomes.append({'point': name, 'pointer': [x, y], 'input': 120, 'before': before, 'after': after})
    r.go(page, 'A3')
    page.locator('[data-action="next"]').click()
    page.wait_for_function('document.querySelector(".ar-tool-rail").scrollLeft > 20')
    x, y = points(page)['face']
    page.mouse.move(x, y)
    before = snapshot(page)
    page.mouse.wheel(0, -120)
    page.wait_for_function('y => scrollY < y-1', arg=before['y'])
    after = snapshot(page)
    assert abs(after['x'] - before['x']) < 1
    outcomes.append({'point': 'face-reverse', 'pointer': [x, y], 'input': -120, 'before': before, 'after': after})
    return {'observed': outcomes}


try:
    r.case('original-native-wheel-gap', baseline, size=DESKTOP)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
