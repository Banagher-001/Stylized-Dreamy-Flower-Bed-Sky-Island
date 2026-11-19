"""Replay the original Bottle control assertions against the in-place window."""
import hashlib
import runpy
import sys
from types import SimpleNamespace

from pair_support import BOTTLE, BrowserRun, CHILD, DESKTOP, PHONE, TESTS


OLD = TESTS / 'beach-bottle-boat-step-7'
sys.path.insert(0, str(OLD))
import harness as previous


class ReplaySession(previous.Session):
    def open(self):
        embedded = self.side == 'embedded'
        host, touch, dpr = self.config
        self.ctx, self.page, self.events = runner.context(host if embedded else CHILD[host], touch, dpr, previous.PROBE)
        self.surface, self.conditions = runner.open(self.page, BOTTLE, embedded, touch)
        self.evaluate(previous.EVENTS)
        self.tick()
        snapshot = self.snapshot()
        assert snapshot['diagnostics']['renderer']['triangles'] > 1000
        canvas = [snapshot['canvas'][axis] for axis in ('width', 'height')]
        assert canvas == self.conditions['viewport'] == list(CHILD[host]), (canvas, self.conditions)
        assert self.conditions['dpr'] == dpr
        self.conditions.update(canvas=canvas, touch=touch)

    def close(self):
        if self.ctx:
            self.ctx.close()


def hidden_export(scene):
    scene.reset()
    button = scene.locator('[data-action=screenshot]')
    button.focus()
    assert button.evaluate('e=>document.activeElement===e')
    scene.page.keyboard.press('h')
    scene.surface.wait_for_function('''() => document.body.classList.contains('ui-hidden') &&
      getComputedStyle(document.querySelector('#control-panel')).visibility==='hidden' ''', polling=100)
    scene.frames(3)
    focused = button.evaluate('e=>document.activeElement===e')
    scene.locator('#restore-ui').click()
    assert not scene.evaluate('document.body.classList.contains("ui-hidden")')
    image = scene.download('restored-original-png')
    return {'download':image,'comparison':{'PNG':image['PNG'],'focusRetainedWhenHidden':focused,
                                           'originalExportAfterRestore':True}}


class Replay:
    def __init__(self, args):
        self.args = args
        self.folder = runner.out

    def pair(self, case_id, controls, action, config='desktop'):
        if not runner.selected(case_id) or case_id == 'INPUT.keyboard':
            return
        if case_id == 'EXPORT.hidden':
            action = hidden_export
        self.case_id = case_id
        dimensions = (DESKTOP, False, 1) if config == 'desktop' else (PHONE, True, 3)

        def run_pair():
            sides = {}
            for side in ('reference', 'embedded'):
                scene = ReplaySession(self, side, dimensions)
                try:
                    scene.open()
                    observations = action(scene)
                    assert not (scene.events['errors'] or scene.events['external'] or scene.events['unexpectedHttp']), scene.events
                    assert all(error == 'net::ERR_ABORTED' for error, _ in scene.events['failures']), scene.events
                    sides[side] = {'conditions': scene.conditions, 'observations': observations, 'network': scene.events}
                    print(case_id, side, 'captured', flush=True)
                except Exception:
                    if scene.page and not scene.page.is_closed():
                        scene.picture('failure-' + case_id)
                    raise
                finally:
                    scene.close()
            previous.close_values(sides['reference']['observations']['comparison'], sides['embedded']['observations']['comparison'])
            return {'controls': controls, **sides}

        runner.record(case_id, run_pair)

    def finish(self):
        # The three original suites share the same browser in this replay.
        pass


runner = BrowserRun()
previous.Run = Replay
previous.arguments = lambda: SimpleNamespace(engine='chromium')
previous.row = lambda path: {'path': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
try:
    for suite in ('controls', 'actions', 'dynamics'):
        runpy.run_path(str(OLD / (suite + '.py')))
finally:
    ok = runner.finish()
raise SystemExit(0 if ok else 1)
