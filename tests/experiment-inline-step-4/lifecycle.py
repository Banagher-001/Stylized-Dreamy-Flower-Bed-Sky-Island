"""Exercise the selected project and frame ownership in a real browser."""
from pathlib import Path
import sys

from playwright.sync_api import Error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'about-refresh-final'))
from support import Run


STAGE = '.experiment-window-stage'
MOUNT = '.experiment-scene-mount'
ARCHIVE = '.experiment-project-archive'
LANDING = '[data-experiment-station="C2"]'
LAWSON = 'lawson'
BOTTLE = 'bottle-ocean'
TITLES = {LAWSON: '罗森便利店', BOTTLE: '瓶中海洋'}
EXPECTED_SIZES = {(1440, 900): [1198, 559], (390, 844): [337, 473], (844, 390): [779, 380]}
r = Run()


def tab(page, project):
    return page.locator(f'[data-project-select="{project}"]')


def iframe(page, project):
    return page.locator(f'{STAGE} iframe[src$="/experiments/{project}/index.html"]')


def enters(request, project):
    return request.resource_type == 'document' and request.url == r.origin + f'experiments/{project}/index.html'


def selection(page, project):
    assert page.locator('.experiment-reading').get_attribute('data-project-id') == project
    assert page.locator(f'{LANDING} h2').inner_text() == TITLES[project]
    assert page.locator(f'{LANDING} .experiment-summary').inner_text().startswith('在一家微缩便利店' if project == LAWSON else '黄昏海岸')
    assert page.locator('#experiment-project-preview').get_attribute('aria-labelledby') == 'experiment-project-' + project
    assert page.locator(f'{STAGE} img').get_attribute('alt').startswith('蓝色 LAWSON' if project == LAWSON else '黄昏海岸')
    assert page.locator(f'{ARCHIVE} summary').get_attribute('aria-label') == f'查看{TITLES[project]}项目档案'
    assert page.locator('[role=tab][data-project-select][aria-selected=true]').count() == 1
    for identifier in TITLES:
        assert tab(page, identifier).is_enabled()
        assert tab(page, identifier).get_attribute('aria-selected') == str(identifier == project).lower()
        assert tab(page, identifier).get_attribute('tabindex') == ('0' if identifier == project else '-1')


def parent(page):
    return page.evaluate('''() => {
      const host=document.querySelector('#tour-host'), stage=document.querySelector('.experiment-window-stage');
      const {x,y,width,height}=stage.getBoundingClientRect();
      return {url:location.href, history:history.length, y:scrollY, h:host.dataset.displayH, camera:host.dataset.cameraTarget,
        bounds:[x,y,width,height], viewport:[innerWidth,innerHeight], dialogs:document.querySelectorAll('dialog[open]').length};
    }''')


def same_position(before, after):
    assert all(before[k] == after[k] for k in before if k != 'bounds'), (before, after)
    assert max(abs(a-b) for a, b in zip(before['bounds'], after['bounds'])) <= 1, (before, after)


def observe_mounts(page):
    page.locator(MOUNT).evaluate('''mount => {
      let count=mount.querySelectorAll('iframe').length;
      window.__testSceneMounts=[];
      new MutationObserver(records => {
        for (const record of records) {
          for (const item of record.removedNodes) if (item instanceof HTMLIFrameElement) {
            window.__testSceneMounts.push({action:'remove', path:new URL(item.src).pathname, count:--count});
          }
          for (const item of record.addedNodes) if (item instanceof HTMLIFrameElement) {
            window.__testSceneMounts.push({action:'attach', path:new URL(item.src).pathname, count:++count});
          }
        }
      }).observe(mount,{childList:true});
    }''')


def mounts(page):
    events = page.evaluate('window.__testSceneMounts')
    assert events and all(0 <= event['count'] <= 1 for event in events), events
    return events


def visit(page):
    r.go(page, 'C2')
    if r.state(page)['mode'] == 'stable':
        page.locator(LANDING).evaluate('''article => {
          const header=document.querySelector('.tour-header');
          scrollBy({top:article.getBoundingClientRect().top-header.getBoundingClientRect().bottom-16,behavior:'instant'});
        }''')


