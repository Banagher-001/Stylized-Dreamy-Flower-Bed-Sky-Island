import { initialEntryIds } from './content';
import { clamp, element } from './dom';
import type { ToolCardView } from './createToolCard';
import type { CardEntranceContext } from './types';
import './cardEntrance.css';

type Phase = 'waiting' | 'preparing' | 'playing' | 'ready' | 'cancelled' | 'disposed';
interface Flight {
  view: ToolCardView; slot: HTMLElement; width: number; height: number;
  x: number; y: number; z: number; pitch: number; yaw: number; roll: number;
  delay: number; duration: number; originalStyle: string | null; originalSlotStyle: string | null;
}
const choreography = [
  { side: -1, vertical: -1, z: -280, pitch: -18, yaw: 62, roll: -11, delay: 0, duration: 980 },
  { side: 1, vertical: -1, z: -420, pitch: 16, yaw: -118, roll: 12, delay: 110, duration: 1040 },
  { side: -1, vertical: 1, z: -240, pitch: 22, yaw: 82, roll: -9, delay: 220, duration: 1080 },
  { side: 1, vertical: 1, z: -360, pitch: -16, yaw: -142, roll: 10, delay: 330, duration: 1120 },
] as const;
const rest = { pitch: 0, yaw: 0, roll: 0 };

