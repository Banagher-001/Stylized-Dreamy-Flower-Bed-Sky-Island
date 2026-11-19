"""Read real input and card positions without changing the application's clock."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/about-refresh-final'))
from support import Run, save

ROOT_SELECTOR = '.ar-tools-browser'
DESKTOP = (1652, 949)


def choose(page, category):
    choice = page.locator(f'button[data-category="{category}"]')
    if choice.is_visible():
        choice.click()
    else:
        page.locator('.ar-category-select select').select_option(category)
    page.wait_for_function('(category) => document.querySelector(".ar-tools-browser").dataset.category === category', arg=category)


def snapshot(page):
    return page.evaluate('''() => {
      const root = document.querySelector('.ar-tools-browser');
      const rail = root.querySelector('.ar-tool-rail');
      const host = document.querySelector('#tour-host');
      const t = root.dataset;
      return { at:performance.now(), x:rail.scrollLeft, y:scrollY,
        maxX:rail.scrollWidth-rail.clientWidth, mode:t.trackMode,
        enabled:t.trackEnabled==='true', state:t.trackState, reason:t.trackReason,
        framePending:t.trackFramePending==='true', speed:Number(t.trackSpeed||0),
        distance:Number(t.trackDistance||0), target:host.dataset.targetH,
        camera:host.dataset.cameraState, entrance:t.entrance, entranceReason:t.entranceReason,
        subphase:t.entranceSubphase, departure:t.departure, detail:t.detailMode,
        category:t.category, count:Number(t.cardCount),
        ids:[...root.querySelectorAll('.ar-tool-card')].map(e => e.dataset.cardInstance) };
    }''')


def points(page):
    return page.evaluate('''() => {
      const root = document.querySelector('.ar-tools-browser');
      const rail = root.querySelector('.ar-tool-rail');
      const a = rail.getBoundingClientRect();
      const c = root.querySelector('.ar-tool-controls').getBoundingClientRect();
      const f = root.querySelector('.ar-filter-bar').getBoundingClientRect();
      const cards = [...rail.querySelectorAll('.ar-tool-slot')].map(e => e.getBoundingClientRect())
        .filter(r => r.left >= a.left && r.right <= a.right).sort((a,b) => a.left-b.left);
      const y = (Math.max(0, f.bottom, a.top) + Math.min(innerHeight, c.top, a.bottom))/2;
      const card = cards[0];
      return { face:[card ? (card.left+card.right)/2 : (a.left+a.right)/2,y],
        gap:[cards.length>1 ? (cards[0].right+cards[1].left)/2 : (a.left+a.right)/2,y],
        left:[(c.left+a.left)/2,y], right:[(a.right+c.right)/2,y],
        center:[(a.left+a.right)/2,y], outside:[Math.max(8,c.left-14),y] };
    }''')


def wait_ready(page):
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady === "true"')


def enter_paused(r, page):
    r.go(page, 'A3')
    wait_ready(page)
    if snapshot(page)['enabled']:
        page.locator('[data-action="auto"]').click()
    choose(page, 'G6')
    page.mouse.move(24, 300)
    page.wait_for_function('''() => {
      const t=document.querySelector('.ar-tools-browser').dataset;
      return t.trackEnabled === 'false' && t.trackMode === 'native' && !Number(t.trackSpeed);
    }''')
    assert snapshot(page)['count'] == 5


START_TRACE = '''() => {
  window.wheelTrace?.stop();
  const root = document.querySelector('.ar-tools-browser');
  const rail = root.querySelector('.ar-tool-rail');
  const host = document.querySelector('#tour-host');
  const frames = [], events = [], stops = [];
  let frame, wasMoving = false;
  const wheel = e => events.push({ at:performance.now(), x:e.clientX, y:e.clientY,
    dx:e.deltaX, dy:e.deltaY, trusted:e.isTrusted, cancelable:e.cancelable, claimed:e.defaultPrevented });
  function read() {
    const t = root.dataset;
    frames.push({ at:performance.now(), x:rail.scrollLeft, distance:Number(t.trackDistance||0),
      speed:Number(t.trackSpeed||0), y:scrollY, target:host.dataset.targetH,
      active:t.trackWheelActive==='true', pending:t.trackFramePending==='true',
      entrance:t.entrance, reason:t.entranceReason, mode:t.trackMode });
    if (frames.length < 250) frame = requestAnimationFrame(read);
  }
  // Observe the completed update. The sampler's RAF may run before the track's
  // callback and report the old pose for an extra frame.
  const track = new MutationObserver(() => {
    const t = root.dataset;
    const moving = t.trackFramePending === 'true' || t.trackWheelActive === 'true' || Boolean(Number(t.trackSpeed));
    if (wasMoving && !moving) stops.push(performance.now());
    wasMoving = moving;
  });
  track.observe(root, {attributes:true, attributeFilter:['data-track-frame-pending','data-track-wheel-active','data-track-speed']});
  window.addEventListener('wheel',wheel,{passive:true});
  window.wheelTrace = {frames, events, stop() {
    cancelAnimationFrame(frame);track.disconnect();window.removeEventListener('wheel',wheel);return {frames,events,stops};
  }};
  read();
}'''