def stale_responses(page):
    routes = {LAWSON: [], BOTTLE: []}

    def hold(route):
        for project in routes:
            if enters(route.request, project):
                routes[project].append(route)
                return
        route.continue_()

    page.route('**/experiments/*/index.html', hold)
    observe_mounts(page)
    with page.expect_request(lambda req: enters(req, LAWSON)):
        visit(page)
    before = parent(page)
    old_lawson = iframe(page, LAWSON).element_handle().content_frame()
    selection(page, LAWSON)
    with page.expect_request(lambda req: enters(req, BOTTLE)):
        tab(page, BOTTLE).click()
    selection(page, BOTTLE)
    assert old_lawson.is_detached()
    old_bottle = iframe(page, BOTTLE).element_handle().content_frame()
    assert page.locator(f'{STAGE} [role=status]').inner_text() == '正在载入瓶中海洋…'
    with page.expect_request(lambda req: enters(req, LAWSON)):
        page.keyboard.press('ArrowLeft')
    selection(page, LAWSON)
    assert tab(page, LAWSON).evaluate('e=>document.activeElement===e') and old_bottle.is_detached()
    assert page.locator(f'{STAGE} [role=status]').inner_text() == '正在载入罗森便利店…'
    assert len(routes[LAWSON]) == 2 and len(routes[BOTTLE]) == 1
    routes[LAWSON][1].continue_()
    current = r.wait_scene(page, LAWSON)
    assert current != old_lawson
    responses = []
    for project, route in [(BOTTLE, routes[BOTTLE][0]), (LAWSON, routes[LAWSON][0])]:
        try:
            route.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Late test response</title>')
            responses.append([project, 'late response released'])
        except Error:
            responses.append([project, 'request disposed with its frame'])
    page.wait_for_timeout(700)
    assert not current.is_detached() and r.wait_scene(page, LAWSON) == current
    assert '罗森便利店已就绪' in page.locator(f'{STAGE} [role=status]').inner_text()
    same_position(before, parent(page))
    events = mounts(page)
    assert [x['path'].split('/')[-2] for x in events if x['action'] == 'attach'] == [LAWSON, BOTTLE, LAWSON]
    return {'mountEvents': events, 'lateResponses': responses, 'parent': before, 'focusedFinalTab': True}


def rapid_clicks_in_one_frame(page):
    observe_mounts(page)
    entries = []
    page.on('request', lambda req: entries.append(req.url) if any(enters(req, p) for p in TITLES) else None)
    visit(page)
    first = r.wait_scene(page, LAWSON)
    before = parent(page)
    # A single script task delivers all input before the next layout frame.
    page.locator('.experiment-project-selector').evaluate('''selector => {
      const left=selector.querySelector('[data-project-select=lawson]');
      const right=selector.querySelector('[data-project-select=bottle-ocean]');
      right.click(); left.click(); right.click();
    }''')
    r.wait_scene(page, BOTTLE)
    selection(page, BOTTLE)
    assert first.is_detached()
    assert [url.split('/')[-2] for url in entries] == [LAWSON, BOTTLE], entries
    same_position(before, parent(page))
    return {'selectionSequence': [BOTTLE, LAWSON, BOTTLE], 'entryRequests': entries, 'mountEvents': mounts(page)}


