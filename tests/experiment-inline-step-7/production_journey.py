"""One headed journey through both original scenes in the downloaded site."""
from contextlib import suppress
import hashlib
from pathlib import Path
import sys

from PIL import Image
from playwright.sync_api import Error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiment-inline-step-6'))
from pair_support import BOTTLE, BrowserRun, CHILD, DESKTOP, IFRAME, LAWSON, STAGE, position, ready_main, wait_child, wait_original
from lawson_native import fullscreen
from support import STOPS


TITLES = {LAWSON: '罗森便利店', BOTTLE: '瓶中海洋'}


def scroll_to_station(page, station, mode):
    if mode == 'immersive':
        delta = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY', STOPS[station])
    else:
        delta = page.locator(f'[data-flow-anchor={station}]').evaluate('''e=>e.getBoundingClientRect().top-
          document.querySelector('.tour-header').getBoundingClientRect().bottom-16''')
    page.mouse.move(10, 300)
    if abs(delta) > 1:
        page.mouse.wheel(0, delta)
    if mode == 'immersive':
        page.wait_for_function('''h=>{
          const host=document.querySelector('#tour-host');
          return Math.abs(Number(host.dataset.displayH)-h)<.006 && host.dataset.cameraState==='settled';
        }''', arg=STOPS[station], timeout=45000, polling=100)


def scene_at(page, project):
    frame = wait_child(page, project)
    wait_original(frame, project)
    assert page.locator('[data-experiment-station=C2] h2').inner_text() == TITLES[project]
    assert page.locator(f'[data-project-select={project}]').get_attribute('aria-selected') == 'true'
    assert frame.url == runner.origin + f'experiments/{project}/index.html'
    response = page.request.get(frame.url)
    assert response.ok and hashlib.sha256(response.body()).hexdigest() == runner.hashes[f'experiments/{project}/index.html']
    return frame


def select(page, project):
    page.locator(f'[data-project-select={project}]').click()
    return scene_at(page, project)


def lawson_controls(page, frame):
    for _ in range(3):
        if frame.evaluate('__LAWSON__.state.quality') == 'low':
            break
        frame.locator('#btn-settings').click()
    assert frame.evaluate('__LAWSON__.state.quality') == 'low'
    times = []
    for preset, hour in (('day', 9), ('night', 22)):
        frame.locator(f'[data-preset={preset}]').click()
        frame.wait_for_function('h=>Math.abs(__LAWSON__.api.getStats().timeOfDay-h)<.025', arg=hour, timeout=90000, polling=100)
        times.append(frame.evaluate('__LAWSON__.api.getStats().timeOfDay'))
    lights = '__LAWSON__.api.getState().lights.LawsonSign'
    before = frame.evaluate(lights)
    frame.locator('.toggle[data-group=LawsonSign]').click()
    assert frame.evaluate(lights) is not before
    frame.locator('.toggle[data-group=LawsonSign]').click()
    assert frame.evaluate(lights) is before
    box = page.locator(IFRAME).bounding_box()
    point = frame.evaluate('''() => {
      for(const x of [.3,.4,.25]) for(const y of [.55,.60,.5]){
        const p=[innerWidth*x,innerHeight*y];if(document.elementFromPoint(...p)?.id==='viewport')return p;
      }return null;
    }''')
    assert box and point, 'A visible part of the original canvas must receive the drag.'
    x, y = box['x']+point[0], box['y']+point[1]
    assert page.evaluate('([x,y])=>document.elementFromPoint(x,y)?.matches(".experiment-window-stage iframe")',[x,y])
    projection = frame.evaluate('__LAWSON__.api.project([3,1,2])')
    page.mouse.move(x,y)
    page.mouse.down()
    page.mouse.move(x+85,y+34,steps=11)
    page.mouse.up()
    frame.wait_for_function('p=>JSON.stringify(__LAWSON__.api.project([3,1,2]))!==JSON.stringify(p)',arg=projection,polling=100)
    changed = frame.evaluate('__LAWSON__.api.project([3,1,2])')
    full = fullscreen(page,frame,True,runner.environment['DISPLAY'],exit_methods=('Escape',))
    frame.locator('#btn-help').click()
    assert frame.locator('#help').is_visible()
    frame.locator('#help-close').click()
    assert frame.locator('#help').is_hidden()
    page.screenshot(path=str(runner.out/'lawson-in-portfolio.png'),timeout=50000)
    return {'times':times,'signOffAndOn':True,'dragProjection':[projection,changed],'fullscreen':full,'helpAfterExit':True}


