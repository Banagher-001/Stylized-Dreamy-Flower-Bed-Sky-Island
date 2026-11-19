"""Real mouse and keyboard regressions for card reading, hold and playback."""
from pathlib import Path
import shutil

from reading_support import (
    DESKTOP, Run, choose, detail_button, enter_paused, hover_card, midpoint, points,
    ready_automatic, tool_state, visible_cards,
)

r = Run()
for name in ('verify.py', 'reading_support.py'):
    shutil.copyfile(Path(__file__).with_name(name), r.out / (name + '.txt'))


def wait_tool(page, key, value, timeout=5000):
    page.wait_for_function('''([key,value]) => document.querySelector('.ar-tools-browser').dataset[key] === value''',
                           arg=[key, value], timeout=timeout)


def displacement(s):
    return float(s.get('trackDistance', 0)) if s['trackMode'] == 'program' else s['x']


def held_at(page, baseline, ms):
    page.wait_for_timeout(ms)
    current = tool_state(page)
    assert abs(displacement(current)-displacement(baseline)) <= 1, (baseline, current)
    assert float(current.get('trackSpeed', 0)) == 0 and current['trackFramePending'] == 'false', current
    return current


def pressing(page):
    page.evaluate('''() => {
      window.pressTrace = [];
      for (const type of ['pointerdown','pointerup','click']) window.addEventListener(type, e => {
        const button = e.target.closest?.('button[data-action=detail]');
        if (!button) return;
        const t = document.querySelector('.ar-tools-browser').dataset;
        const b = button.getBoundingClientRect();
        window.pressTrace.push({ type, trusted:e.isTrusted, card:button.dataset.toolId,
          shape:[b.left,b.top,b.width,b.height], hover:t.hoverState, detail:t.detailMode, at:performance.now(),
          instance:button.closest('.ar-tool-card').dataset.cardInstance });
      }, {capture:true,passive:true});
    }''')


def mouse_pin(page, card):
    button = detail_button(page, card)
    page.mouse.click(*midpoint(button), delay=80)
    wait_tool(page, 'detailMode', 'pinned')
    assert tool_state(page)['readingId'] == card


def begin_frames(page):
    page.evaluate('''() => {
      window.readingTrace?.stop();
      const root = document.querySelector('.ar-tools-browser'), rail = root.querySelector('.ar-tool-rail');
      const rows = [];
      let wheel = null;
      let frame;
      const received = e => { wheel = {at:performance.now(), trusted:e.isTrusted, claimed:e.defaultPrevented}; };
      window.addEventListener('wheel',received,{passive:true});
      function sample() {
        const t = root.dataset;
        rows.push({at:performance.now(), distance:Number(t.trackDistance||0),x:rail.scrollLeft,
          speed:Number(t.trackSpeed||0), enabled:t.trackEnabled, held:t.trackHeld==='true',
          pending:t.trackWheelActive==='true', detail:t.detailMode, id:t.readingId,
          reading:root.querySelectorAll('[data-reading="true"]').length, state:t.hoverState,
          y:scrollY, camera:document.querySelector('#tour-host').dataset.targetH, wheel});
        if (rows.length < 220) frame = requestAnimationFrame(sample);
      }
      window.readingTrace = {stop(){cancelAnimationFrame(frame);window.removeEventListener('wheel',received);return rows;}};
      sample();
    }''')


def end_frames(page):
    return page.evaluate('window.readingTrace.stop()')


def wheel_response(frames, before):
    first = next((f for f in frames if f['wheel'] and f['distance'] > displacement(before) + 8), None)
    assert first and first['wheel']['claimed'] and first['wheel']['trusted'], frames
    delta = first['at'] - first['wheel']['at']
    assert 0 <= delta <= 150, (delta, frames)
    return delta


def hover_release(page):
    ready_automatic(r, page)
    hover_card(page)
    preview = tool_state(page)
    assert preview['trackEnabled'] == 'true' and preview['trackHeld'] == 'true'
    held_at(page, preview, 300)
    begin_frames(page)
    page.mouse.move(24, 300)
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed) > 26', timeout=5000)
    trace = end_frames(page)
    first_free = next(f for f in trace if not f['held'])
    assert first_free['at'] > trace[0]['at'] and abs(first_free['distance'] - displacement(preview)) <= 1
    assert all(abs(f['distance'] - displacement(preview)) <= 1 for f in trace if f['held'])
    first_motion = next(f for f in trace if f['distance'] > displacement(preview) + .5)
    assert 140 <= first_motion['at'] - first_free['at'] <= 580, trace

    page.locator('[data-action="auto"]').click()
    card = hover_card(page)
    paused_preview = tool_state(page)
    assert paused_preview['trackEnabled'] == 'false' and paused_preview['readingId'] == card
    page.mouse.move(24, 300)
    wait_tool(page, 'trackHeld', 'false')
    paused = held_at(page, paused_preview, 640)
    assert paused['trackEnabled'] == 'false' and paused['detailMode'] == 'summary'
    return {'preview': preview, 'resumedTrace': trace, 'paused': paused,
            'firstMotionAfterReleaseMs': first_motion['at'] - first_free['at']}


