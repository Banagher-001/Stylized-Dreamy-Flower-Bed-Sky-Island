import { clamp, element } from './dom';
import type { ToolCardView } from './createToolCard';
import type { CardTrackContext, CardTrackSnapshot, TrackPosition } from './types';
import { cardWheelMotion, createWheelVelocity } from './cardWheelInput';
import type { TrackDirection } from './cardWheelInput';
import './cardTrack.css';

interface Item { id: string; slot: HTMLElement; view: ToolCardView; base: number; width: number; style: string | null; slotStyle: string | null; painted: boolean; }
type TrackState = 'waiting' | 'running' | 'paused' | 'suspended' | 'static' | 'disposed';
const speed = cardWheelMotion.baseSpeed;
const guard = 64;
const rightGuard = 40;
const rest = { pitch: 0, yaw: 0, roll: 0 };

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
  let cursor = '', stateSignature = '';
  let direction: TrackDirection = 1, velocity = 0, targetSpeed = 0, leadIn = 0;
  const wheel = createWheelVelocity();
  let readingHeld = false;
  let departureHeld = false;

  const slots = () => [...rail.querySelectorAll<HTMLElement>('.ar-tool-slot')];
  const supported = () => context.allowed && fine.matches && !reduced.matches;
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
  function clearMotion() {
    wheel.clear();velocity = 0;targetSpeed = 0;stop();
    root.dataset.trackSpeed = '0.0000';root.dataset.trackTargetSpeed = '0.0000';root.dataset.trackWheelActive = 'false';
  }
  function publish(next: TrackState, reason: string) {
    state = next;
    root.dataset.trackState = next;root.dataset.trackReason = reason;
    root.dataset.trackEnabled = String(decided ? intent : context.automatic);
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
      cycled: stage ? cycled : saved?.cycled ?? cycled, enabled: intent, decided,
      bend: stage ? bend : saved?.bend ?? bend, direction, leadIn: stage ? leadIn : saved?.leadIn ?? leadIn };
  }
  function detach(remember = true) {
    readingHeld = false;clearMotion();
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
  function tick(now: number) {
    frame = undefined;root.dataset.trackFramePending = 'false';
    if (disposed || state !== 'running') { clearMotion();return; }
    if (!supported() || document.hidden) { intent = false;decided = true;reconcile();return; }
    if (!context.active || readingHeld) { reconcile();return; }
    if (!last) last = now;
    const dt = Math.min((now - last) / 1000, .25);last = now;
    const ramp = clamp((now - startAt) / 300, 0, 1), eased = ramp * ramp * (3 - 2 * ramp);
    const base = intent ? direction * speed * eased : 0;
    const input = wheel.target(now, base);targetSpeed = input.speed;
    velocity += (targetSpeed - velocity) * (1 - Math.exp(-dt / cardWheelMotion.response));
    velocity = clamp(velocity, -cardWheelMotion.maxSpeed, cardWheelMotion.maxSpeed);
    if (!input.active && Math.abs(velocity - base) < cardWheelMotion.stopSpeed) velocity = base;
    bend = Math.max(bend, eased);
    advance(velocity * dt);paint();
    root.dataset.trackSpeed = velocity.toFixed(4);root.dataset.trackTargetSpeed = targetSpeed.toFixed(4);
    root.dataset.trackWheelActive = String(input.active);
    if (!intent && !input.active && velocity === 0) { stop();publish('paused', 'manual');return; }
    schedule();
  }
  function canWheel() { return !!stage && entryReady && canToggle() && viewable() && !document.hidden; }
  function canToggle() { return !disposed && context.active && supported() && !fitsOneScreen(); }
  function reconcile() {
    if (disposed) return;
    if (departureHeld) { clearMotion();publish('paused', 'departure');return; }
    if (!supported()) {
      if (stage) detach();
      publish('static', 'reading-mode');return;
    }
    if (!context.active || !entryReady || !viewable() || document.hidden) {
      clearMotion();publish(!entryReady ? 'waiting' : 'suspended', 'not-visible');return;
    }
    if (!decided) {
      decided = true;intent = context.automatic && entryReason === 'completed';
    }
    if (fitsOneScreen()) { clearMotion();if (stage) detach(false);publish('static', 'fits-one-screen');return; }
    if (saved?.program && !stage) bind();
    if (readingHeld) { clearMotion();publish('paused', 'reading');return; }
    if (!intent) { if (state !== 'running' || frame === undefined) { stop();publish('paused', 'manual'); } return; }
    if (!bind()) { publish('static', 'no-cards');return; }
    if (state !== 'running') { startAt = performance.now() + 500;last = 0;publish('running', 'automatic');schedule(); }
  }
  const abort = { signal: events.signal };
  const visibility = new IntersectionObserver(reconcile, { threshold: [0,.25,.5,.75,1] });visibility.observe(rail);visibility.observe(controls);
  document.addEventListener('visibilitychange', () => { if (document.hidden) { intent = false;decided = true;clearMotion();publish('paused', 'page-hidden'); } else reconcile(); }, abort);
  window.addEventListener('resize', () => {
    if (disposed) return;
    if (innerWidth < 1180) { intent = false;decided = true; }
    if (stage) detach();else clearMotion();
    if (resizeTimer !== undefined) clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => { resizeTimer = undefined;reconcile(); }, 300);
  }, abort);
  window.addEventListener('scroll', () => { if (context.active && entryReady) reconcile(); }, { ...abort, passive: true });
  const modeChanged = () => { if (!fine.matches || reduced.matches) { intent = false;decided = true;detach(); } reconcile(); };
  fine.addEventListener('change', modeChanged, abort);reduced.addEventListener('change', modeChanged, abort);
  root.dataset.trackState = state;root.dataset.trackMode = 'native';root.dataset.trackFramePending = 'false';root.dataset.trackEnabled = 'false';
  return {
    get active() { return !!stage; },
    get enabled() { return decided ? intent : context.automatic; },
    get available() { return canToggle(); },
    suspendForDeparture(held: boolean) {
      departureHeld = held;root.dataset.trackDepartureHeld = String(held);
      if (held) { clearMotion();publish('paused', 'departure'); }
      else signature = '';
    },
    holdReading(held: boolean) {
      if (disposed || held === readingHeld) return;
      readingHeld = held;
      if (held) { clearMotion();publish('paused', 'reading'); } else reconcile();
    },
    capture,
    position,
    present(next: CardTrackContext, ready: boolean, reason: string) {
      const key = JSON.stringify([next,ready,reason]);if (key === signature) return;
      if (next.active && !next.allowed) { intent = false;decided = true; }
      if (context.automatic && !next.automatic) {
        intent = false;decided = true;detach();
        if (saved) saved = { ...saved, enabled: false, program: false };
      }
      signature = key;context = next;entryReady = ready;entryReason = reason;reconcile();
    },
    refresh: reconcile,
    pause(reason = 'interaction') { intent = false;decided = true;clearMotion();publish('paused', reason); },
    wheel(delta: number, now = performance.now()) {
      if (!canWheel()) return false;
      const next = wheel.push(delta, now);
      if (next === undefined) return true;
      direction = next;startAt = now - 300;root.dataset.trackDirection = String(direction);
      publish('running', intent ? 'wheel-automatic' : 'wheel-manual');schedule();return true;
    },
    releaseWheel() { wheel.release(performance.now()); },
    get wheelAvailable() { return canWheel(); },
    play() { if (!canToggle() || !entryReady) return;decided = true;intent = true;reconcile(); },
    step(direction: -1 | 1, fromId = cursor) {
      if (!stage || !items.length) return undefined;
      intent = false;decided = true;clearMotion();
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
    native(reason: string) { intent = false;decided = true;detach(false);saved = undefined;savedIDs = '';publish('paused', reason); },
    clear(remember = false) { if (disposed) return;detach(remember);if (!remember) { saved = undefined;savedIDs = '';phase = 0;cycled = false; } publish('paused', 'content-changed'); },
    restore(snapshot: CardTrackSnapshot, ids?: readonly string[]) { detach(false);direction = snapshot.direction === -1 ? -1 : 1;saved = structuredClone(snapshot);intent = snapshot.enabled;decided = snapshot.decided;cycled = snapshot.cycled;savedIDs = (ids ?? slots().map(slot => slot.dataset.cardId!)).join(',');signature = ''; },
    dispose() {
      if (disposed) return;detach(false);disposed = true;stop();visibility.disconnect();events.abort();
      if (resizeTimer !== undefined) clearTimeout(resizeTimer);publish('disposed', 'disposed');
    },
  };
}
