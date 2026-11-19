"""Record the ordinary visitor route across the complete card interaction."""
from pathlib import Path
import sys

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests / 'card-refinement-step-5'))
from departure_support import DESKTOP, Run, choose, detail_button, hover_card, midpoint, phase, points, progress, tool_state
from reading_support import visible_cards


RAIL = '.ar-tool-rail'


def route(page):
    timeline = []

    def mark(name):
        clock = page.evaluate('performance.now()')
        state = tool_state(page)
        fields = ('category', 'x', 'y', 'camera', 'entrance', 'departure', 'readingId', 'trackEnabled')
        timeline.append({'action': name, 'pageTimeMs': round(clock, 1), **{key: state.get(key) for key in fields}})
        return state

    assert r.state(page)['mode'] == 'immersive'
    assert r.state(page)['host']['displayH'] == '0.0000000'
    assert not page.locator('.ar-card-region-debug').count()
    mark('courtyard')
    page.wait_for_timeout(650)
    r.go(page, 'A1')
    mark('about')
    page.wait_for_timeout(600)
    r.go(page, 'A2')
    mark('experience')
    page.wait_for_timeout(680)
    r.go(page, 'A3')
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>20')
    entry = mark('four-cards-landed-and-automatic')
    assert entry['entrancePlays'] == '1' and entry['entranceReason'] == 'completed'
    assert entry['entranceIds'].split(',') == ['midjourney', 'comfyui', 'kling', 'blender']
    assert entry['trackMode'] == 'program' and entry['trackEnabled'] == 'true'
    page.wait_for_timeout(850)
    page.locator('[data-action=auto]').click()
    choose(page, 'G6')
    paused = mark('post-production-paused')
    assert paused['trackEnabled'] == 'false' and paused['trackMode'] == 'native'
    page.screenshot(path=str(r.out / 'desktop-paused.png'))
    page.wait_for_timeout(500)

    page.evaluate('''() => {
      window.journeyWheels = [];
      window.addEventListener('wheel', e => window.journeyWheels.push({
        trusted: e.isTrusted, claimed: e.defaultPrevented, deltaY: e.deltaY, at: performance.now()
      }), { passive: true });
    }''')
    rolls = {}
    for name, point, delta, interval in [('slow', 'left', 40, 170), ('fast', 'right', 115, 35)]:
        before = mark(f'{name}-wheel-start')
        page.mouse.move(*points(page)[point])
        for _ in range(4):
            page.mouse.wheel(0, delta)
            page.wait_for_timeout(interval)
        page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackFramePending==="false"')
        after = mark(f'{name}-wheel-settled')
        assert after['x'] > before['x']+8 and float(after['trackSpeed']) == 0
        assert after['y'] == paused['y'] and after['camera'] == paused['camera']
        rolls[name] = {'displacement': after['x']-before['x'], 'x': after['x']}
        page.wait_for_timeout(480)
    assert rolls['fast']['displacement'] > rolls['slow']['displacement'], rolls

    candidate = visible_cards(page)[1]
    card_id = hover_card(page, candidate)
    card = page.locator(f'{RAIL} .ar-tool-card[data-tool-id="{card_id}"]')
    pose = card.evaluate('e=>e.dataset.readingPose.split(",").map(Number)')
    assert pose[4] > 1 and not card.locator('.ar-card-detail').is_hidden()
    front = card.locator('.ar-card-front').bounding_box()
    page.mouse.move(front['x']+front['width']*.67, front['y']+front['height']*.3, steps=9)
    page.wait_for_function('''([id,yaw]) => Math.abs(Number(document.querySelector(
      '.ar-tool-card[data-tool-id="'+id+'"]').dataset.readingPose.split(',')[6])-yaw)>.25''', arg=[card_id,pose[6]])
    preview = mark('hover-tilt-and-details')
    assert preview['detailMode'] == 'preview' and preview['readingId'] == card_id
    page.wait_for_timeout(500)
    page.mouse.click(*midpoint(detail_button(page, card_id)), delay=80)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"')
    page.mouse.move(*points(page)['outside'])
    page.wait_for_timeout(680)
    fixed = mark('fixed-details-after-pointer-left')
    assert fixed['readingId'] == card_id and fixed['detailMode'] == 'pinned'
    assert fixed['y'] == paused['y'] and fixed['camera'] == paused['camera']
    page.screenshot(path=str(r.out / 'desktop-fixed.png'))

    progress(page,.86,wait=False)
    phase(page, 'departed')
    parked = mark('visible-cards-flew-out')
    assert parked['departureDirection'] == '1' and parked['departureIds']
    page.wait_for_timeout(650)
    progress(page,.65,wait=False)
    phase(page, 'idle')
    page.wait_for_timeout(400)
    returned = mark('original-class-position-and-detail-restored')
    assert returned['departureReason'] == 'returned' and returned['entrancePlays'] == '1'
    assert returned['category'] == fixed['category'] and returned['readingId'] == card_id
    assert returned['detailMode'] == 'pinned' and returned['trackEnabled'] == 'false'
    assert abs(returned['x']-fixed['x']) <= 1, (returned['x'], fixed['x'])
    page.wait_for_timeout(700)
    page.locator('[data-action=continue]').click()
    page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.006')
    mark('continued-to-ai-film')
    page.wait_for_timeout(1000)
    wheels = page.evaluate('window.journeyWheels')
    assert all(event['trusted'] for event in wheels)
    assert len([event for event in wheels if event['claimed']]) >= 4
    assert [event['claimed'] for event in wheels[-2:]] == [False, False]
    return {'viewport': list(DESKTOP), 'timeline': timeline, 'wheels': wheels, 'rolls': rolls,
            'hoverScale':pose[4], 'restoredTool':card_id, 'entryMs':float(entry['entranceObservedDuration'])}


if __name__ == '__main__':
    r = Run()
    try:
        r.case('courtyard-cards-and-return', route, size=DESKTOP, video=True)
    finally:
        passed = r.finish()
    raise SystemExit(0 if passed else 1)