def true_click_and_wheel(page):
    ready_automatic(r, page)
    pressing(page)
    # Move to the newly opening card, then press its still-moving detail button.
    selected = hover_card(page, phase='either')
    mouse_pin(page, selected)
    native = page.evaluate('window.pressTrace')
    assert [e['type'] for e in native] == ['pointerdown', 'pointerup', 'click'], native
    assert native[0]['hover'] == 'entering', native
    assert all(e['card'] == selected and e['trusted'] and e['instance'] == native[0]['instance'] for e in native), native
    error = max(abs(v-w) for e in native[1:] for v,w in zip(e['shape'], native[0]['shape']))
    assert error <= 1, native
    page.mouse.move(24, 300)
    wait_tool(page, 'hoverState', 'reading')
    pinned = tool_state(page)
    assert pinned['detailMode'] == 'pinned' and pinned['trackEnabled'] == 'true' and pinned['focus'] == selected
    held_at(page, pinned, 320)

    # Use the actual visible fixed card as the place the wheel gesture starts.
    p = next(c['point'] for c in visible_cards(page) if c['id'] == selected)
    page.mouse.move(*p)
    before = tool_state(page)
    begin_frames(page)
    page.mouse.wheel(0, 120)
    wait_tool(page, 'detailMode', 'summary')
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed) > 25')
    page.wait_for_timeout(1120)
    frames = end_frames(page)
    after = tool_state(page)
    assert after['detailMode'] == 'summary' and after['trackEnabled'] == 'true' and abs(float(after['trackSpeed']) - 28) < 1
    assert all(f['detail'] != 'preview' and f['y'] == before['y'] and f['camera'] == before['camera'] for f in frames)
    assert any(f['pending'] and f['distance'] > displacement(before) + 8 for f in frames), frames
    return {'pressEvents': native, 'pressGeometryError': error, 'pinned': pinned, 'after': after,
            'wheelResponseMs': wheel_response(frames, before), 'wheelFrames': frames}


def wheel_from_preview(page):
    ready_automatic(r, page)
    hover_card(page)
    before = tool_state(page)
    begin_frames(page)
    page.mouse.wheel(0, 120)
    wait_tool(page, 'detailMode', 'summary')
    page.wait_for_timeout(420)
    rows = end_frames(page)
    assert before['detailMode'] == 'preview' and before['trackHeld'] == 'true'
    assert all(f['y'] == before['y'] and f['camera'] == before['camera'] and f['enabled'] == 'true' for f in rows)
    assert any(f['wheel'] and f['detail'] == 'summary' and f['pending'] for f in rows)
    return {'wheelResponseMs': wheel_response(rows, before), 'frames': rows}


def pause_step_and_continue(page):
    ready_automatic(r, page)
    group = visible_cards(page)
    card = hover_card(page, group[0])
    mouse_pin(page, card)
    page.locator('[data-action="auto"]').click()
    paused = tool_state(page)
    assert paused['trackEnabled'] == 'false' and paused['detailMode'] == 'pinned' and paused['readingId'] == card
    page.locator('[data-action="next"]').click()
    stepped = tool_state(page)
    assert stepped['trackEnabled'] == 'false' and stepped['detailMode'] == 'pinned' and stepped['readingId'] == group[1]['id'], stepped
    page.locator('[data-action="previous"]').click()
    wait_tool(page, 'readingId', card)
    page.locator('[data-action="auto"]').click()
    wait_tool(page, 'trackEnabled', 'true')
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>26')
    resumed = tool_state(page)
    assert resumed['detailMode'] == 'summary' and resumed['trackHeld'] == 'false'
    return {'paused': paused, 'fixedStep': stepped, 'resumed': resumed}


def handoff_between_cards(page):
    ready_automatic(r, page)
    choices = visible_cards(page)
    a = hover_card(page, choices[0])
    b = next(c for c in reversed(visible_cards(page)) if c['id'] != a)
    before = tool_state(page)
    begin_frames(page)
    hover_card(page, b)
    frames = end_frames(page)
    after = tool_state(page)
    assert len(frames) > 2 and all(f['held'] and f['reading'] <= 1 and abs(f['distance'] - displacement(before)) <= 1 for f in frames), frames
    assert after['reading'] == [b['id']] and after['trackEnabled'] == 'true'
    return {'from': a, 'to': b['id'], 'frames': frames}


def rearm_after_wheel(page):
    enter_paused(r, page)
    p = visible_cards(page)[1]['point']
    page.mouse.move(*p)
    begin_frames(page)
    page.mouse.wheel(0, 240)
    page.wait_for_timeout(1150)
    frames = end_frames(page)
    pre_move = tool_state(page)
    assert pre_move['x'] > 10 and pre_move['trackEnabled'] == 'false' and pre_move['detailMode'] == 'summary'
    tail = max(f['at'] for f in frames if f['pending'])
    assert frames[-1]['at'] - tail >= 700 and all(f['detail'] == 'summary' for f in frames), frames
    hover_card(page)
    post_move = tool_state(page)
    assert post_move['trackEnabled'] == 'false' and post_move['reading'] == [post_move['readingId']]
    return {'frames': frames, 'stationary': pre_move, 'freshHover': post_move}


