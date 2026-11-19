"""Check the project tabs and original experience routes on the production site."""
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'about-refresh-final'))
from support import Run


DESKTOP = (1652, 949)
SELECTOR = '.experiment-project-selector'
DIALOG = '.tour-project-dialog'
PROJECTS = ('lawson', 'bottle-ocean')
LABELS = {'lawson': '罗森便利店', 'bottle-ocean': '瓶中海洋'}
SUMMARIES = {'lawson': '观察店员与车辆', 'bottle-ocean': '三桅帆船'}


def tab(page, identifier):
    return page.locator(f'{SELECTOR} [data-project-select="{identifier}"]')


def card_layout(page):
    return page.locator(SELECTOR).evaluate('''selector => {
      const r = selector.getBoundingClientRect(), s = getComputedStyle(selector);
      const buttons = [...selector.querySelectorAll('button')].map(el => {
        const b = el.getBoundingClientRect();
        return {id:el.dataset.projectSelect, text:el.innerText, active:el.getAttribute('aria-selected'),
          index:el.tabIndex, width:b.width, height:b.height, left:b.left, right:b.right, top:b.top,
          clipped:el.scrollWidth>el.clientWidth+1 || el.scrollHeight>el.clientHeight+1};
      });
      return {buttons, left:r.left+parseFloat(s.borderLeftWidth)+parseFloat(s.paddingLeft),
        right:r.right-parseFloat(s.borderRightWidth)-parseFloat(s.paddingRight)};
    }''')


def position(page):
    return page.evaluate('''() => {
      const d = document.querySelector('#tour-host').dataset;
      return {url:location.href,y:scrollY,display:d.displayH,target:d.targetH,mode:document.querySelector('main').dataset.readingMode};
    }''')


def choice(page, identifier):
    page.wait_for_function('''id => document.querySelector('.experiment-reading').dataset.projectId === id &&
      document.querySelector('.experiment-reading').dataset.coverState === 'ready' ''', arg=identifier)
    selected = page.locator(SELECTOR + ' [aria-selected="true"]')
    assert selected.count() == 1 and selected.get_attribute('data-project-select') == identifier
    assert selected.get_attribute('tabindex') == '0'
    assert page.locator(SELECTOR + ' [aria-selected="false"]').evaluate_all('els=>els.every(e=>e.tabIndex===-1)')
    assert page.locator('#experiment-C2-title').inner_text() == LABELS[identifier]
    assert SUMMARIES[identifier] in page.locator('.experiment-summary').inner_text()
    assert page.locator('#experiment-project-preview').get_attribute('aria-labelledby') == f'experiment-project-{identifier}'
    assert page.locator('[data-project-tab="archive"]').is_enabled()
    return page.locator('.experiment-cover img').evaluate('e=>({src:e.currentSrc,alt:e.alt,width:e.naturalWidth})')


def two_columns(page):
    layout = card_layout(page)
    left, right = layout['buttons']
    assert tuple(b['id'] for b in (left, right)) == PROJECTS
    assert all(LABELS[b['id']] in b['text'] and b['height'] >= 44 and not b['clipped'] for b in (left, right)), layout
    assert abs(left['width']-right['width']) <= 1 and abs(left['top']-right['top']) <= 1, layout
    assert abs(left['left']-layout['left']) <= 1 and abs(right['right']-layout['right']) <= 1, layout
    return layout


def original_pages(page):
    records = []
    for identifier in PROJECTS:
        frame = r.open_project(page, identifier)
        path = urlsplit(frame.url).path
        assert path.endswith(f'/experiments/{identifier}/index.html'), path
        if identifier == 'lawson':
            before = frame.evaluate('__LAWSON__.state.cameraMode')
            frame.locator('[data-cam=interior]').click()
            frame.wait_for_function('__LAWSON__.state.cameraMode==="interior"')
            control = {'camera': [before, frame.evaluate('__LAWSON__.state.cameraMode')]}
            assert control['camera'][0] != control['camera'][1]
            controls = frame.locator('button,input,.toggle').count()
        else:
            before = frame.evaluate('__bottleOcean.state.waveHeight')
            frame.locator('#waveHeight').press('End')
            control = {'waveHeight': [before, frame.evaluate('__bottleOcean.state.waveHeight')]}
            assert control['waveHeight'] == [35, 100], control
            controls = frame.locator('button,input').count()
        page.locator('#project-tab-archive').click()
        archive = page.locator('#tour-project-archive')
        archive.wait_for(state='visible')
        heading = archive.locator('h3').first.inner_text()
        assert ('一间店' if identifier == 'lawson' else '让一片海') in heading, heading
        assert page.locator(DIALOG).get_attribute('data-project-id') == identifier
        r.close_project(page)
        choice(page, identifier)
        records.append({'id':identifier, 'entry':path, 'archive':heading, 'controls':controls, **control})
    return records