/** One cancellable entrance per document instance. No clock while waiting or ready. */
export function createCardEntrance(options: {
  root: HTMLElement; rail: HTMLElement; foreground: HTMLElement;
  views: ReadonlyMap<string, ToolCardView>; changed(): void;
}) {
  const { root, rail, foreground, views } = options;
  const events = new AbortController();
  let phase: Phase = 'waiting', handled = false, generation = 0;
  let frame: number | undefined, started = 0, requested = 0, readyFrames = 0;
  let plays = 0, flights: Flight[] = [], context: CardEntranceContext = { active: false, enabled: false, revealed: false };
  let stage: HTMLElement | undefined, stageBox: DOMRect | undefined;
  let frozenLayout = '';

  function publish(next: Phase, reason = '') {
    phase = next;root.dataset.entrance = next;
    root.dataset.entranceReady = String(next === 'ready' || next === 'cancelled');
    root.dataset.entranceReason = reason;root.dataset.entrancePlays = String(plays);
    root.dataset.entranceFramePending = String(frame !== undefined);
    options.changed();
  }
  function stopFrame() { if (frame !== undefined) cancelAnimationFrame(frame);frame = undefined; }
  function restore() {
    for (const flight of flights) {
      flight.view.setPose(rest);
      const card = flight.view.element;
      for (const axis of ['x', 'y', 'z']) card.style.removeProperty(`--ar-card-${axis}`);
      if (flight.originalStyle === null) card.removeAttribute('style');else card.setAttribute('style', flight.originalStyle);
      card.inert = false;card.removeAttribute('aria-hidden');
      if (flight.originalSlotStyle === null) flight.slot.removeAttribute('style');else flight.slot.setAttribute('style', flight.originalSlotStyle);
      flight.slot.append(card);delete flight.slot.dataset.entryCard;
    }
    flights = [];
    for (const slot of rail.querySelectorAll<HTMLElement>('[data-entry-card]')) {
      delete slot.dataset.entryCard;
      const card = slot.querySelector<HTMLElement>('.ar-stone-card');
      if (card) { card.inert = false;card.removeAttribute('aria-hidden'); }
    }
    stage?.remove();stage = undefined;stageBox = undefined;
    foreground.removeAttribute('style');delete foreground.dataset.flightWindow;
  }
  function finish(reason: string, cancelled = false) {
    if (phase === 'disposed') return;
    generation++;stopFrame();restore();handled = true;
    root.dataset.entranceFinishedAt = String(performance.now());
    publish(cancelled ? 'cancelled' : 'ready', reason);
  }
  function cancel(reason = 'interaction') {
    if (phase === 'preparing' || phase === 'playing') finish(reason, true);
  }
  function schedule() {
    if (frame !== undefined) return;
    const ownGeneration = generation;
    frame = requestAnimationFrame(now => {
      frame = undefined;root.dataset.entranceFramePending = 'false';
      if (ownGeneration !== generation || phase === 'disposed') return;
      tick(now);
    });
    root.dataset.entranceFramePending = 'true';
  }
  function layoutKey() {
    const r = rail.getBoundingClientRect(), b = root.getBoundingClientRect();
    return [innerWidth, innerHeight, r.x, r.y, r.width, r.height, b.x, b.y, getComputedStyle(root).fontSize].map(v => typeof v === 'number' ? v.toFixed(2) : v).join('|');
  }
  function prepare() {
    for (const id of initialEntryIds) {
      const slot = rail.querySelector<HTMLElement>(`[data-card-id="${id}"]`);
      const card = views.get(id)?.element;
      if (!slot || !card) { finish('restored-content');return; }
      slot.dataset.entryCard = 'true';card.inert = true;card.setAttribute('aria-hidden', 'true');
    }
    publish('preparing');
  }
  function resourcesReady() {
    return initialEntryIds.every(id => {
      const view = views.get(id);
      return view?.element.dataset.geometryReady === 'true' && [...view.element.querySelectorAll('img')].every(image => image.complete);
    }) && document.fonts.status !== 'loading';
  }
  function begin(now: number) {
    const railBox = rail.getBoundingClientRect(), rootBox = root.getBoundingClientRect();
    foreground.dataset.flightWindow = 'true';
    Object.assign(foreground.style, { left: `${railBox.left - rootBox.left}px`, top: `${railBox.top - rootBox.top}px`, width: `${railBox.width}px`, height: `${railBox.height}px` });
    stage = element('div', 'ar-flight-stage');foreground.append(stage);stageBox = stage.getBoundingClientRect();
    const targets = initialEntryIds.map(id => {
      const view = views.get(id)!, slot = rail.querySelector<HTMLElement>(`[data-card-id="${id}"]`)!;
      return { view, slot, rect: view.element.getBoundingClientRect() };
    });
    for (const [i, { view, slot, rect }] of targets.entries()) {
      const config = choreography[i]!, card = view.element;
      const flight: Flight = { view, slot, width: rect.width, height: rect.height, x: 0, y: config.vertical * 115, ...config, originalStyle: card.getAttribute('style'), originalSlotStyle: slot.getAttribute('style') };
      flights.push(flight);
      slot.style.height = `${rect.height}px`;
      Object.assign(card.style, { left: `${rect.left - stageBox.left}px`, top: `${rect.top - stageBox.top}px`, width: `${rect.width}px`, height: `${rect.height}px` });
      stage.append(card);view.setPose(config);
      // Adjust projected faces, not the untransformed article, completely offscreen.
      flight.x = 0;
      paint(flight, 0);
      const edge = () => {
        const faces = view.measure().faces;
        return config.side < 0 ? Math.max(...faces.map(r => r.right)) : Math.min(...faces.map(r => r.left));
      };
      const goal = config.side < 0 ? -42 : innerWidth + 42;
      for (let n = 0; n < 2; n++) {
        const before = edge();
        flight.x += 100;paint(flight, 0);
        const slope = (edge() - before) / 100;
        if (!Number.isFinite(slope) || Math.abs(slope) < .1) throw new Error('Unprojectable entrance');
        flight.x += (goal - edge()) / slope;paint(flight, 0);
      }
    }
    started = now;handled = true;plays++;root.dataset.entranceStartedAt = String(now);
    root.dataset.entranceDuration = '1450';root.dataset.entranceIds = initialEntryIds.join(',');
    frozenLayout = layoutKey();publish('playing');schedule();
  }
  function paint(flight: Flight, t: number) {
    // Fast spatial approach, slower orientation: the back/edge can be seen in-frame.
    const travel = 1 - Math.pow(1 - t, 3);
    const turnTime = flight.yaw < -90 ? clamp((t - .26) / .74, 0, 1) : t;
    const turn = turnTime * turnTime * (3 - 2 * turnTime);
    const arc = Math.sin(Math.PI * t);
    const settle = t > .82 ? Math.sin((t - .82) / .18 * Math.PI) * (1 - t) / .18 : 0;
    const card = flight.view.element;
    card.style.setProperty('--ar-card-x', `${flight.x * (1 - travel)}px`);
    card.style.setProperty('--ar-card-y', `${flight.y * (1 - travel) - 24 * arc}px`);
    card.style.setProperty('--ar-card-z', `${flight.z * (1 - travel) + 12 * arc}px`);
    flight.view.setPose({ pitch: flight.pitch * (1 - turn) + settle * 1.4, yaw: flight.yaw * (1 - turn), roll: flight.roll * (1 - turn) - settle * 1.2 });
  }
  function tick(now: number) {
    if (!context.active || !context.enabled || document.hidden) { cancel('presentation-changed');return; }
    if (phase === 'preparing') {
      if (!context.revealed) return;
      if (!resourcesReady()) {
        readyFrames = 0;
        if (now - requested > 1200) finish('resource-fallback');else schedule();
      } else if (++readyFrames < 2) schedule();
      else { try { begin(now); } catch { finish('geometry-fallback'); } }
      return;
    }
    if (phase !== 'playing') return;
    if (layoutKey() !== frozenLayout) { cancel('layout-changed');return; }
    const elapsed = now - started;
    if (elapsed > 2500) { finish('time-fallback');return; }
    for (const flight of flights) paint(flight, clamp((elapsed - flight.delay) / flight.duration, 0, 1));
    root.dataset.entranceProgress = String(clamp(elapsed / 1450, 0, 1));
    if (elapsed >= 1450) finish('completed');else schedule();
  }
  const abortEvents = { signal: events.signal };
  window.addEventListener('resize', () => cancel('resize'), abortEvents);
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancel('page-hidden'); }, abortEvents);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  reduced.addEventListener('change', () => { if (reduced.matches) cancel('reduced-motion'); }, abortEvents);
  root.dataset.entrance = phase;root.dataset.entranceReady = 'false';root.dataset.entrancePlays = '0';root.dataset.entranceFramePending = 'false';
  return {
    get ready() { return phase === 'ready' || phase === 'cancelled'; },
    cancel,
    present(next: CardEntranceContext) {
      if (phase === 'disposed') return;
      context = next;
      if (!next.active) {
        if (phase === 'playing') cancel('left-station');
        else if (phase === 'preparing') { generation++;stopFrame();restore();readyFrames = 0;requested = 0;publish('waiting'); }
        return;
      }
      if (handled) return;
      if (!next.enabled || reduced.matches) { finish('static-reading');return; }
      if (phase === 'waiting') prepare();
      if (phase === 'preparing' && next.revealed) {
        if (!requested) requested = performance.now();
        schedule();
      }
    },
    dispose() {
      if (phase === 'disposed') return;
      generation++;stopFrame();restore();events.abort();publish('disposed');
    },
  };
}