def overlays_and_filter(page):
    ready_automatic(r, page)
    card = hover_card(page)
    mouse_pin(page, card)
    page.locator('[data-action="help"]').click()
    assert tool_state(page)['helpOpen'] == 'true'
    page.locator('[data-action="help-close"]').click()
    still_fixed = tool_state(page)
    assert still_fixed['readingId'] == card and still_fixed['detailMode'] == 'pinned' and still_fixed['trackEnabled'] == 'true'
    held_at(page, still_fixed, 550)

    slot = page.locator(f'.ar-tool-slot[data-card-id="{card}"]')
    before_x = slot.bounding_box()['x']
    page.locator('[data-action="all"]').click()
    dialog = page.locator('.ar-overview-dialog')
    dialog.wait_for(state='visible')
    page.keyboard.press('Escape')
    dialog.wait_for(state='hidden')
    wait_tool(page, 'detailMode', 'pinned')
    page.wait_for_timeout(400)
    restored = tool_state(page)
    assert restored['readingId'] == card and restored['trackEnabled'] == 'true' and restored['trackFramePending'] == 'false'
    assert abs(slot.bounding_box()['x'] - before_x) <= 2, (before_x, slot.bounding_box(), restored)
    choose(page, 'G6')
    wait_tool(page, 'trackEnabled', 'true')
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>26')
    filtered = tool_state(page)
    assert filtered['detailMode'] == 'summary' and filtered['cardCount'] == '5' and not filtered.get('detailPressed')
    return {'heldThroughHelp': still_fixed, 'restored': restored, 'filtered': filtered}


def real_keyboard(page):
    ready_automatic(r, page)
    # Focus the rail as the setup for sequential, trusted Tab navigation.
    page.locator('.ar-tool-rail').focus()
    page.keyboard.press('Tab')
    card = tool_state(page)['focus']
    assert card
    page.keyboard.press('Enter')
    wait_tool(page, 'detailMode', 'pinned')
    fixed = tool_state(page)
    assert fixed['focus'] == fixed['readingId'] == card and fixed['trackEnabled'] == 'true'
    page.keyboard.press('Escape')
    wait_tool(page, 'detailMode', 'summary')
    closed = held_at(page, fixed, 660)
    assert closed['focus'] == card and closed['trackEnabled'] == 'true'
    visited = [card]
    for _ in range(int(closed['cardCount']) + 2):
        if not page.evaluate("!!document.activeElement?.closest('.ar-tool-rail')"):
            break
        page.keyboard.press('Tab')
        visited.append(tool_state(page)['focus'])
    assert not page.evaluate("!!document.activeElement?.closest('.ar-tool-rail')")
    assert len(set([c for c in visited if c])) > 1
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>25', timeout=6000)
    return {'fixed': fixed, 'closed': closed, 'visitedCards': visited, 'resumed': tool_state(page)}


def edge_and_cancelled_press(page):
    ready_automatic(r, page)
    flat = visible_cards(page)[0]
    card = hover_card(page, flat)
    button = detail_button(page, card)
    page.mouse.move(*midpoint(button))
    page.mouse.down()
    wait_tool(page, 'detailPressed', card)
    frozen = tool_state(page)
    held_at(page, frozen, 220)
    page.mouse.move(24, 300)
    page.mouse.up()
    page.wait_for_function('!document.querySelector(".ar-tools-browser").dataset.detailPressed')
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>25')
    cancelled = tool_state(page)
    assert cancelled['detailMode'] == 'summary' and cancelled['trackEnabled'] == 'true'

    # The same run exercises the first native click near the leading edge.
    left = hover_card(page, visible_cards(page)[0])
    pressing(page)
    mouse_pin(page, left)
    trace = page.evaluate('window.pressTrace')
    assert [e['type'] for e in trace] == ['pointerdown', 'pointerup', 'click'] and all(e['card'] == left for e in trace)
    error = max(abs(v-w) for e in trace[1:] for v,w in zip(e['shape'], trace[0]['shape']))
    assert error <= 1
    return {'cancelled': cancelled, 'edgeCard': left, 'firstClickGeometryError': error, 'trace': trace}


try:
    r.case('hover-hold-and-resume-by-choice', hover_release, size=DESKTOP)
    r.case('first-native-click-and-wheel', true_click_and_wheel, size=DESKTOP, video=True)
    r.case('wheel-directly-from-preview', wheel_from_preview, size=DESKTOP)
    r.case('pause-and-step-while-pinned', pause_step_and_continue, size=DESKTOP)
    r.case('single-preview-switch', handoff_between_cards, size=DESKTOP)
    r.case('wheel-tail-and-fresh-hover', rearm_after_wheel, size=DESKTOP)
    r.case('overlay-and-category-restore', overlays_and_filter, size=DESKTOP)
    r.case('keyboard-focus-and-release', real_keyboard, size=DESKTOP)
    r.case('edge-click-and-abandoned-press', edge_and_cancelled_press, size=DESKTOP)
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
