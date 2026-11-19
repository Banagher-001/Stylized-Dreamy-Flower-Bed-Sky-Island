import { clamp, element } from './dom';
import type { ToolCardView } from './createToolCard';
import type { CardTrackContext, CardTrackSnapshot, TrackPosition } from './types';
import { cardWheelMotion, createWheelVelocity } from './cardWheelInput';
import type { TrackDirection, WheelAxis } from './cardWheelInput';
import './cardTrack.css';

interface Item { id: string; slot: HTMLElement; view: ToolCardView; base: number; width: number; style: string | null; slotStyle: string | null; painted: boolean; }
type TrackState = 'waiting' | 'running' | 'paused' | 'suspended' | 'static' | 'disposed';
export type CardTrackActivity = 'still' | 'automatic' | 'manual';
const speed = cardWheelMotion.baseSpeed;
const readingResumeDelay = 180;
const edgeBrakeDistance = 48;
const edgeCueDuration = 160;
const guard = 64;
const rightGuard = 40;
const rest = { pitch: 0, yaw: 0, roll: 0 };

function nativeDestination(x: number, limit: number, delta: number, damped: boolean) {
  if (!delta) return x;
  const edge = delta > 0 ? limit : 0;
  const distance = Math.abs(edge - x);
  const t = clamp(distance / edgeBrakeDistance, 0, 1);
  const approach = t * t * (3 - 2 * t);
  const factor = damped ? .4 + .6 * approach * approach : 1;
  const travel = Math.abs(delta) * factor;
  return distance - travel <= 1 ? edge : x + Math.sign(delta) * travel;
}