def select_and_return(page):
    observe_mounts(page)
    entries = []
    page.on('request', lambda req: entries.append(req.url) if any(enters(req, p) for p in TITLES) else None)
    visit(page)
    lawson = r.wait_scene(page, LAWSON)
    selection(page, LAWSON)
    # Desktop also verifies that switching closes an already expanded archive.
    if not r.touch:
        page.locator(f'{ARCHIVE} summary').click()
        page.locator(f'{ARCHIVE} [data-project-id=lawson]').wait_for()
    before = parent(page)
    r.activate(tab(page, BOTTLE))
    bottle = r.wait_scene(page, BOTTLE)
    selection(page, BOTTLE)
    assert lawson.is_detached()
    assert not page.locator(ARCHIVE).evaluate('e=>e.open')
    after = parent(page)
    same_position(before, after)
    native = bottle.evaluate('() => [innerWidth,innerHeight]')
    assert native == EXPECTED_SIZES[tuple(before['viewport'])]

    if not r.touch:
        slider = bottle.locator('#waveHeight')
        slider.press('End')
        assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    r.activate(tab(page, BOTTLE))
    assert r.wait_scene(page, BOTTLE) == bottle
    if not r.touch:
        assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    assert [url.split('/')[-2] for url in entries] == [LAWSON, BOTTLE], entries
    same_position(before, parent(page))

    r.go(page, 'water')
    page.locator(f'{STAGE} iframe').wait_for(state='detached')
    assert bottle.is_detached() and page.locator('.experiment-reading').get_attribute('data-project-id') == BOTTLE
    visit(page)
    returned = r.wait_scene(page, BOTTLE)
    selection(page, BOTTLE)
    assert returned != bottle and returned.evaluate('__bottleOcean.state.waveHeight') == 35
    assert [url.split('/')[-2] for url in entries] == [LAWSON, BOTTLE, BOTTLE], entries
    result = {'initial': before, 'switched': after, 'nativeDimensions': native, 'sameFrameOnRepeat': True,
              'returnedSelection': BOTTLE, 'mountEvents': mounts(page)}
    if not r.touch:
        result['waveHeight'] = {'beforeRepeat': 100, 'afterRepeat': 100, 'afterReentry': 35}
        page.reload(wait_until='domcontentloaded')
        page.wait_for_selector('main[data-layout-ready=true]')
        visit(page)
        r.wait_scene(page, LAWSON)
        selection(page, LAWSON)
        result['selectedAfterReload'] = LAWSON
    return result


def resize_within_scene(page):
    observe_mounts(page)
    visit(page)
    frame = r.wait_scene(page, LAWSON)
    tab(page, BOTTLE).press('End')
    bottle = r.wait_scene(page, BOTTLE)
    assert frame.is_detached()
    bottle.locator('#waveHeight').press('End')
    initial = parent(page)
    page.set_viewport_size({'width': 1652, 'height': 949})
    page.wait_for_function('''() => {
      const win=document.querySelector('.experiment-window-stage');
      const main=document.querySelector('main');
      const capacity=JSON.parse(main.dataset.readingCapacity).stations.find(el=>el.id==='C2');
      return main.dataset.readingMode==='immersive' && win.clientWidth===1280 && Math.round(capacity.bounds[2])===1308;
    }''')
    page.wait_for_timeout(300)
    assert r.wait_scene(page, BOTTLE) == bottle
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    resized = parent(page)
    page.locator('#tour-layout-toggle').click()
    page.wait_for_selector('main[data-reading-mode=stable]')
    page.wait_for_timeout(300)
    assert r.wait_scene(page, BOTTLE) == bottle
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    page.locator('#tour-layout-toggle').click()
    page.wait_for_selector('main[data-reading-mode=immersive]')
    page.wait_for_timeout(300)
    assert r.wait_scene(page, BOTTLE) == bottle
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    assert sum(event['action'] == 'attach' for event in mounts(page)) == 2
    return {'initial': initial, 'resized': resized, 'sameFrameAcrossModes': True, 'mountEvents': mounts(page)}


def switch_from_error(page):
    page.route('**/experiments/lawson/index.html', lambda route: route.fulfill(
        status=200, content_type='text/html', body='<!doctype html><title>Invalid test document</title>'))
    observe_mounts(page)
    visit(page)
    page.locator(f'{STAGE}[data-scene-state=error]').wait_for()
    old = iframe(page, LAWSON).element_handle().content_frame()
    selection(page, LAWSON)
    before = parent(page)
    assert page.locator(f'{STAGE} .experiment-scene-retry').is_visible()
    tab(page, BOTTLE).click()
    r.wait_scene(page, BOTTLE)
    assert old.is_detached()
    assert not page.locator(f'{STAGE} .experiment-scene-retry').is_visible()
    selection(page, BOTTLE)
    same_position(before, parent(page))
    return {'mountEvents': mounts(page), 'parent': before}


try:
    r.case('out-of-order-scene-responses', stale_responses)
    r.case('one-frame-last-selection', rapid_clicks_in_one_frame)
    r.case('desktop-selection-repeat-return', select_and_return)
    r.case('phone-selection-repeat-return', select_and_return, size=(390, 844), touch=True)
    r.case('landscape-selection-repeat-return', select_and_return, size=(844, 390), touch=True)
    r.case('resize-and-reading-mode-keeps-scene', resize_within_scene)
    r.case('switch-directly-from-error', switch_from_error)
finally:
    good = r.finish()
raise SystemExit(0 if good else 1)
