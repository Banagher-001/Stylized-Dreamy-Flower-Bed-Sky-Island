"""A real wall-clock ten-minute session; never substitutes clocks or RAF."""
from support import Run, save, now
import time, json
r = Run()

def session(page):
    assert r.args.seconds >= 600, 'Final endurance evidence requires at least 600 real seconds'
    for station in ['A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','water','A3']:
        r.go(page, station)
    page.wait_for_timeout(1000)
    base = r.state(page)
    baseline_resources = json.loads(base['host']['rendererStats'])
    ids = [c['instance'] for c in base['cards']]
    tool_ids = [c['id'] for c in base['cards']]
    started = time.monotonic()
    rows, actions = [], []
    next_sample, next_action, action_index = 0, 60, 0
    def restore():
        r.go(page, 'A3')
        page.mouse.move(24, 300)
        if r.state(page)['tools']['trackEnabled'] != 'true':
            page.locator('[data-action=auto]').click()
        page.wait_for_timeout(500)
    def observe():
        s = r.state(page)
        assert s['host']['renderState'] == 'ready' and s['canvas'] == 1 and s['frames'] == 0
        assert len(s['cards']) == 22 and [c['instance'] for c in s['cards']] == ids
        assert [c['id'] for c in s['cards']] == tool_ids
        assert len(set(c['instance'] for c in s['cards'])) == 22
        assert page.locator('.ar-tools-browser .ar-tool-card').count() == 22
        assert s['overflow'] <= 1 and not s['dialogs']
        resources = json.loads(s['host']['rendererStats'])
        for key in ['geometries','textures','programs']:
            assert resources[key] <= baseline_resources[key] + 2, (key, resources, baseline_resources)
        row = {'elapsedSeconds': round(time.monotonic()-started,3), 'atShanghai': now(),
               'resources': resources, 'sceneTime': s['host']['sceneTime'], 'railX': s['railX'],
               'tools': s['tools'], 'frames': s['frames'], 'cards': len(s['cards']), 'canvas': s['canvas'],
               'heap': page.evaluate('performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize}:null')}
        rows.append(row)
        save(r.out/'samples.json', {'durationRequired':r.args.seconds,'samples':rows,'actions':actions})
        print(json.dumps({'elapsedSeconds':row['elapsedSeconds'],'cards':22,'resources':{k:resources[k] for k in ['geometries','textures','programs']}}), flush=True)
    while time.monotonic()-started < r.args.seconds:
        elapsed = time.monotonic()-started
        if elapsed >= next_action and next_action <= 540:
            action_index += 1
            if action_index in [3,9]:
                identifier = 'lawson' if action_index == 3 else 'bottle-ocean'
                frame = r.open_scene(page, identifier)
                if identifier == 'lawson': frame.locator('[data-cam=front]').click()
                else: frame.locator('[data-action=pause]').click()
                restore()
                action = 'embedded-open-close-'+identifier
            elif action_index == 5:
                page.set_viewport_size({'width':390,'height':844})
                page.wait_for_timeout(750)
                assert r.state(page)['mode'] == 'stable'
                page.set_viewport_size({'width':1440,'height':900})
                page.wait_for_timeout(750)
                if r.state(page)['mode'] == 'stable':
                    button = page.locator('#tour-layout-toggle')
                    if button.is_enabled(): button.click()
                restore()
                action = 'resize-and-return'
            elif action_index == 7:
                page.locator('[data-action=all]').click()
                assert page.locator('.ar-catalog .ar-tool-card').count() == 22
                page.keyboard.press('Escape')
                page.wait_for_function('!document.querySelector(".ar-overview-dialog").open')
                restore()
                # The catalog deliberately destroys its old views and rebuilds
                # the rail; require one current entity per tool, not old nodes.
                ids = [c['instance'] for c in r.state(page)['cards']]
                action = 'catalog-open-close'
            else:
                rail=page.locator('.ar-tool-rail').bounding_box()
                page.mouse.move(rail['x']+rail['width']/2,rail['y']+rail['height']/2)
                page.mouse.wheel(0,240)
                page.wait_for_timeout(300)
                page.mouse.move(24,300)
                # A wheel over a gap can deliberately hand control to the page.
                # Return by the same real wheel route before invoking A3 controls.
                r.go(page, 'A3')
                page.locator('[data-action=help]').click()
                page.keyboard.press('Escape')
                action = 'wheel-and-help'
            actions.append({'elapsedSeconds':round(time.monotonic()-started,3),'action':action})
            next_action += 60
        if elapsed >= next_sample:
            observe()
            next_sample += 30
        page.wait_for_timeout(500)
    observe()
    duration = time.monotonic()-started
    assert duration >= r.args.seconds
    assert float(rows[-1]['sceneTime']) > float(rows[0]['sceneTime']) + 60
    assert len({x['tools'].get('trackDistance') for x in rows if x['tools'].get('trackDistance') is not None}) >= 3
    final = r.checkpoint(page, 'final')
    return {'actualWallSeconds':duration,'requiredWallSeconds':r.args.seconds,'sampleCount':len(rows),'actions':actions,'baselineResources':baseline_resources,'finalResources':json.loads(final['host']['rendererStats']),'oneCardEntityPerTool':True,'clockModified':False,'RAFModified':False,'hardwareFPSClaimed':False,'samples':'samples.json'}

try:
    r.case('ten-minute-real-clock-stability', session)
finally:
    good=r.finish()
raise SystemExit(0 if good else 1)
