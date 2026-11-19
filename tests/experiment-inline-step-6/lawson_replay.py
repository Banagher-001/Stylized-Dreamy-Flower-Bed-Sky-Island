"""Replay Lawson's actual scene and pointer effect checks in the work window."""
import runpy
import sys
import traceback

from pair_support import BrowserRun, IFRAME, LAWSON, TESTS, literal, position, save


OLD = TESTS / 'lawson-fullpage-step-7'
sys.path.insert(0, str(OLD))
import common as previous


class InlineMouse(previous.Mouse):
    def point(self, x, y):
        if self.target.frame == self.target.owner:
            return x, y
        frame = self.target.owner.locator(IFRAME).bounding_box()
        return x + frame['x'], y + frame['y']


class Replay:
    low = previous.Run.low
    state = previous.Run.state
    observed = previous.Run.observed

    def __init__(self, runner, page, scene, side, label):
        self.owner = page
        self.page = previous.Target(page)
        self.page.frame = scene
        self.page.mouse = InlineMouse(self.page)
        self.side = side
        self.label = label
        self.folder = runner.out / (label + '-' + side)
        self.folder.mkdir()
        self.report = {'checks': []}

    def load(self):
        return {'observationsInstalled': self.page.evaluate(previous.INSTALL), 'default': self.state()}

    def picture(self, name):
        if name in ('time-day', 'time-night', 'camera-hero', 'target-door', 'target-clerkA', 'inventory', 'help-original'):
            self.owner.screenshot(path=str(self.folder / (name + '.png')), timeout=60000)

    def save(self):
        save(self.folder / 'details.json', self.report)

    def case(self, identifier, description, action):
        try:
            result = action()
            status = result.pop('_status', '通过')
            record = {'id': identifier, 'description': description, 'status': status, 'effect': result}
        except Exception:
            self.report['checks'].append({'id': identifier, 'status': '需复核', 'error': traceback.format_exc()})
            self.save()
            raise
        self.report['checks'].append(record)
        self.save()
        print(self.label, self.side, identifier, status, flush=True)

    def finish(self):
        self.save()


def observed_time(scene, time):
    scene.wait_for_function('t=>Math.abs(__LAWSON__.api.getStats().timeOfDay-t)<.02', arg=time, timeout=60000, polling=100)


