"""Check the visible guidance against native input on the production site."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'card-refinement-step-5'))
from departure_support import DESKTOP, Run, choose, enter_paused, points, ready_automatic, tool_state


ROOT = '.ar-tools-browser'
RAIL = '.ar-tool-rail'
HELP = '.ar-tool-help-panel'
HINT = '.ar-current-hint'
OPEN = '[data-action="help"]'
CONTINUE = '.ar-continue-slot [data-action="continue"]'
STATE = '''() => {
  const root = document.querySelector('.ar-tools-browser'), rail = root.querySelector('.ar-tool-rail');
  return {hint: root.querySelector('.ar-current-hint').textContent, input: root.dataset.toolInput,
    state: root.dataset.guidanceState, category: root.dataset.category, motion: root.dataset.trackReason,
    auto: root.dataset.trackEnabled, x: rail.scrollLeft, y: scrollY,
    camera: document.querySelector('#tour-host').dataset.targetH,
    label: document.querySelector('.ar-continue-slot .ar-hint').textContent,
    details: root.dataset.readingId, pageOverflow: document.documentElement.scrollWidth - innerWidth};
}'''


def state(page):
    return page.evaluate(STATE)


def wait_hint(page, value):
    page.wait_for_function('v=>document.querySelector(".ar-tools-browser").dataset.guidanceState===v', arg=value)
    return state(page)


def help_geometry(page):
    return page.locator(HELP).evaluate('''panel => {
      const button = panel.querySelector('.ar-tool-help-close').getBoundingClientRect();
      const root = panel.closest('.ar-tools-browser'), rail = root.querySelector('.ar-tool-rail');
      const screen = panel.getBoundingClientRect(), controls = root.querySelector('.ar-tool-controls').getBoundingClientRect();
      const sizes = [...root.querySelectorAll('.ar-tool-controls button:not([hidden]),.ar-tool-help-close')]
        .map(e=>[e.getBoundingClientRect().width,e.getBoundingClientRect().height]);
      return {mode: panel.dataset.presentation, buttons: sizes, overflow: panel.scrollWidth-panel.clientWidth,
        panel: [screen.left,screen.top,screen.right,screen.bottom], close: [button.top,button.bottom],
        controls: [controls.top,controls.bottom], rail: [rail.getBoundingClientRect().top,rail.getBoundingClientRect().bottom],
        description: rail.getAttribute('aria-describedby'), scroll: [panel.scrollHeight,panel.clientHeight],
        rows: [...panel.querySelectorAll('dd')].map(e=>e.textContent)};
    }''')


def scroll_probe(page):
    page.evaluate('''() => {
      window.wheelLog=[];
      window.addEventListener('wheel', e=>window.wheelLog.push({trusted:e.isTrusted, claimed:e.defaultPrevented, x:e.deltaX, y:e.deltaY}), {passive:true});
    }''')


def swipe(page, start, end):
    client = page.context.new_cdp_session(page)
    client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [dict(zip(('x', 'y'), start))]})
    for step in range(1, 11):
        point = [a + step * (b - a) / 10 for a, b in zip(start, end)]
        client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [dict(zip(('x', 'y'), point))]})
        page.wait_for_timeout(25)
    client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    client.detach()


def desktop_guidance(page):
    ready_automatic(r, page)
    automatic = wait_hint(page, 'automatic')
    assert automatic['hint'] == '自动展示中 · 滚轮可接管'
    page.locator(OPEN).click()
    automatic_help = help_geometry(page)
    assert '停滚后平缓接回自动展示' in automatic_help['rows'][0]
    page.locator('[data-action="help-close"]').click()
    wait_hint(page, 'automatic')
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(0, 260)
    manual = wait_hint(page, 'manual')
    assert manual['auto'] == 'true' and manual['hint'] == '卡牌区内滚轮横移'
    wait_hint(page, 'automatic')
    page.locator('[data-action="auto"]').click()
    choose(page, 'G6')
    assert wait_hint(page, 'paused')['hint'] == '已暂停 · 滚轮仍可横移'

    page.locator(OPEN).click()
    guidance = help_geometry(page)
    assert guidance['mode'] == 'popover' and len(guidance['rows']) == 4
    assert '停滚后缓慢停下' in guidance['rows'][0]
    assert guidance['rail'][0] <= guidance['panel'][1] < guidance['panel'][3] <= guidance['controls'][0]
    assert guidance['panel'][1] <= guidance['close'][0] < guidance['close'][1] <= guidance['panel'][3]
    assert guidance['description'] == page.locator(HINT).get_attribute('id')
    page.screenshot(path=str(r.out / 'desktop-help.png'))
    page.locator('[data-action="help-close"]').click()

    scroll_probe(page)
    start = wait_hint(page, 'paused')
    changes = []
    for point, dx, dy in [('left', 0, 130), ('right', 0, 130), ('face', -40, 0)]:
        previous = state(page)
        page.mouse.move(*points(page)[point])
        page.mouse.wheel(dx, dy)
        page.wait_for_function('(x)=>Math.abs(document.querySelector(".ar-tool-rail").scrollLeft-x)>=8', arg=previous['x'])
        page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackFramePending==="false"')
        after = state(page)
        assert (after['x'] - previous['x']) * (dx or dy) > 0
        assert (after['y'], after['camera']) == (start['y'], start['camera'])
        changes.append(after['x'] - previous['x'])

    page.mouse.move(*points(page)['outside'])
    assert state(page)['y'] == start['y']
    page.mouse.wheel(0, 140)
    page.wait_for_function('y=>scrollY>y', arg=start['y'])
    inputs = page.evaluate('window.wheelLog')
    assert len(inputs) == 4 and all(e['trusted'] for e in inputs) and [e['claimed'] for e in inputs] == [True, True, True, False]
    return {'automatic': automatic, 'automaticHelp': automatic_help, 'manual': manual,
            'paused': start, 'help': guidance, 'cardDisplacements': changes, 'wheel': inputs}


def all_fit(page):
    enter_paused(r, page)
    choose(page, 'G3')
    before = wait_hint(page, 'fits')
    assert before['hint'] == '本类已全部展示' and '移出' not in before['label']
    assert page.locator('[data-action="auto"]').is_hidden()
    scroll_probe(page)
    page.mouse.move(*points(page)['center'])
    page.mouse.wheel(0, 150)
    page.wait_for_function('y=>scrollY>y+10', arg=before['y'])
    after = state(page)
    assert before['x'] == after['x'] == 0
    assert page.evaluate('window.wheelLog') == [{'trusted': True, 'claimed': False, 'x': 0, 'y': 150}]
    return {'before': before, 'after': after}


def tab_to(page, selector):
    for _ in range(45):
        if page.evaluate('s=>document.activeElement.matches(s)', selector):
            assert page.evaluate('''() => document.activeElement.matches(':focus-visible') &&
                getComputedStyle(document.activeElement).outlineStyle !== 'none' ''')
            return
        page.keyboard.press('Tab')
    raise AssertionError(f'Could not Tab to {selector}')


def keyboard(page):
    ready_automatic(r, page)
    tab_to(page, RAIL + ' button[data-action="detail"]')
    focused = tool_state(page)
    assert focused['toolInput'] == 'keyboard' and focused['trackFramePending'] == 'false'
    page.keyboard.press('Enter')
    fixed = wait_hint(page, 'pinned')
    assert fixed['details'] == focused['focus'] and 'Esc' in fixed['hint']
    page.keyboard.press('Escape')
    wait_hint(page, 'keyboard')
    tab_to(page, '[data-action="next"]')
    previous = tool_state(page)['activeId']
    page.keyboard.press('Space')
    assert tool_state(page)['activeId'] != previous
    tab_to(page, OPEN)
    page.keyboard.press('Enter')
    opened = help_geometry(page)
    assert 'Enter 或空格' in opened['rows'][0]
    assert page.locator(OPEN).get_attribute('aria-expanded') == 'true'
    assert page.locator(HELP + ' h3').evaluate('e=>document.activeElement===e && e.matches(":focus-visible")')
    page.keyboard.press('Escape')
    assert page.locator(OPEN).evaluate('e=>document.activeElement===e && e.getAttribute("aria-expanded")==="false"')
    page.keyboard.press('Enter')
    tab_to(page, '[data-action="help-close"]')
    page.keyboard.press('Space')
    assert page.locator(HELP).is_hidden()
    tab_to(page, CONTINUE)
    page.keyboard.press('Enter')
    page.wait_for_function('Number(document.querySelector("#tour-host").dataset.targetH)>4.8')
    return {'focused': focused['focus'], 'fixed': fixed, 'help': opened, 'continued': state(page)}


def touch(page):
    r.go(page, 'A3')
    choose(page, 'G6')
    rail = page.locator(RAIL)
    rail.scroll_into_view_if_needed()
    initial = wait_hint(page, 'touch')
    assert initial['hint'] == '左右滑卡 · 点按详情'
    box = rail.bounding_box()
    x, y = box['x'] + box['width'] - 25, box['y'] + min(130, box['height'] / 2)
    swipe(page, (x, y), (x - min(240, box['width'] - 50), y))
    page.wait_for_function('x=>document.querySelector(".ar-tool-rail").scrollLeft>x+100', arg=initial['x'])
    page.wait_for_timeout(450)
    horizontal = state(page)
    assert horizontal['y'] == initial['y'] and horizontal['input'] == 'touch'
    before = horizontal['y']
    swipe(page, (6, 560), (6, 400))
    page.wait_for_function('y=>scrollY>y+20', arg=before)
    r.activate(page.locator(OPEN))
    help_box = help_geometry(page)
    assert help_box['mode'] == 'inline' and help_box['panel'][1] >= help_box['controls'][1]
    assert help_box['overflow'] <= 1 and all(min(button) >= 44 for button in help_box['buttons'])
    assert '左右滑动' in help_box['rows'][0]
    page.locator(HELP).scroll_into_view_if_needed()
    page.screenshot(path=str(r.out / f'phone-help-{page.viewport_size["width"]}.png'))
    r.activate(page.locator('[data-action="help-close"]'))
    button = rail.locator('button[data-action="detail"]').first
    r.activate(button)
    read = wait_hint(page, 'pinned')
    assert read['hint'] == '已展开 · 点按收起详情' and button.get_attribute('aria-expanded') == 'true'
    r.activate(button)
    assert wait_hint(page, 'touch')['details'] == ''
    return {'initial': initial, 'afterSwipe': horizontal, 'help': help_box, 'detail': read}


def hybrid(page):
    ready_automatic(r, page)
    auto = page.locator('[data-action="auto"]')
    auto.click()
    auto.click()
    wait_hint(page, 'automatic')
    assert page.evaluate('matchMedia("(hover:hover) and (pointer:fine)").matches')
    page.evaluate('''() => {window.pointerSources=[];document.addEventListener('pointerdown',e=>window.pointerSources.push([e.pointerType,e.isTrusted]));}''')
    rail = page.locator(RAIL)
    box = rail.bounding_box()
    x, y = box['x']+box['width']*.74, box['y']+box['height']*.43
    before = state(page)
    swipe(page, (x, y), (x-240, y))
    wait_hint(page, 'touch')
    page.wait_for_timeout(550)
    touch_state = tool_state(page)
    assert touch_state['trackMode'] == 'native' and touch_state['trackEnabled'] == 'true', touch_state
    assert touch_state['x'] > before['x']+100 and touch_state['y'] == before['y'], touch_state
    assert touch_state['trackFramePending'] == 'false' and auto.is_hidden()
    assert page.evaluate('window.pointerSources')[-1] == ['touch', True]
    wheel_before = state(page)
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(0, 140)
    wait_hint(page, 'manual')
    wait_hint(page, 'automatic')
    mouse_state = tool_state(page)
    assert mouse_state['category'] == touch_state['category'] and mouse_state['trackEnabled'] == 'true'
    assert mouse_state['y'] == touch_state['y'] and mouse_state['camera'] == wheel_before['camera']
    return {'touch': touch_state, 'mouse': mouse_state}


def hybrid_detail(page):
    ready_automatic(r, page)
    rail = page.locator(RAIL)

    def button_hit():
        return rail.evaluate('''e => {
          const bounds = e.getBoundingClientRect();
          for (const button of e.querySelectorAll('button[data-action="detail"]')) {
            const b = button.getBoundingClientRect(), x = b.left + b.width/2, y = b.top + b.height/2;
            if (x >= bounds.left + 300 && x < bounds.right - 20 && button.contains(document.elementFromPoint(x,y)))
              return {x,y,id:button.dataset.toolId};
          }
          return null;
        }''')

    b = button_hit()
    assert b, 'No accessible detail button in the automatic track'
    swipe(page, (b['x'], b['y']), (b['x']-230, b['y']))
    wait_hint(page, 'touch')
    after = tool_state(page)
    assert after['trackMode'] == 'native' and after['x'] > 100 and after['detailMode'] == 'summary', after
    page.mouse.move(*points(page)['left'])
    wait_hint(page, 'automatic')
    b = button_hit()
    assert b
    client = page.context.new_cdp_session(page)
    client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x':b['x'], 'y':b['y']}]})
    page.wait_for_timeout(85)
    client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    client.detach()
    selected = wait_hint(page, 'pinned')
    assert selected['details'] == b['id'] and selected['auto'] == 'true' and selected['input'] == 'touch'
    return {'swipeFromDetailButton': after, 'tapOnDetailButton': selected}


def reduced_during_entrance(page):
    r.go(page, 'A3')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceSubphase==="flying"')
    flying = tool_state(page)
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    r.go(page, 'A3')
    rail = page.locator(RAIL)
    rail.scroll_into_view_if_needed()
    start = tool_state(page)
    assert start['entranceFramePending'] == start['entranceHoldPending'] == 'false'
    assert not page.locator('.ar-flight-stage').count() and start['trackFramePending'] == 'false'
    page.mouse.move(*points(page)['center'])
    page.mouse.wheel(0, 140)
    page.wait_for_function('x=>document.querySelector(".ar-tool-rail").scrollLeft>x+100', arg=start['x'])
    after = tool_state(page)
    assert after['y'] == start['y'] and after['trackFramePending'] == 'false'
    page.locator(OPEN).click()
    guide = help_geometry(page)
    assert guide['mode'] == 'inline' and '直接横移' in guide['rows'][0] and '缓慢' not in guide['rows'][0]
    return {'duringFlight': flying, 'before': start, 'after': after, 'help': guide}


def reduced_during_wheel(page):
    enter_paused(r, page)
    detector = page.locator(ROOT)
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(0, 160)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackWheelActive==="true"')
    before = tool_state(page)
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    r.go(page, 'A3')
    page.locator(RAIL).scroll_into_view_if_needed()
    after = tool_state(page)
    assert after['trackFramePending'] == after['trackWheelActive'] == 'false' and after['category'] == before['category']
    assert after['trackEnabled'] == before['trackEnabled'] == 'false'
    assert detector.evaluate('e=>!e.querySelector("[data-edge-contact]")')
    page.wait_for_timeout(380)
    assert abs(tool_state(page)['x']-after['x']) <= 1
    return {'before': before, 'after': after}


def enlarged_text(page):
    page.add_style_tag(content=':root { font-size: 200% }')
    page.wait_for_function('document.documentElement.classList.contains("tour-large-text")')
    r.go(page, 'A3')
    page.locator(OPEN).click()
    guide = help_geometry(page)
    assert guide['mode'] == 'inline' and guide['overflow'] <= 1 and state(page)['pageOverflow'] <= 1
    page.locator('[data-action="help-close"]').scroll_into_view_if_needed()
    assert page.locator('[data-action="help-close"]').evaluate('e=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}')
    page.screenshot(path=str(r.out / 'enlarged-text-help.png'))
    page.locator('[data-action="help-close"]').click()
    assert page.locator(CONTINUE).is_visible()
    return {'geometry': guide, 'textScale': 2, 'viewport': page.viewport_size}


if __name__ == '__main__':
    r = Run()
    try:
        r.case('desktop-guidance-and-wheel', desktop_guidance, size=DESKTOP)
        r.case('all-fit-first-wheel-goes-to-page', all_fit, size=DESKTOP)
        r.case('keyboard-details-help-and-next-screen', keyboard, size=DESKTOP)
        r.case('phone-touch-and-help', touch, size=(390, 844), touch=True)
        r.case('narrow-touch-and-help', touch, size=(320, 740), touch=True)
        if r.args.engine == 'chromium':
            r.case('hybrid-native-touch-resumes-mouse', hybrid, size=DESKTOP)
            r.case('hybrid-detail-button-swipe-and-tap', hybrid_detail, size=DESKTOP)
        r.case('reduce-during-entrance', reduced_during_entrance, size=DESKTOP)
        r.case('reduce-during-wheel-tail', reduced_during_wheel, size=DESKTOP)
        r.case('enlarged-text-inline-guidance', enlarged_text, size=(1100, 850))
    finally:
        passed = r.finish()
    raise SystemExit(0 if passed else 1)
