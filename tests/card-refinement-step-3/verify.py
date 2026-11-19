"""Exercise wheel ownership and motion through the built site's normal entry."""
import shutil

from observe import DESKTOP, START_TRACE, Run, choose, enter_paused, points, snapshot, wait_ready

r = Run()
for name in ('observe.py', 'verify.py'):
    shutil.copyfile(__file__.replace('verify.py', name), r.out / (name + '.txt'))


def start(page):
    page.evaluate(START_TRACE)


def end(page):
    return page.evaluate('window.wheelTrace.stop()')


def sample_at(page, point, dy, *, dx=0, wait=380):
    page.mouse.move(*point)
    before = snapshot(page)
    start(page)
    page.mouse.wheel(dx, dy)
    page.wait_for_timeout(wait)
    return before, snapshot(page), end(page)


def owned(trace, count=1):
    events = trace['events']
    assert len(events) == count and all(e['trusted'] and e['cancelable'] and e['claimed'] for e in events), events


def still_at_station(before, after, trace=None):
    assert abs(after['y'] - before['y']) <= 1 and after['target'] == before['target'], (before, after)
    if trace:
        assert all(abs(f['y'] - before['y']) <= 1 and f['target'] == before['target'] for f in trace['frames'])


def native_points(page):
    enter_paused(r, page)
    measurements = []
    for name, direction in [('face', 1), ('gap', 1), ('left', 1), ('right', 1), ('face-up', -1)]:
        point = points(page)[name.split('-')[0]]
        before, after, trace = sample_at(page, point, 120 * direction)
        owned(trace)
        still_at_station(before, after, trace)
        assert not after['enabled'] and after['mode'] == 'native' and not after['framePending'] and after['speed'] == 0, after
        assert before['ids'] == after['ids'] and len(after['ids']) == 5
        at = trace['events'][0]['at']
        first = next((f for f in trace['frames'] if (f['x'] - before['x']) * direction >= 8 and f['at'] >= at), None)
        assert first and first['at'] - at <= 150, (name, first, at, trace)
        measurements.append({'point': name, 'riseMs': first['at'] - at, 'travel': after['x'] - before['x'], 'trace': trace})
    return {'measurements': measurements}


def braking(page):
    enter_paused(r, page)
    page.locator('[data-action="next"]').click()
    page.wait_for_function('document.querySelector(".ar-tool-rail").scrollLeft > 20')
    page.mouse.move(*points(page)['right'])
    before = snapshot(page)
    start(page)
    page.mouse.wheel(0, 180)
    page.wait_for_timeout(65)
    page.mouse.wheel(0, -120)
    page.wait_for_timeout(370)
    after, trace = snapshot(page), end(page)
    owned(trace, 2)
    still_at_station(before, after, trace)
    t = trace['events'][-1]['at']
    reverse = next((f for f in trace['frames'] if f['at'] >= t and f['speed'] < -1), None)
    assert reverse and reverse['at'] - t <= 120 and after['speed'] == 0
    return {'reverseMs': reverse['at'] - t, 'reverse': trace}


def automatic(page):
    r.go(page, 'A3')
    page.wait_for_function('''() => {
      const t=document.querySelector('.ar-tools-browser').dataset;
      return t.entranceReason==='completed' && t.trackMode==='program' && Number(t.trackSpeed)>20;
    }''')
    before, after, trace = sample_at(page, points(page)['left'], -120, wait=450)
    owned(trace)
    still_at_station(before, after, trace)
    assert before['ids'] == after['ids'] and len(after['ids']) == 22
    assert after['enabled'] and after['mode'] == 'program' and abs(after['speed'] + 28) < .5
    assert before['distance'] - after['distance'] >= 8 and after['reason'] == 'automatic'
    choose(page, 'G6')
    page.wait_for_function('''() => {
      const t=document.querySelector('.ar-tools-browser').dataset;
      return t.trackEnabled==='true' && t.trackMode==='program' && Math.abs(Number(t.trackSpeed))>20;
    }''')
    filtered = snapshot(page)
    page.locator('[data-action="auto"]').click()
    choose(page, 'G6')
    paused = snapshot(page)
    assert filtered['count'] == 5 and not paused['enabled'] and paused['mode'] == 'native'
    return {'before': before, 'resumed': after, 'trace': trace, 'filtered': filtered, 'paused': paused}


