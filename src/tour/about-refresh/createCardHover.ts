import { clamp } from './dom';
import { restingReadingPose } from './createToolCard';
import type { ToolCardReadingPose, ToolCardView } from './createToolCard';
import type { CardTrackContext } from './types';
import './cardHover.css';

interface Point { x: number; y: number; }
interface Goal { width: number; reference: DOMRect; scale: number; x: number; y: number; z: number; pitch: number; yaw: number; }
interface Reading {
  id: string; view: ToolCardView; reference: DOMRect; goal: Goal;
  pose: ToolCardReadingPose; from: ToolCardReadingPose; started: number;
  leaving: boolean; keyboard: boolean; pressed: boolean; pinned: boolean; baseWidth: number; width: number; fromWidth: number; reveal: number; fromReveal: number;
}
const smooth = (x: number) => x * x * (3 - 2 * x);
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

/** A single intentional reading gesture; no horizontal clock and no DOM copies. */
export function createCardHover(options: {
  root: HTMLElement; rail: HTMLElement; views: ReadonlyMap<string, ToolCardView>;
  hold(held: boolean): void; interaction(): void; changed(): void; pinnedChanged(id: string | null): void; nativePinned(): void; layoutChanged(): void;
}) {
  const { root, rail, views } = options;
  const events = new AbortController(), abort = { signal: events.signal };
  const fine = matchMedia('(hover:hover) and (pointer:fine)'), reduced = matchMedia('(prefers-reduced-motion:reduce)');
  let context: CardTrackContext = { active: false, allowed: false, automatic: false, top: 0, bottom: 0 };
  let ready = false, disposed = false, active: Reading | undefined;
  let candidate: { id: string; point: Point } | undefined, queued: { id: string; point: Point } | undefined;
  let pointer: Point | undefined, lastPointer: Point | undefined, lastInput = -Infinity;
  let timer: number | undefined, leaveTimer: number | undefined, pressTimer: number | undefined, focusTimer: number | undefined, frame: number | undefined, lastFrame = 0;
  let state = 'idle', wantedPin: string | null = null, suppressed = '', blockedPin = '';
  let pinRefresh: number | undefined;
  let departureHeld = false, departureStarted = 0;
  let touchInput = false;

  function publish(next: string) {
    state = next;root.dataset.hoverState = next;root.dataset.hoverId = active?.id ?? candidate?.id ?? '';
    root.dataset.hoverSource = active?.pinned ? 'pinned' : active?.keyboard ? 'keyboard' : active ? 'pointer' : '';
    root.dataset.detailMode = wantedPin ? 'pinned' : active && !active.leaving ? 'preview' : 'summary';
    root.dataset.readingId = wantedPin ?? active?.id ?? '';
    options.changed();
  }
  function wideEnvironment() {
    return !touchInput && fine.matches && !reduced.matches && innerWidth >= 1180 && root.closest<HTMLElement>('.about-refresh')?.dataset.largeText !== 'true';
  }
  function pinKey() { return JSON.stringify([wantedPin,innerWidth,innerHeight,context,ready,wideEnvironment()]); }
  function renderIdlePin() {
    if (departureHeld) return;
    const view = wantedPin ? views.get(wantedPin) : undefined;
    if (!view || !rail.contains(view.element) || active?.pinned) return;
    const wide = wideEnvironment() && blockedPin !== pinKey();
    const previousWide = view.element.dataset.detailWide, previousState = view.element.dataset.detailState;
    if (previousWide === String(wide) && previousState === 'pinned') return;
    view.setDetail('pinned', wide ? 360 : undefined);
    if (!wide) options.nativePinned();
    if (!wide && (previousWide !== 'false' || previousState !== 'pinned')) options.layoutChanged();
  }
  function eligible() {
    if (departureHeld || disposed || touchInput || !ready || !context.active || !context.allowed || !fine.matches || reduced.matches || document.hidden || innerWidth < 1180) return false;
    const host = root.closest<HTMLElement>('.about-refresh');
    if (host?.dataset.largeText === 'true') return false;
    const b = rail.getBoundingClientRect();
    return b.width >= 700 && b.top >= context.top - 1 && b.bottom <= context.bottom + 1 && !rail.hidden;
  }
  function quiet() {
    return performance.now() - lastInput >= 220 && root.dataset.trackWheelActive !== 'true' && Math.abs(Number(root.dataset.trackSpeed) || 0) <= 40;
  }
  function clearCandidate() {
    if (timer !== undefined) clearTimeout(timer);timer = undefined;candidate = undefined;root.dataset.hoverPending = 'false';
  }
  function stopFrame() {
    if (frame !== undefined) cancelAnimationFrame(frame);frame = undefined;lastFrame = 0;root.dataset.hoverFramePending = 'false';
  }
  function clearLeave() { if (leaveTimer !== undefined) clearTimeout(leaveTimer);leaveTimer = undefined; }
  function finish() {
    stopFrame();
    if (active) { active.view.setReading();active.view.setDetail('summary');delete active.view.element.dataset.reading; }
    active = undefined;renderIdlePin();options.hold(false);publish(disposed ? 'disposed' : 'idle');
  }
  function cancel(reason: string) {
    if (departureHeld) return;
    clearCandidate();clearLeave();
    if (pressTimer !== undefined) clearTimeout(pressTimer);pressTimer = undefined;
    if (focusTimer !== undefined) clearTimeout(focusTimer);focusTimer = undefined;
    queued = undefined;finish();root.dataset.hoverReason = reason;
  }
  function cardAt(point: Point) {
    const box = rail.getBoundingClientRect();
    if (point.x < box.left || point.x > box.right || point.y < box.top || point.y > box.bottom) return undefined;
    const card = document.elementFromPoint(point.x, point.y)?.closest<HTMLElement>('.ar-tool-card');
    return card && rail.contains(card) && !card.inert ? card.dataset.toolId : undefined;
  }
  function schedule() {
    if (frame !== undefined || disposed || departureHeld) return;
    frame = requestAnimationFrame(tick);root.dataset.hoverFramePending = 'true';
  }
  function leave() {
    if (departureHeld) return;
    clearCandidate();clearLeave();
    if (!active || active.leaving || active.pressed || active.pinned) return;
    active.leaving = true;active.started = performance.now();active.from = { ...active.pose };active.fromWidth = active.width;active.fromReveal = active.reveal;publish('leaving');schedule();
  }
  function deferLeave() {
    if (departureHeld || leaveTimer !== undefined || !active || active.keyboard || active.pinned || active.pressed) return;
    leaveTimer = window.setTimeout(() => { leaveTimer = undefined;leave(); }, 90);
  }
  function safeGoal(view: ToolCardView, keyboard: boolean): Goal | undefined {
    const b = rail.getBoundingClientRect();
    const safe = { left: b.left + 8, right: b.right - 8, top: Math.max(context.top + 2, b.top + 8), bottom: Math.min(context.bottom - 2, b.bottom - 8) };
    const baseZ = parseFloat(view.element.style.getPropertyValue('--ar-card-z')) || 0;
    const baseFront = view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect();
    const projectedScale = clamp(baseFront.width / view.element.getBoundingClientRect().width, .94, 1.02);
    const profiles = [
      { scale: 1.08, z: 36, pitch: 3, yaw: 5, y: -8 },
      { scale: 1.06, z: 34, pitch: 2.5, yaw: 4, y: -7 },
      { scale: 1.04, z: 32, pitch: 2, yaw: 3, y: -6 },
      { scale: 1.02, z: 30, pitch: 1.5, yaw: 2, y: -6 },
    ];
    let chosen: Goal | undefined;
    for (const panelWidth of [360,340]) {
      view.probeDetail(panelWidth, () => {
        for (const profile of profiles) {
          const goal: Goal = { ...profile, width: panelWidth, reference: new DOMRect(), z: profile.z - baseZ, scale: Math.max(1.02, profile.scale * projectedScale), x: 0, pitch: keyboard ? 0 : profile.pitch, yaw: keyboard ? 0 : profile.yaw };
          const bounds = () => {
            const boxes = [];
            for (const pitch of [-goal.pitch, goal.pitch]) for (const yaw of [-goal.yaw, goal.yaw]) {
              view.setReading({ amount: 1, x: goal.x, y: goal.y, z: goal.z, scale: goal.scale, pitch, yaw });boxes.push(view.measure().bounds);
            }
            return { left: Math.min(...boxes.map(r => r.left)), right: Math.max(...boxes.map(r => r.right)), top: Math.min(...boxes.map(r => r.top)), bottom: Math.max(...boxes.map(r => r.bottom)) };
          };
          let box = bounds();
          if (box.right - box.left > safe.right - safe.left || box.bottom - box.top > safe.bottom - safe.top) continue;
          for (let pass = 0; pass < 3; pass++) {
            goal.x += Math.max(0, safe.left - box.left) + Math.min(0, safe.right - box.right);
            goal.y += Math.max(0, safe.top - box.top) + Math.min(0, safe.bottom - box.bottom);box = bounds();
          }
          if (box.left >= safe.left - .5 && box.right <= safe.right + .5 && box.top >= safe.top - .5 && box.bottom <= safe.bottom + .5) {
            view.setReading({ amount: 1, x: goal.x, y: goal.y, z: goal.z, scale: goal.scale, pitch: 0, yaw: 0 });
            goal.reference = view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect();chosen = goal;break;
          }
        }
        view.setReading();
      });
      if (chosen) break;
    }
    return chosen;
  }
  function begin(id: string, keyboard = false, pinned = false, instant = false) {
    clearCandidate();clearLeave();
    const view = views.get(id);
    if (!view || !eligible() || !pinned && !keyboard && !quiet() || !pinned && wantedPin !== null) { publish('idle');return false; }
    options.hold(true);
    const goal = safeGoal(view, keyboard || pinned);
    if (!goal) { blockedPin = pinKey();renderIdlePin();options.hold(false);publish('idle');return false; }
    const baseWidth = view.element.closest<HTMLElement>('.ar-tool-slot')!.getBoundingClientRect().width;
    active = { id, view, reference: goal.reference, goal, pose: { ...restingReadingPose }, from: { ...restingReadingPose }, started: performance.now() - (instant ? 400 : 0), leaving: false, keyboard, pressed: false, pinned, baseWidth, width: baseWidth, fromWidth: baseWidth, reveal: 0, fromReveal: 0 };
    view.setDetail(pinned ? 'pinned' : 'preview', baseWidth, 0);
    view.element.dataset.reading = 'true';root.dataset.hoverProfile = JSON.stringify(goal);root.dataset.hoverWorldDepth = String(goal.z + (parseFloat(view.element.style.getPropertyValue('--ar-card-z')) || 0));
    if (!instant) options.interaction();publish('entering');
    if (instant) tick(performance.now());else schedule();return true;
  }
  function clearPin(animate = false) {
    const old = wantedPin;wantedPin = null;blockedPin = '';
    if (pinRefresh !== undefined) clearTimeout(pinRefresh);pinRefresh = undefined;
    if (old) { suppressed = old;options.pinnedChanged(null); }
    if (active?.pinned && animate) { active.pressed = false;active.pinned = false;leave(); }
    else { cancel('unpin');if (old) views.get(old)?.setDetail('summary'); }
  }
  function pin(id: string) {
    if (!views.has(id)) return;
    suppressed = '';blockedPin = '';
    if (wantedPin && wantedPin !== id) { const old = wantedPin;wantedPin = null;cancel('pin-switch');views.get(old)?.setDetail('summary'); }
    wantedPin = id;options.pinnedChanged(id);
    if (active?.id === id && !active.leaving) {
      active.pinned = true;active.keyboard = true;active.pressed = false;active.goal.pitch = 0;active.goal.yaw = 0;
      options.hold(true);active.view.setDetail('pinned', active.width, active.reveal);publish('entering');schedule();return;
    }
    cancel('pin');
    if (!begin(id, true, true)) renderIdlePin();
  }
  function arm(id: string, point: Point) {
    clearCandidate();
    if (!eligible() || !quiet() || wantedPin || id === suppressed) { if (!active) publish('idle');return; }
    candidate = { id, point };root.dataset.hoverPending = 'true';publish('pending');
    timer = window.setTimeout(() => {
      timer = undefined;const next = candidate;
      if (!next || !pointer || cardAt(pointer) !== next.id) { clearCandidate();if (!active) publish('idle');return; }
      begin(next.id);
    }, 120);
  }
  function tick(now: number) {
    frame = undefined;root.dataset.hoverFramePending = 'false';
    if (!active || !eligible()) { cancel('presentation-changed');return; }
    const a = active;
    if (a.pressed) { stopFrame();return; }
    const dt = lastFrame ? Math.min((now - lastFrame) / 1000, .1) : .016;lastFrame = now;
    const elapsed = now - a.started;
    const t = smooth(clamp((elapsed - (a.leaving ? 60 : 0)) / (a.leaving ? 240 : 260), 0, 1));
    if (a.leaving) {
      a.reveal = a.fromReveal * (1 - smooth(clamp(elapsed / 100, 0, 1)));
      a.width = mix(a.fromWidth, a.baseWidth, smooth(clamp((elapsed - 100) / 200, 0, 1)));
      const from = a.from;
      a.pose = { amount: from.amount * (1 - t), x: from.x * (1 - t), y: from.y * (1 - t), z: from.z * (1 - t), scale: mix(from.scale, 1, t), pitch: from.pitch * (1 - t), yaw: from.yaw * (1 - t) };
    } else {
      a.width = mix(a.baseWidth, a.goal.width, smooth(clamp(elapsed / 220, 0, 1)));
      a.reveal = smooth(clamp((elapsed - 210) / 140, 0, 1));
      const px = !a.keyboard && pointer ? clamp((pointer.x - a.reference.x) / a.reference.width * 2 - 1, -1, 1) : 0;
      const py = !a.keyboard && pointer ? clamp((pointer.y - a.reference.y) / a.reference.height * 2 - 1, -1, 1) : 0;
      const response = 1 - Math.exp(-dt / .07);
      a.pose = { amount: t, x: a.goal.x * t, y: a.goal.y * t, z: a.goal.z * t, scale: mix(1, a.goal.scale, t),
        pitch: mix(a.pose.pitch, -py * a.goal.pitch * t, response), yaw: mix(a.pose.yaw, px * a.goal.yaw * t, response) };
      if (t === 1 && a.reveal === 1 && Math.abs(a.pose.pitch + py * a.goal.pitch) < .015 && Math.abs(a.pose.yaw - px * a.goal.yaw) < .015) {
        a.pose.pitch = -py * a.goal.pitch;a.pose.yaw = px * a.goal.yaw;
        a.view.setDetail(a.pinned ? 'pinned' : 'preview', a.width, a.reveal);a.view.setReading(a.pose);publish('reading');stopFrame();return;
      }
    }
    a.view.setDetail(a.leaving && a.reveal === 0 ? 'summary' : a.pinned ? 'pinned' : 'preview', a.width, a.reveal);a.view.setReading(a.pose);
    if (a.leaving && t === 1) {
      const next = queued;queued = undefined;finish();
      if (next && pointer && cardAt(pointer) === next.id) arm(next.id, pointer);
      return;
    }
    schedule();
  }
  function move(event: PointerEvent) {
    if (departureHeld) return;
    if (event.pointerType !== 'mouse' || event.buttons) return;
    const next = { x: event.clientX, y: event.clientY }, moved = !lastPointer || Math.hypot(next.x - lastPointer.x, next.y - lastPointer.y) >= 1.5;
    pointer = next;
    if (!moved) return;lastPointer = next;
    if (!eligible()) { cancel('unavailable');return; }
    const id = cardAt(next);
    if (suppressed && id !== suppressed) suppressed = '';
    if (wantedPin) return;
    if (active?.keyboard && document.activeElement && active.view.element.contains(document.activeElement)) return;
    if (active) {
      if (id === active.id && !active.leaving) { clearLeave();schedule();return; }
      if (id && id !== active.id) { queued = { id, point: next };leave();return; }
      const b = active.view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect();
      if (!active.leaving && next.x >= b.left - 8 && next.x <= b.right + 8 && next.y >= b.top - 8 && next.y <= b.bottom + 8) { clearLeave();schedule(); }
      else deferLeave();
      return;
    }
    if (!id) { clearCandidate();publish('idle');return; }
    if (candidate?.id === id) { candidate.point = next;return; }
    arm(id, next);
  }
  rail.addEventListener('pointermove', move, abort);
  rail.addEventListener('pointerleave', () => { pointer = undefined;lastPointer = undefined;queued = undefined;suppressed = '';clearCandidate();deferLeave(); }, abort);
  rail.addEventListener('pointerdown', event => {
    if (departureHeld) return;
    clearCandidate();clearLeave();queued = undefined;
    if (active && active.view.element.contains(event.target as Node)) {
      active.pressed = true;stopFrame();publish('pressed');
    } else cancel('pointerdown');
  }, { ...abort, capture: true });
  window.addEventListener('pointerup', () => {
    if (!active?.pressed) return;
    // Keep the real button under the pointer through the native click dispatch.
    const id = active.id;
    pressTimer = window.setTimeout(() => { pressTimer = undefined;if (active?.id === id && active.pressed) { active.pressed = false;if (active.pinned) { publish('reading');schedule(); } else leave(); } }, 0);
  }, abort);
  rail.addEventListener('pointercancel', () => cancel('pointercancel'), abort);
  rail.addEventListener('scroll', () => {
    if (root.dataset.trackMode === 'program') return;
    lastInput = performance.now();
    const focused = document.activeElement instanceof HTMLElement && document.activeElement.matches(':focus-visible') ? document.activeElement.closest<HTMLElement>('.ar-tool-card')?.dataset.toolId : undefined;
    cancel('native-scroll');
    if (focused) focusTimer = window.setTimeout(() => { focusTimer = undefined;if (views.get(focused)?.element.contains(document.activeElement)) begin(focused, true); }, 180);
  }, { ...abort, passive: true });
  window.addEventListener('scroll', () => cancel('page-scroll'), { ...abort, passive: true });
  window.addEventListener('resize', () => { blockedPin = '';cancel('resize');if (pinRefresh !== undefined) clearTimeout(pinRefresh);pinRefresh = window.setTimeout(() => { pinRefresh = undefined;restorePin(); }, 350); }, abort);
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancel('page-hidden'); }, abort);
  fine.addEventListener('change', () => cancel('pointer-mode'), abort);reduced.addEventListener('change', () => cancel('motion-mode'), abort);
  function restorePin() {
    if (departureHeld || !wantedPin || disposed) return;
    if (!active && eligible() && blockedPin !== pinKey()) begin(wantedPin, true, true, true);
    else if (!active) renderIdlePin();
  }
  root.dataset.hoverState = state;root.dataset.hoverPending = 'false';root.dataset.hoverFramePending = 'false';
  return {
    get available() { return eligible(); },
    setTouchInput(next: boolean) {
      if (disposed || next === touchInput) return;
      touchInput = next;blockedPin = '';
      if (next) { pointer = undefined;lastPointer = undefined;cancel('touch-input'); }
      else restorePin();
    },
    suspendForDeparture(held: boolean, returned = false) {
      if (held === departureHeld) return;
      departureHeld = held;root.dataset.hoverDepartureHeld = String(held);
      if (held) {
        departureStarted = performance.now();clearCandidate();clearLeave();stopFrame();queued = undefined;pointer = undefined;lastPointer = undefined;
        for (const id of [pressTimer,focusTimer,pinRefresh]) if (id !== undefined) clearTimeout(id);
        pressTimer = focusTimer = pinRefresh = undefined;
      } else if (returned && active) {
        active.started += performance.now() - departureStarted;active.pressed = false;
        if (active.pinned) { publish('entering');schedule(); }
        else { active.leaving = false;leave(); }
      } else cancel('departure-ended');
    },
    present(next: CardTrackContext, entryReady: boolean) {
      const oldKey = pinKey();context = next;ready = entryReady;
      if (departureHeld) return;
      if (pinKey() !== oldKey) blockedPin = '';
      if ((!next.active || !next.allowed || !entryReady || reduced.matches || !fine.matches) && (active || candidate || frame !== undefined)) cancel('presentation-changed');
      restorePin();
    },
    wheel() { lastInput = performance.now();lastPointer = pointer ? { ...pointer } : undefined;cancel('wheel'); },
    cancel, pin, clearPin,
    restorePinned(id: string | null) {
      if (wantedPin !== id) { const old = wantedPin;wantedPin = null;cancel('restore-pin');if (old) views.get(old)?.setDetail('summary');wantedPin = id; }
      suppressed = '';blockedPin = '';renderIdlePin();restorePin();publish(active ? state : 'idle');
    },
    focus(id: string) {
      if (departureHeld) return;
      if (wantedPin || suppressed === id) return;
      if (active?.id === id && !active.leaving) { options.hold(true);active.keyboard = true;active.goal.pitch = 0;active.goal.yaw = 0;publish('entering');schedule();return; }
      cancel('keyboard-focus');
      if (root.dataset.trackMode === 'program') begin(id, true);
      else focusTimer = window.setTimeout(() => { focusTimer = undefined;if (views.get(id)?.element.contains(document.activeElement)) begin(id, true); }, 180);
    },
    blur() { if (departureHeld) return;suppressed = '';if (focusTimer !== undefined) clearTimeout(focusTimer);focusTimer = undefined;if (active?.keyboard && !active.pinned) leave(); },
    escape() { if (rail.hidden) return false;if (wantedPin) { clearPin(true);return true; }if (active) suppressed = active.id;if (!active && focusTimer === undefined) return false;cancel('escape');return true; },
    dispose() { if (disposed) return;wantedPin = null;if (pinRefresh !== undefined) clearTimeout(pinRefresh);pinRefresh = undefined;cancel('disposed');disposed = true;events.abort();publish('disposed'); },
  };
}