def water_entrance(page):
    r.go(page, 'water')
    state = position(page)
    assert abs(float(state['display'])-11.5) < .007 and page.locator('#tour-host canvas').is_visible()
    r.open_project(page, 'courtyard')
    assert page.locator(DIALOG).get_attribute('data-tab') == 'live'
    assert page.locator('#tour-host canvas').is_visible()
    for mode in ('native', 'pixel'):
        page.locator(f'{DIALOG} [data-project-mode="{mode}"]').click()
        page.wait_for_function('mode=>document.querySelector("#tour-host canvas").dataset.renderMode===mode', arg=mode)
    r.close_project(page)
    assert page.locator('[data-flow-live]').is_visible()
    return {'waterView':state, 'liveOpened':True, 'returnedFocus':r.state(page)['focus']}


def baseline(page):
    r.go(page, 'C2')
    choice(page, 'lawson')
    layout = card_layout(page)
    assert [b['id'] for b in layout['buttons']] == ['lawson','bottle-ocean','courtyard']
    page.screenshot(path=str(r.out/'desktop-before.png'))
    return {'layout':layout, 'works':original_pages(page), 'water':water_entrance(page)}


def desktop(page):
    r.go(page, 'C2')
    first = choice(page, 'lawson')
    layout = two_columns(page)
    before = position(page)
    assert before['mode'] == 'immersive'
    page.screenshot(path=str(r.out/'desktop-two-tabs.png'))
    tab(page, 'bottle-ocean').click()
    second = choice(page, 'bottle-ocean')
    assert first['src'] != second['src'] and first['width'] > 0 and second['width'] > 0
    tab(page, 'lawson').click()
    assert choice(page, 'lawson') == first
    assert position(page) == before and page.locator('dialog[open]').count() == 0

    page.keyboard.press('Shift+Tab')
    page.keyboard.press('Tab')
    assert tab(page, 'lawson').evaluate('e=>e===document.activeElement&&e.matches(":focus-visible")')
    for key, identifier in [('ArrowRight','bottle-ocean'), ('ArrowRight','lawson'), ('ArrowLeft','bottle-ocean'),
                            ('Home','lawson'), ('End','bottle-ocean'), ('ArrowLeft','lawson')]:
        page.keyboard.press(key)
        choice(page, identifier)
        assert tab(page, identifier).evaluate('e=>e===document.activeElement&&e.matches(":focus-visible")')
    assert position(page) == before
    return {'layout':layout, 'station':before, 'covers':[first,second], 'works':original_pages(page), 'water':water_entrance(page)}


def mobile(page):
    r.go(page, 'C2')
    choice(page, 'lawson')
    first = two_columns(page)
    page.evaluate('''() => {
      window.experimentCapacityChecks = 0;
      new MutationObserver(() => window.experimentCapacityChecks++).observe(document.querySelector('main'),
        {attributes:true,attributeFilter:['data-reading-capacity']});
    }''')
    tab(page, 'bottle-ocean').tap()
    choice(page, 'bottle-ocean')
    page.wait_for_function('window.experimentCapacityChecks>0')
    assert page.locator('.experiment-image-state').is_hidden(), 'Layout measurement covered the loaded project image'
    second = two_columns(page)
    page.locator('#experiment-C2-title').scroll_into_view_if_needed()
    page.screenshot(path=str(r.out/'phone-two-tabs.png'))
    tab(page, 'lawson').tap()
    choice(page, 'lawson')
    assert r.state(page)['overflow'] <= 1
    return {'default':first,'bottle':second,'coverVisibleAfterLayoutMeasurement':True}


if __name__ == '__main__':
    r = Run()
    try:
        if r.args.only and 'baseline-three-projects' in r.args.only:
            r.case('baseline-three-projects', baseline, size=DESKTOP)
        r.case('desktop-two-projects-and-water', desktop, size=DESKTOP)
        r.case('touch-two-equal-tabs', mobile, size=(390, 844), touch=True)
    finally:
        passed = r.finish()
    raise SystemExit(0 if passed else 1)