def flying(page):
    r.go(page, 'A3')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceSubphase==="flying"')


def one_wheel_during_flight(page):
    flying(page)
    before, after, trace = sample_at(page, points(page)['left'], 120, wait=540)
    owned(trace)
    still_at_station(before, after, trace)
    assert set(after['ids']) == set(before['ids']) and len(after['ids']) == 22
    assert after['entranceReason'] == 'wheel' and after['x'] > 8
    assert not page.locator('.ar-flight-stage').count()
    at = trace['events'][0]['at']
    landed = next(f for f in trace['frames'] if f['entrance'] == 'cancelled')
    restored_at = float(page.locator('.ar-tools-browser').get_attribute('data-entrance-finished-at'))
    first_move = next(f for f in trace['frames'] if f['x'] >= 2)
    assert at <= restored_at <= landed['at'] and restored_at - at <= 245, trace
    assert first_move['at'] >= landed['at'] and first_move['at'] - at <= 310, trace
    assert not after['framePending'] and after['speed'] == 0
    return {'landedMs': restored_at - at, 'firstObservedLandingMs': landed['at'] - at,
            'moveMs': first_move['at'] - at, 'travel': after['x'], 'trace': trace}


def discard_on_filter(page):
    flying(page)
    choice = page.locator('button[data-category="G6"]').bounding_box()
    x, y = points(page)['left']
    page.mouse.move(x, y)
    start(page)
    page.mouse.wheel(0, 120)
    page.mouse.click(choice['x'] + choice['width']/2, choice['y'] + choice['height']/2)
    page.wait_for_timeout(440)
    after, trace = snapshot(page), end(page)
    owned(trace)
    assert after['count'] == 5 and after['category'] == 'G6' and after['x'] == 0, after
    assert after['entranceReason'] == 'category' and not after['framePending'], (after, trace)
    return {'after': after, 'trace': trace}


def boundaries(page):
    enter_paused(r, page)
    first = snapshot(page)
    before, after, left = sample_at(page, points(page)['left'], -180)
    owned(left)
    still_at_station(before, after, left)
    assert after['x'] == first['x'] == 0 and not after['framePending']
    before, after, horizontal = sample_at(page, points(page)['right'], 25, dx=1100)
    owned(horizontal)
    still_at_station(before, after, horizontal)
    assert abs(after['x'] - after['maxX']) <= 1
    at_end = snapshot(page)
    start(page)
    for _ in range(3):
        page.mouse.wheel(0, 180)
    page.wait_for_timeout(360)
    after, right = snapshot(page), end(page)
    owned(right, 3)
    still_at_station(at_end, after, right)
    assert after['x'] == at_end['x'] and not after['framePending']
    before, after, out = sample_at(page, points(page)['outside'], 120)
    assert after['y'] > before['y'] + 1 and not out['events'][0]['claimed']
    r.go(page, 'A3')
    choose(page, 'G3')
    before, after, fit = sample_at(page, points(page)['center'], 120)
    assert before['maxX'] <= 1 and after['x'] == before['x'] and after['y'] > before['y']+1
    assert not fit['events'][0]['claimed']
    return {'left': left, 'trackpadAxis': horizontal, 'right': right, 'outside': out, 'fits': fit}