def interface(replay):
    scene = replay.page
    replay.load()

    def inventory():
        controls = scene.locator('button,input,.toggle').evaluate_all('''elements=>elements.map(e=>({
          tag:e.tagName,id:e.id,type:e.type,title:e.title,group:e.dataset.group||null,
          data:{...e.dataset},text:e.innerText||e.getAttribute('aria-label')||''
        }))''')
        assert len(controls) == 41 and sum(x['tag'] == 'BUTTON' for x in controls) == 32
        assert sum(x['tag'] == 'INPUT' for x in controls) == 1 and sum(bool(x['group']) for x in controls) == 8
        assert replay.state()['state']['timeOfDay'] == 18.5 and not replay.state()['panelCollapsed']
        replay.picture('inventory')
        return {'controls': controls, 'comparison': controls}

    def quality():
        rows = []
        for _ in range(3):
            before = scene.evaluate('__LAWSON__.api.getStats()')
            expected = {'low': 'high', 'high': 'medium', 'medium': 'low'}[before['quality']]
            scene.locator('#btn-settings').click()
            after = scene.evaluate('__LAWSON__.api.getStats()')
            assert after['quality'] == expected
            rows.append(after)
        replay.low()
        return {'actualRenderer': rows, 'comparison': [row['quality'] for row in rows]}

    def time_slider():
        slider = scene.locator('#time-slider')
        steps = []
        for key, expected in (('Home', 0), ('End', 24)):
            slider.press(key)
            assert float(slider.input_value()) == expected
            observed_time(scene, expected)
            steps.append(expected)
        rect = slider.evaluate('e=>e.getBoundingClientRect().toJSON()')
        scene.mouse.click(rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2)
        middle = float(slider.input_value())
        assert 11 < middle < 13
        observed_time(scene, middle)
        slider.press('ArrowRight')
        assert abs(float(slider.input_value()) - middle - .1) < .001
        observed_time(scene, middle + .1)
        return {'input': steps + [middle, middle + .1], 'comparison': steps + ['middle', .1]}

    def help_and_fold():
        scene.locator('#btn-help').click()
        assert scene.locator('#help').is_visible()
        text = scene.locator('#help').inner_text()
        replay.picture('help-original')
        scene.locator('#help-close').click()
        assert scene.locator('#help').is_hidden()
        scene.locator('#btn-help').click()
        scene.mouse.click(10, 10)
        assert scene.locator('#help').is_hidden()
        panel = scene.locator('#panel')
        original = panel.evaluate('e=>e.getBoundingClientRect().width')
        scene.locator('#panel-collapse').click()
        assert panel.evaluate('e=>e.classList.contains("collapsed")')
        folded = panel.evaluate('e=>e.getBoundingClientRect().width')
        assert folded < original
        scene.locator('#panel-collapse').click()
        assert not panel.evaluate('e=>e.classList.contains("collapsed")')
        return {'help': text, 'panelWidths': [original, folded], 'comparison': ['open', 'close', 'backdrop', 'fold', 'expand']}

    def keys():
        scene.mouse.click(10, 10)
        running = scene.evaluate('__LAWSON__.state.traffic.running')
        scene.keyboard.press('Space')
        assert scene.evaluate('__LAWSON__.state.traffic.running') is not running
        scene.keyboard.press('Space')
        assert scene.evaluate('__LAWSON__.state.traffic.running') is running
        scene.evaluate(literal('lawson-fullpage-step-7/supplement.py', 'SYSTEMS'))
        scene.locator('[data-cam=hero]').click()
        replay.observed()
        original = replay.state()
        scene.mouse.move(300, 320)
        scene.mouse.down()
        scene.mouse.move(430, 350, steps=4)
        scene.mouse.up()
        replay.observed(.2)
        assert replay.state()['projection'] != original['projection']
        scene.mouse.click(10, 10)
        scene.keyboard.press('r')
        scene.wait_for_function('!__fullpageAudit.cameraInstance?.tween', timeout=90000, polling=100)
        replay.observed(1)
        after = replay.state()
        assert after['state']['cameraMode'] == 'hero' and not after['state']['walk']
        assert scene.evaluate('__fullpageAudit.events.some(e=>e.kind==="keydown"&&e.code==="KeyR")')
        error = max(abs(x-y) for a, b in zip(original['projection'], after['projection']) for x, y in zip(a, b))
        before_hud = scene.locator('pre:visible').count()
        scene.keyboard.press('n')
        assert scene.locator('pre:visible').count() == before_hud
        return {'resetProjectionErrorCSSPx': error, 'documentedNHasNoRuntimeHUD': True,
                'comparison': {'spaceToggles': True, 'rHero': True, 'nActivatedHUD': False}}

    for identifier, action in (('controls-inventory', inventory), ('renderer-tiers', quality),
                               ('time-slider', time_slider), ('help-collapse', help_and_fold), ('scene-keys', keys)):
        replay.case(identifier, identifier, action)


def run_bundle(label, page, scene, side):
    replay = Replay(runner, page, scene, side, label)
    before = position(page)
    if label == 'interface':
        interface(replay)
    else:
        historical(replay, label)
    if side == 'embedded':
        assert position(page) == before, (before, position(page))
    checks = replay.report['checks']
    comparison = {row['id']: row['effect'].get('comparison', row['status']) for row in checks}
    if label == 'targets':
        comparison.update({row['id']: row['effect']['originalActivation']['action'] for row in checks if row['id'] != 'TARGETS.load'})
    return {'comparison': comparison, 'cases': list(comparison), 'details': f'{replay.folder.name}/details.json'}


def historical(replay, suite):
    # Point the historical journey at the same original, reached through the current entry.
    saved_run, saved_argv = previous.Run, sys.argv
    previous.Run = lambda *_args: replay
    sys.argv = [suite + '.py', '--run', 'inline-parity']
    try:
        runpy.run_path(str(OLD / (suite + '.py')))
    finally:
        previous.Run, sys.argv = saved_run, saved_argv


if __name__ == '__main__':
    runner = BrowserRun()
    try:
        for bundle in ('interface', 'supplement', 'targets'):
            runner.pairs('lawson-' + bundle, LAWSON, lambda page, scene, side, bundle=bundle: run_bundle(bundle, page, scene, side),
                         probe=previous.PROBE)
    finally:
        ok = runner.finish()
    raise SystemExit(0 if ok else 1)