def bottle_controls(page, frame):
    frame.locator('[data-quality=retro]').click()
    assert frame.evaluate('__bottleOcean.state.quality') == 'retro'
    frame.locator('#waveHeight').press('End')
    assert frame.evaluate('__bottleOcean.state.waveHeight') == 100
    positions = []
    for preset, fov in (('side',39),('cinema',42)):
        frame.locator(f'[data-preset={preset}]').click()
        frame.wait_for_function('fov=>Math.abs(__bottleOcean.cameraRig.getState().fov-fov)<.01',arg=fov,timeout=60000,polling=100)
        state = frame.evaluate('__bottleOcean.cameraRig.getState()')
        assert state['preset'] == preset
        positions.append(state['position'])
    assert positions[0] != positions[1]
    pause = frame.locator('#pause-button')
    pause.click()
    assert frame.evaluate('__bottleOcean.state.paused')
    stopped = frame.evaluate('__bottleOcean.getDiagnostics().simTime')
    page.wait_for_timeout(450)
    assert frame.evaluate('__bottleOcean.getDiagnostics().simTime') == stopped
    pause.click()
    frame.wait_for_function('t=>!__bottleOcean.state.paused && __bottleOcean.getDiagnostics().simTime>t',arg=stopped,polling=100)
    with page.expect_download(timeout=60000) as event:
        frame.locator('[data-action=screenshot]').click()
    download = event.value
    path = runner.out/'bottle-original.png'
    download.save_as(path)
    assert not download.failure()
    dimensions = frame.evaluate('''() => {
      const canvas=document.querySelector('#gl'), ratio=Math.min(devicePixelRatio,2);
      return [Math.round(canvas.clientWidth*ratio),Math.round(canvas.clientHeight*ratio)];
    }''')
    with Image.open(path) as png:
        assert png.format == 'PNG' and list(png.size) == dimensions
        assert all(low < high for low,high in png.convert('RGB').getextrema())
    page.screenshot(path=str(runner.out/'bottle-in-portfolio.png'),timeout=50000)
    return {'waveHeight':100,'cameraPositions':positions,'pauseSimTime':stopped,'resumed':True,
            'download':{'name':download.suggested_filename,'PNG':dimensions,'bytes':path.stat().st_size,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}


def production_journey():
    context,page,events = runner.context(DESKTOP)
    try:
        ready_main(page,runner.origin)
        menu = page.locator('main')
        toggle = page.locator('#tour-layout-toggle')
        if menu.get_attribute('data-reading-mode') == 'stable' and toggle.is_enabled():
            toggle.click()
            page.wait_for_function('document.querySelector("main").dataset.readingMode==="immersive"',polling=100)
        mode = menu.get_attribute('data-reading-mode')
        assert not page.locator(IFRAME).count()
        scroll_to_station(page,'C2',mode)
        lawson = scene_at(page,LAWSON)
        assert page.locator('[data-project-select]').evaluate_all('rows=>rows.map(e=>e.dataset.projectSelect)') == list(TITLES)
        box = page.locator(STAGE).bounding_box()
        size = lawson.evaluate('() => [innerWidth,innerHeight]')
        assert box and abs(box['width']-size[0])<=1 and abs(box['height']-size[1])<=1
        if mode == 'immersive':
            assert size == list(CHILD[DESKTOP]), size
        parent = position(page)
        history = page.evaluate('history.length')
        lawson_result = lawson_controls(page,lawson)
        assert position(page) == parent
        print('Lawson original controls and OS Escape verified',flush=True)
        bottle = select(page,BOTTLE)
        assert lawson.is_detached() and bottle.evaluate('() => [innerWidth,innerHeight]') == size
        assert position(page) == parent
        bottle_result = bottle_controls(page,bottle)
        assert position(page) == parent
        lawson = select(page,LAWSON)
        assert bottle.is_detached() and position(page) == parent and page.evaluate('history.length') == history
        print('Bottle native PNG and return to Lawson verified',flush=True)
        scroll_to_station(page,'water',mode)
        page.locator(IFRAME).wait_for(state='detached',timeout=30000)
        assert lawson.is_detached()
        scroll_to_station(page,'C2',mode)
        returned = scene_at(page,LAWSON)
        assert returned != lawson and page.evaluate('history.length') == history
        assert len(context.pages) == 1 and position(page)['dialogs'] == 0
        assert not (events['external'] or events['errors'] or events['unexpectedHttp']), events
        assert all(error=='net::ERR_ABORTED' for error,_ in events['failures']), events
        return {'mode':mode,'sceneViewport':size,'normalEntry':runner.origin,'productionPackage':True,
                'lawson':lawson_result,'bottle':bottle_result,'stationPosition':parent,
                'historyLength':history,'detachedAtWater':True,'returnedCurrentSelection':LAWSON,'network':events}
    except Exception:
        with suppress(Error):
            page.screenshot(path=str(runner.out/'failure.png'),timeout=15000)
        raise
    finally:
        context.close()


runner = BrowserRun(headed=True)
try:
    runner.record('independent-production-desktop-journey',production_journey)
finally:
    passed = runner.finish()
raise SystemExit(0 if passed else 1)