def reading(page):
    enter_paused(r, page)
    card = page.locator('.ar-tool-card button').first
    card.focus()
    page.keyboard.press('Enter')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"')
    before, after, collapse = sample_at(page, points(page)['right'], 120)
    owned(collapse)
    still_at_station(before, after, collapse)
    assert after['detail'] == 'summary' and after['x'] > before['x'] + 8 and not after['enabled']
    page.locator('[data-action="help"]').click()
    help_panel = page.locator('.ar-tool-help-panel')
    box = help_panel.bounding_box()
    help_max = help_panel.evaluate('e=>e.scrollHeight-e.clientHeight')
    before, after, help_trace = sample_at(page, (box['x']+30, box['y']+110), 100)
    help_scroll = help_panel.evaluate('e=>e.scrollTop')
    assert help_panel.is_visible() and (help_max <= 1 or help_scroll > 0), (help_max, help_scroll)
    assert before['x'] == after['x'] and before['y'] == after['y'] and not help_trace['events'][0]['claimed']
    page.locator('[data-action="help-close"]').click()
    page.locator('[data-action="all"]').click()
    dialog = page.locator('.ar-overview-dialog')
    dialog.wait_for(state='visible')
    dialog_box = dialog.bounding_box()
    _, _, catalog = sample_at(page, (dialog_box['x']+120, dialog_box['y']+180), 100)
    catalog_scroll = dialog.evaluate('e=>e.scrollTop')
    assert dialog.get_attribute('open') is not None and not catalog['events'][0]['claimed'] and catalog_scroll > 0
    page.keyboard.press('Escape')
    dialog.wait_for(state='hidden')
    before, after, returned = sample_at(page, points(page)['left'], 120)
    owned(returned)
    still_at_station(before, after, returned)
    assert after['x'] > before['x'] + 8 and after['category'] == 'G6'
    return {'collapsedPin': collapse, 'help': help_trace, 'helpMaxScroll': help_max, 'helpScroll': help_scroll,
            'fullCatalog': catalog, 'catalogScroll': catalog_scroll, 'returned': returned}


def stable(page, reduced=False):
    r.stable(page)
    r.go(page, 'A3')
    wait_ready(page)
    choose(page, 'G6')
    page.locator('.ar-tool-rail').scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    before, after, trace = sample_at(page, points(page)['center'], 120)
    owned(trace)
    still_at_station(before, after, trace)
    assert after['x'] > before['x'] + 8 and after['mode'] == 'native' and not after['framePending']
    if reduced:
        assert all(not f['active'] and not f['pending'] for f in trace['frames'])
    return {'before': before, 'after': after, 'trace': trace, 'reducedMotion': reduced}


def input_variants(page):
    enter_paused(r, page)
    x, y = points(page)['center']
    page.mouse.move(x, y)
    before = snapshot(page)
    # Dispatch exceptional event variants only. Real browser wheels cover motion.
    results = page.evaluate('''([x,y]) => {
      const target = document.elementFromPoint(x,y);
      const send = extra => {
        const e = new WheelEvent('wheel',{bubbles:true,cancelable:true,clientX:x,clientY:y,deltaY:120,...extra});
        target.dispatchEvent(e);
        return e.defaultPrevented;
      };
      return [send({ctrlKey:true}),send({metaKey:true}),send({altKey:true}),send({cancelable:false}),send({deltaY:0})];
    }''', [x, y])
    after = snapshot(page)
    assert results == [False] * 5 and before['x'] == after['x'] and not after['framePending']
    line_page = []
    for mode in (1, 2):
        start(page)
        page.evaluate('''([x,y,mode]) => document.elementFromPoint(x,y).dispatchEvent(new WheelEvent('wheel',
          {bubbles:true,cancelable:true,clientX:x,clientY:y,deltaY:mode===1?6:1,deltaMode:mode}))''', [x,y,mode])
        page.wait_for_timeout(360)
        line_page.append(end(page))
    assert all(g['events'][0]['claimed'] and max(f['speed'] for f in g['frames']) > 20 for g in line_page)
    assert snapshot(page)['x'] > before['x']+12
    return {'exceptionalClaimed': results, 'linePageSimulation': line_page}


try:
    r.case('paused-native-four-points-and-reverse', native_points, size=DESKTOP, video=True)
    r.case('wheel-reverses-and-stops', braking, size=DESKTOP)
    r.case('automatic-and-category-choice', automatic, size=DESKTOP)
    r.case('one-wheel-during-flight', one_wheel_during_flight, size=DESKTOP)
    r.case('discard-flight-input-on-category', discard_on_filter, size=DESKTOP)
    r.case('finite-ends-and-page-routing', boundaries, size=DESKTOP)
    r.case('pinned-help-and-catalog', reading, size=DESKTOP)
    r.case('stable-1100px', stable, size=(1100, 850))
    r.case('reduced-motion-direct', lambda page: stable(page, reduced=True), size=(1100,850), reduced=True)
    r.case('input-units-and-browser-priority', input_variants, size=DESKTOP)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