/** Single physical card per ID. Only fully offscreen slots change circulation. */
export function createCardTrack(options: {
  root: HTMLElement; rail: HTMLElement; controls: HTMLElement;
  views: ReadonlyMap<string, ToolCardView>;
  nativePosition(): TrackPosition;
  restoreNative(position: TrackPosition): void;
  cursor(id: string, position: TrackPosition): void;
  changed(): void;
}) {
  const { root, rail, controls, views } = options;
  const events = new AbortController();
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let context: CardTrackContext = { active: false, allowed: false, automatic: false, top: 0, bottom: 0 };
  let entryReady = false, entryReason = '', signature = '', state: TrackState = 'waiting';
  let intent = false, decided = false, disposed = false, items: Item[] = [], stage: HTMLElement | undefined;
  let saved: CardTrackSnapshot | undefined, savedIDs = '';
  let phase = 0, cycled = false, period = 0, distance = 0, cycles = 0, width = 0, padding = 0;
  let bend = 0, last = 0, startAt = 0, frame: number | undefined, resizeTimer: number | undefined;
  let resumeAt = 0, resumeTimer: number | undefined;
  let cursor = '', stateSignature = '';
  let direction: TrackDirection = 1, velocity = 0, targetSpeed = 0, leadIn = 0;
  const wheel = createWheelVelocity();
  let nativeWheel: { x: number; limit: number } | undefined;
  let edgeCue: TrackDirection | undefined, edgeTimer: number | undefined;
  let lastEdgeInput = -Infinity;
  let lastEdgeDirection: TrackDirection | undefined;
  let readingHeld = false;
  let departureHeld = false;
  let touchInput = false;
  let entranceHandoffUsed = false;

  const slots = () => [...rail.querySelectorAll<HTMLElement>('.ar-tool-slot')];
  const supported = () => context.allowed && fine.matches && !reduced.matches && !touchInput;
  // Only the explicit controls write the choice. Context supplies a default
  // for an untouched track, and independently determines whether it can move.
  const preferred = () => decided ? intent : context.automatic && (!entryReady || entryReason === 'completed');
  function fitsOneScreen() {
    if (items.length) return period - leadIn - (parseFloat(getComputedStyle(stage!).columnGap) || 24) <= width - padding * 2 + .5;
    return rail.scrollWidth <= rail.clientWidth + 1;
  }
  function viewable() {
    const a = rail.getBoundingClientRect(), b = controls.getBoundingClientRect();
    return a.width >= 700 && a.height > 0 && a.top >= context.top - 1 && b.bottom <= context.bottom + 1;
  }
  function stop() {
    if (frame !== undefined) cancelAnimationFrame(frame);
    frame = undefined;last = 0;root.dataset.trackFramePending = 'false';
  }
  function cancelResume() {
    if (resumeTimer !== undefined) clearTimeout(resumeTimer);
    resumeTimer = undefined;
    resumeAt = 0;
  }
  function delayResume() {
    cancelResume();
    resumeAt = performance.now() + readingResumeDelay;
  }
  function clearMotion() {
    cancelResume();
    wheel.clear();nativeWheel = undefined;velocity = 0;targetSpeed = 0;stop();
    root.dataset.trackSpeed = '0.0000';root.dataset.trackTargetSpeed = '0.0000';root.dataset.trackWheelActive = 'false';
  }
  function clearEdgeCue() {
    if (edgeTimer !== undefined) clearTimeout(edgeTimer);
    edgeTimer = undefined;
    delete rail.dataset.edgeContact;
  }
  function releaseEdgeGesture() {
    clearEdgeCue();
    edgeCue = lastEdgeDirection = undefined;
    lastEdgeInput = -Infinity;
  }
  function showEdge(side: TrackDirection) {
    if (edgeCue === side || lastEdgeInput === -Infinity || reduced.matches) return;
    clearEdgeCue();
    edgeCue = side;
    rail.dataset.edgeContact = side < 0 ? 'start' : 'end';
    edgeTimer = window.setTimeout(clearEdgeCue, edgeCueDuration);
  }
  function publish(next: TrackState, reason: string) {
    state = next;
    root.dataset.trackState = next;root.dataset.trackReason = reason;
    root.dataset.trackEnabled = String(preferred());
    root.dataset.trackMode = stage ? 'program' : 'native';root.dataset.trackHeld = String(readingHeld);
    const value = `${next}|${reason}|${root.dataset.trackEnabled}|${!!stage}|${canToggle()}`;
    if (value !== stateSignature) { stateSignature = value;options.changed(); }
  }
  function position(): TrackPosition {
    if (!items.length || !period) return saved?.position ?? options.nativePosition();
    const anchor = items.find(item => item.id === cursor) ?? items[0]!;
    // A signed offset also represents the leading card during a reverse seam.
    // Native handoff then retains that card instead of jumping to the last page.
    const offset = ((phase - anchor.base + period / 2) % period + period) % period - period / 2;
    return { anchorId: anchor.id, offsetRatio: offset / anchor.width, scrollLeft: phase, viewportWidth: width };
  }
  function capture(): CardTrackSnapshot {
    return { position: stage ? position() : saved?.position ?? options.nativePosition(), program: !!stage || !!saved?.program,
      cycled: stage ? cycled : saved?.cycled ?? cycled, enabled: preferred(), decided,
      bend: stage ? bend : saved?.bend ?? bend, direction, leadIn: stage ? leadIn : saved?.leadIn ?? leadIn };
  }
  function detach(remember = true) {
    clearMotion();releaseEdgeGesture();
    if (!stage) return;
    const snapshot = capture();
    const focused = document.activeElement instanceof HTMLElement && stage.contains(document.activeElement) ? document.activeElement : undefined;
    for (const item of items) {
      item.view.setPose(rest);
      if (item.style === null) item.view.element.removeAttribute('style');else item.view.element.setAttribute('style', item.style);
      item.view.setReading();
      if (item.slotStyle === null) item.slot.removeAttribute('style');else item.slot.setAttribute('style', item.slotStyle);
      item.view.element.inert = false;item.view.element.removeAttribute('aria-hidden');
      delete item.slot.dataset.trackVisible;
      rail.append(item.slot);
    }
    stage.remove();stage = undefined;items = [];rail.removeAttribute('data-track-mode');
    saved = remember ? snapshot : undefined;
    options.restoreNative(snapshot.position);
    focused?.focus({ preventScroll: true });
  }
  function bind() {
    if (stage) return true;
    const nodes = slots();
    if (!nodes.length || nodes.some(slot => !views.has(slot.dataset.cardId!))) return false;
    releaseEdgeGesture();
    const ids = nodes.map(node => node.dataset.cardId).join(',');
    const restoreBend = saved?.program && savedIDs === ids ? saved.bend ?? 1 : 0;
    const seed = saved?.program && savedIDs === ids ? saved.position : options.nativePosition();
    cycled = !!(saved?.program && savedIDs === ids && saved.cycled);
    padding = parseFloat(getComputedStyle(rail).paddingLeft) || 0;width = rail.clientWidth;
    const gap = parseFloat(getComputedStyle(rail).columnGap) || 24;
    let base = 0, height = 0;
    items = nodes.map(slot => {
      const view = views.get(slot.dataset.cardId!)!;
      const item: Item = { id: slot.dataset.cardId!, slot, view, base, width: slot.getBoundingClientRect().width,
        style: view.element.getAttribute('style'), slotStyle: slot.getAttribute('style'), painted: false };
      base += item.width + gap;height = Math.max(height, slot.getBoundingClientRect().height);return item;
    });
    // At the untouched initial pose the previous card and its shadow must be
    // completely outside the crop. This small lead-in is removed only when the
    // seam is offscreen on both sides; all subsequent gaps stay at the usual 24px.
    const initialLead = Math.max(0, padding + guard - gap + 2);
    leadIn = saved?.program && savedIDs === ids ? saved.leadIn ?? (saved.cycled ? 0 : initialLead) : initialLead;
    period = base + leadIn;
    stage = element('div', 'ar-track-stage');
    stage.style.setProperty('--ar-track-gap', `${gap}px`);stage.style.height = `${height}px`;
    stage.style.perspectiveOrigin = `${width / 2 - padding}px ${height / 2}px`;
    stage.append(...nodes);rail.append(stage);rail.dataset.trackMode = 'program';rail.scrollLeft = 0;
    const anchor = items.find(item => item.id === seed.anchorId) ?? items[0]!;
    phase = ((anchor.base + seed.offsetRatio * anchor.width) % period + period) % period;
    savedIDs = ids;saved = undefined;cursor = '';bend = restoreBend;
    paint();return true;
  }
  function paint() {
    if (!stage) return;
    const edge = -padding;
    for (const item of items) {
      const raw = item.base - phase;
      const circulation = Math.ceil((edge - item.width - guard - raw) / period);
      const x = raw + circulation * period;
      const visible = x + item.width + guard > edge && x - guard < width - padding;
      item.slot.style.transform = `translate3d(${x - item.base}px,0,0)`;
      item.slot.dataset.trackVisible = String(visible);
      const focused = item.view.element.contains(document.activeElement);
      item.view.element.inert = !visible && !focused;
      if (!visible && !item.painted) continue;
      const u = clamp((padding + x + item.width / 2 - width / 2) / (width / 2), -1, 1);
      const curve = clamp((Math.abs(u) - .3) / .7, 0, 1);
      item.view.element.style.setProperty('--ar-card-y', `${6 * curve * curve * bend}px`);
      item.view.element.style.setProperty('--ar-card-z', `${-28 * curve * curve * bend}px`);
      item.view.setPose({ pitch: 0, yaw: -Math.sign(u) * 6 * curve * bend, roll: 0 });
      item.painted = visible;
    }
    // The reference is the first resting card centre, not an ever-moving DOM order.
    const reference = items[0]!.width / 2;
    const primary = items.reduce((best, item) => {
      const circular = ((item.base - phase + period / 2) % period + period) % period - period / 2;
      const score = Math.abs(circular + item.width / 2 - reference);
      return score < best.score ? { id: item.id, score } : best;
    }, { id: items[0]!.id, score: Infinity });
    if (cursor !== primary.id) { cursor = primary.id;options.cursor(cursor, position()); }
    root.dataset.trackOffset = phase.toFixed(4);root.dataset.trackDistance = distance.toFixed(4);
    root.dataset.trackCycles = String(cycles);root.dataset.trackPeriod = String(period);root.dataset.trackBaseSpeed = String(speed);
    root.dataset.trackDirection = String(direction);root.dataset.trackLeadIn = String(leadIn);
  }
  function advance(delta: number) {
    distance += delta;
    // Small integration steps also catch the narrow safe seam window in a
    // five-card category at the highest allowed speed, without extra paint/RAF.
    const steps = Math.max(1, Math.ceil(Math.abs(delta) / 8));
    for (let i = 0; i < steps; i++) {
      phase += delta / steps;
      if (phase < 0 || phase >= period) {
        const n = Math.floor(phase / period);cycles += n;phase = ((phase % period) + period) % period;cycled = true;
      }
      if (leadIn && phase > Math.max(...items.map(item => item.width)) + padding + guard + 1 && phase < period - leadIn - (width - padding + rightGuard + 1)) {
        period -= leadIn;leadIn = 0;
      }
    }
  }
  function schedule() {
    if (frame !== undefined || disposed) return;
    frame = requestAnimationFrame(tick);root.dataset.trackFramePending = 'true';
  }
  function canContinueWheel() {
    return !disposed && !document.hidden && !departureHeld && !readingHeld && rail.isConnected &&
      !rail.closest('[hidden],[inert],[aria-hidden="true"]') && (!stage || (context.active && supported()));
  }
  function finishWheel() {
    wheel.clear();
    nativeWheel = undefined;
    root.dataset.trackWheelActive = 'false';
    if (stage && preferred()) {
      publish('running', 'automatic');
      schedule();
    } else {
      clearMotion();
      publish('paused', 'manual');
      if (preferred()) reconcile();
    }
  }
  function tick() {
    frame = undefined;root.dataset.trackFramePending = 'false';
    if (disposed || state !== 'running') { clearMotion();return; }
    const manual = wheel.active;
    if (manual ? !canContinueWheel() : !stage || !context.active || !supported() || readingHeld || document.hidden) {
      clearMotion();
      reconcile();
      return;
    }
    const now = performance.now();
    if (!last) last = now;
    const dt = clamp((now - last) / 1000, 0, manual ? .05 : .25);last = now;
    const ramp = clamp((now - startAt) / 300, 0, 1), eased = ramp * ramp * (3 - 2 * ramp);
    const base = stage && preferred() ? direction * speed * eased : 0;
    const input = wheel.target(now, base, velocity);targetSpeed = input.speed;
    velocity = input.settling ? targetSpeed : velocity + (targetSpeed - velocity) * (1 - Math.exp(-dt / cardWheelMotion.response));
    velocity = clamp(velocity, -cardWheelMotion.maxSpeed, cardWheelMotion.maxSpeed);
    if (!manual && Math.abs(velocity - base) < .25) velocity = base;

    let atEdge = false;
    let visibleSpeed = velocity;
    if (stage) {
      bend = Math.max(bend, eased);
      advance(velocity * dt);
      paint();
    } else if (nativeWheel) {
      // Keep subpixel input even when the browser rounds scrollLeft on write.
      const { x, limit } = nativeWheel;
      nativeWheel.x = nativeDestination(x, limit, velocity * dt, true);
      rail.scrollLeft = nativeWheel.x;
      atEdge = velocity > 0 && nativeWheel.x === limit || velocity < 0 && nativeWheel.x === 0;
      if (atEdge) showEdge(velocity > 0 ? 1 : -1);
      visibleSpeed = dt > 0 ? (nativeWheel.x - x) / dt : 0;
    }
    root.dataset.trackSpeed = visibleSpeed.toFixed(4);root.dataset.trackTargetSpeed = targetSpeed.toFixed(4);
    root.dataset.trackWheelActive = String(input.active);
    if (manual && (!input.active || atEdge)) { finishWheel();return; }
    if (!manual && eased > 0 && root.dataset.trackReason !== 'automatic') publish('running', 'automatic');
    schedule();
  }

  function useWheel(amount: number, axis: WheelAxis, logicalLimit: number, now = performance.now()) {
    if (!canContinueWheel()) return;
    const limit = stage ? logicalLimit : Math.max(0, Math.min(logicalLimit, rail.scrollWidth - rail.clientWidth));
    if (limit <= 1) return;
    cancelResume();

    if (!stage) {
      // Native wheel positioning is independent of the last program snapshot.
      saved = undefined;
      savedIDs = '';
      rail.dataset.wheelDriven = 'true';
      const side = amount > 0 ? 1 : -1;
      if (side !== lastEdgeDirection || now - lastEdgeInput > 180) releaseEdgeGesture();
      lastEdgeDirection = side;
      lastEdgeInput = now;
    }
    if (axis === 'horizontal' || reduced.matches) {
      clearMotion();
      direction = amount > 0 ? 1 : -1;
      if (stage) { advance(amount);paint(); }
      else {
        const x = nativeDestination(rail.scrollLeft, limit, amount, !reduced.matches);
        rail.scrollLeft = x;
        if (x === (direction > 0 ? limit : 0)) showEdge(direction);
      }
      // The touchpad already sends its own momentum samples. Pause the base
      // briefly between those samples and resume from the last painted pose.
      if (stage && preferred()) {
        startAt = now + 120;
        publish('running', 'trackpad');
        schedule();
      } else publish('paused', 'wheel-direct');
      return;
    }

    if (!stage && (amount > 0 && rail.scrollLeft >= limit - .5 || amount < 0 && rail.scrollLeft <= .5)) {
      // Keep ownership at the end of the finite row without running an idle frame.
      rail.scrollLeft = amount > 0 ? limit : 0;
      showEdge(amount > 0 ? 1 : -1);
      finishWheel();
      return;
    }
    const starting = !wheel.active || velocity * amount < 0;
    const next = wheel.push(amount, now);
    if (next === undefined) return;
    direction = next;
    if (!stage) {
      nativeWheel ??= { x: rail.scrollLeft, limit };
      nativeWheel.limit = limit;
      if (starting) {
        // A bounded first increment makes the first native paint responsive
        // even when the scene leaves little frame time before the wheel tail.
        nativeWheel.x = nativeDestination(nativeWheel.x, limit, clamp(amount * .08, -12, 12), true);
        rail.scrollLeft = nativeWheel.x;
        if (nativeWheel.x === (next > 0 ? limit : 0)) {
          showEdge(next);
          finishWheel();
          return;
        }
      }
    }
    if (starting) {
      // A light initial response keeps the first wheel notch perceptible even
      // if the scene delays the first track frame until the settling phase.
      const base = stage && preferred() ? direction * speed : 0;
      velocity = wheel.target(now, base, velocity).speed * .25;
    }
    if (!last) last = now;
    startAt = now - 300;
    root.dataset.trackDirection = String(direction);
    root.dataset.trackWheelActive = 'true';
    publish('running', preferred() ? 'wheel-automatic' : 'wheel-manual');
    schedule();
  }
  function canToggle() { return !disposed && context.active && supported() && !fitsOneScreen(); }
  function reconcile() {
    if (disposed) return;
    if (departureHeld) { clearMotion();publish('paused', 'departure');return; }
    if (wheel.active) {
      if (canContinueWheel()) { schedule();return; }
      clearMotion();
    }
    if (!supported()) {
      if (stage) detach();else clearMotion();
      publish('static', 'reading-mode');return;
    }
    if (!context.active || !entryReady || !viewable() || document.hidden) {
      clearMotion();publish(!entryReady ? 'waiting' : 'suspended', 'not-visible');return;
    }
    if (fitsOneScreen()) { clearMotion();if (stage) detach(false);publish('static', 'fits-one-screen');return; }
    if (readingHeld) { clearMotion();publish('paused', 'reading');return; }
    if (!preferred()) {
      cancelResume();
      if (saved?.program && !stage) bind();
      stop();
      publish('paused', 'manual');
      return;
    }
    const wait = resumeAt - performance.now();
    if (wait > 0) {
      stop();
      if (resumeTimer === undefined) resumeTimer = window.setTimeout(() => { resumeTimer = undefined;reconcile(); }, wait);
      publish('paused', 'reading-break');
      return;
    }
    if (!bind()) { publish('static', 'no-cards');return; }
    if (state !== 'running' || frame === undefined) {
      const pauseAlreadyShown = !entranceHandoffUsed && entryReason === 'completed' && root.dataset.entrancePauseComplete === 'true';
      const firstWait = !entranceHandoffUsed && !pauseAlreadyShown && !resumeAt ? 500 : 0;
      cancelResume();
      startAt = performance.now() + firstWait;entranceHandoffUsed = true;
      last = 0;publish('running', firstWait ? 'automatic-delay' : 'automatic');schedule();
    }
  }
  const abort = { signal: events.signal };
  const visibility = new IntersectionObserver(reconcile, { threshold: [0,.25,.5,.75,1] });visibility.observe(rail);visibility.observe(controls);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { clearMotion();releaseEdgeGesture();publish('paused', 'page-hidden'); }
    else { delayResume();reconcile(); }
  }, abort);
  window.addEventListener('resize', () => {
    if (disposed) return;
    if (stage) detach();else { clearMotion();releaseEdgeGesture(); }
    if (resizeTimer !== undefined) clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => { resizeTimer = undefined;reconcile(); }, 300);
  }, abort);
  window.addEventListener('scroll', () => { if (context.active && entryReady) reconcile(); }, { ...abort, passive: true });
  const modeChanged = () => {
    if (!fine.matches || reduced.matches) {
      detach();
      if (!fine.matches) delete rail.dataset.wheelDriven;
    }
    reconcile();
  };
  fine.addEventListener('change', modeChanged, abort);reduced.addEventListener('change', modeChanged, abort);
  root.dataset.trackState = state;root.dataset.trackMode = 'native';root.dataset.trackFramePending = 'false';root.dataset.trackEnabled = 'false';
  return {
    get active() { return !!stage; },
    get enabled() { return preferred(); },
    get available() { return canToggle(); },
    get userPaused() { return decided && !intent; },
    get activity(): CardTrackActivity {
      if (state !== 'running') return 'still';
      if (wheel.active || root.dataset.trackReason === 'trackpad') return 'manual';
      return root.dataset.trackReason === 'automatic' ? 'automatic' : 'still';
    },
    setTouchInput(next: boolean) {
      if (disposed || next === touchInput) return;
      touchInput = next;
      if (next) {
        detach(false);
        saved = undefined;savedIDs = '';
        delete rail.dataset.wheelDriven;
      } else delayResume();
      reconcile();
    },
    suspendForDeparture(held: boolean) {
      departureHeld = held;root.dataset.trackDepartureHeld = String(held);
      if (held) { clearMotion();releaseEdgeGesture();publish('paused', 'departure'); }
      else { signature = '';delayResume(); }
    },
    holdReading(held: boolean) {
      if (disposed || held === readingHeld) return;
      readingHeld = held;
      if (held) { clearMotion();publish('paused', 'reading'); }
      else { delayResume();reconcile(); }
    },
    capture,
    position,
    present(next: CardTrackContext, ready: boolean, reason: string) {
      const key = JSON.stringify([next,ready,reason]);if (key === signature) return;
      if (context.active && !next.active && wheel.active) clearMotion();
      if (context.automatic && !next.automatic) {
        detach();
        if (saved) saved = { ...saved, program: false };
      }
      signature = key;context = next;entryReady = ready;entryReason = reason;reconcile();
    },
    refresh: reconcile,
    pause() { intent = false;decided = true;clearMotion();releaseEdgeGesture();publish('paused', 'user-pause'); },
    wheel: useWheel,
    cancelWheel() {
      releaseEdgeGesture();
      if (!wheel.active) return;
      clearMotion();
      publish('paused', 'wheel-cancelled');
      reconcile();
    },
    releaseWheel() { releaseEdgeGesture();wheel.release(performance.now()); },
    play() {
      if (!canToggle()) return;
      decided = true;intent = true;delayResume();reconcile();
    },
    step(direction: -1 | 1, fromId = cursor) {
      if (!stage || !items.length) return undefined;
      clearMotion();
      const current = Math.max(0, items.findIndex(item => item.id === fromId)), next = items[(current + direction + items.length) % items.length]!;
      if (current + direction < 0 || current + direction >= items.length) cycled = true;
      phase = next.base;bend = 1;paint();publish('paused', 'step');return next.id;
    },
    focus(id: string) {
      if (!stage) return;
      const item = items.find(item => item.id === id);if (!item) return;
      const rect = item.view.element.getBoundingClientRect(), bounds = rail.getBoundingClientRect();
      if (rect.left < bounds.left + 12 || rect.right > bounds.right - 12) { phase = item.base;bend = 1;paint(); }
    },
    native(reason: string) {
      detach(false);saved = undefined;savedIDs = '';
      publish('paused', reason);
    },
    clear(remember = false) {
      if (disposed) return;
      detach(remember);
      delete rail.dataset.wheelDriven;
      signature = '';
      if (!remember) { saved = undefined;savedIDs = '';phase = 0;cycled = false; }
      publish('paused', 'content-changed');
    },
    restore(snapshot: CardTrackSnapshot, ids?: readonly string[]) { detach(false);direction = snapshot.direction === -1 ? -1 : 1;saved = structuredClone(snapshot);intent = snapshot.enabled;decided = snapshot.decided;cycled = snapshot.cycled;savedIDs = (ids ?? slots().map(slot => slot.dataset.cardId!)).join(',');signature = ''; },
    dispose() {
      if (disposed) return;detach(false);disposed = true;stop();visibility.disconnect();events.abort();
      if (resizeTimer !== undefined) clearTimeout(resizeTimer);publish('disposed', 'disposed');
    },
  };
}
