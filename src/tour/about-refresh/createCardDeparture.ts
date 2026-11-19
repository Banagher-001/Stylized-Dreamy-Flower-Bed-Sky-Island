import { clamp } from './dom';
import { restingFlightPose } from './createToolCard';
import type { ToolCardFlightPose, ToolCardView } from './createToolCard';
import type { CardDepartureContext, ToolBrowserSnapshot } from './types';

type Phase = 'idle' | 'exiting' | 'departed' | 'returning' | 'disposed';
interface Flight {
  id: string; view: ToolCardView; end: ToolCardFlightPose;
  pose: ToolCardFlightPose; from: ToolCardFlightPose; delay: number;
}
const boundary = { armStart: .32, armEnd: .78, readStart: .30, readEnd: .80,
  returnStart: .34, returnEnd: .76, visibleStart: .20, visibleEnd: .96,
  quickStart: .24, quickEnd: .90 } as const;
const timing = { flight: 420, stagger: 45, quickFlight: 200, quickStagger: 20,
  return: 300, redirect: 360, shortcut: 220 } as const;
const smooth = (n: number) => { const u = clamp(n,0,1);return u*u*(3-2*u); };
const blend = (a: ToolCardFlightPose, b: ToolCardFlightPose, t: number): ToolCardFlightPose => ({
  x: a.x+(b.x-a.x)*t, y: a.y+(b.y-a.y)*t, z: a.z+(b.z-a.z)*t,
  pitch: a.pitch+(b.pitch-a.pitch)*t, yaw: a.yaw+(b.yaw-a.yaw)*t, roll: a.roll+(b.roll-a.roll)*t,
});

/** A finite lease of the existing perspective chain. No copied cards, reparenting,
 * scroll interception, route writes or environment-clock dependency. */
export function createCardDeparture(options: {
  root: HTMLElement; rail: HTMLElement; views: ReadonlyMap<string,ToolCardView>;
  ready(): boolean; capture(): ToolBrowserSnapshot; freeze(): void; release(returned: boolean): void;
  changed?(): void;
}) {
  const {root,rail,views} = options;
  const events = new AbortController(), abort = {signal:events.signal};
  const fine = matchMedia('(hover:hover) and (pointer:fine)'), reduced = matchMedia('(prefers-reduced-motion:reduce)');
  let phase: Phase = 'idle', armed = false, flights: Flight[] = [];
  let frame: number | undefined;
  let started = 0, duration = 0, layout = '', generation = 0, exits = 0, returns = 0, redirects = 0;
  let flightTime: number = timing.flight;
  let direction: -1 | 1 = 1;
  let fromCurrent = false, quick = false, pressed = false, pointerPaused = false, pressedAt = 0;
  let lastPointer: {x:number;y:number} | undefined;
  const inert = new Map<HTMLElement,boolean>();
  const owns = () => phase === 'exiting' || phase === 'departed' || phase === 'returning';
  function publish(next: Phase, reason: string) {
    phase = next;root.dataset.departure = next;root.dataset.departureOwned = String(owns());
    root.dataset.departureReason = reason;root.dataset.departureFramePending = String(frame !== undefined);
    root.dataset.departurePlays = String(exits);root.dataset.departureReturns = String(returns);
    root.dataset.departureRedirects = String(redirects);
    options.changed?.();
  }
  function stop() {
    generation++;if (frame !== undefined) cancelAnimationFrame(frame);frame = undefined;root.dataset.departureFramePending = 'false';
    pressed = false;pointerPaused = false;root.dataset.departurePressed = 'false';root.dataset.departurePointerPaused = 'false';
    lastPointer = undefined;
  }
  function schedule() {
    if (frame !== undefined || pressed || pointerPaused || phase === 'disposed') return;
    const token = generation;
    frame = requestAnimationFrame(() => { frame = undefined;root.dataset.departureFramePending = 'false';if(token === generation) tick(performance.now()); });
    root.dataset.departureFramePending = 'true';
  }
  function layoutKey() {
    const box = rail.getBoundingClientRect(), host = root.closest<HTMLElement>('.about-refresh');
    return [innerWidth,innerHeight,box.width.toFixed(2),box.height.toFixed(2),getComputedStyle(root).fontSize,host?.dataset.layout,host?.dataset.largeText].join('|');
  }
  function hasWindow() {
    return rail.getBoundingClientRect().width >= 700 && !rail.hidden && !root.closest<HTMLElement>('.ar-screen')?.hidden;
  }
  function restoreInert() { for(const [node,value] of inert) node.inert = value; }
  function cancel(reason = 'interaction') {
    if (reason === 'navigation') {
      armed = false;
      if (!owns()) root.dataset.departureReason = reason;
    }
    if (!owns()) return;
    stop();for(const flight of flights) flight.view.setFlight();restoreInert();inert.clear();flights = [];armed = false;
    root.dataset.departureProgress = '0';publish('idle',reason);options.release(false);
  }
  function park(reason: string) {
    stop();for(const flight of flights) { flight.pose = {...flight.end};flight.view.setFlight(flight.pose); }
    for(const node of inert.keys()) node.inert = true;
    root.dataset.departureProgress = '1';publish('departed',reason);
  }
  function aim(bounds: DOMRect) {
    for (const flight of flights) {
      const side = flight.end.yaw < 0 ? -1 : 1;
      const goal = side < 0 ? bounds.left-36 : bounds.right+36;
      const edge = () => { const box = flight.view.measure().bounds;return side < 0 ? box.right : box.left; };
      flight.view.setFlight(flight.end);
      for (let pass=0;pass<3;pass++) {
        const previous = edge();flight.end.x += 100;flight.view.setFlight(flight.end);
        const slope = (edge()-previous)/100;
        if (!Number.isFinite(slope) || Math.abs(slope)<.1) throw new Error('Unprojectable departure');
        flight.end.x += (goal-edge())/slope;flight.view.setFlight(flight.end);
      }
      if (Math.abs(edge()-goal)>1) throw new Error('Departure outside projection budget');
      flight.view.setFlight(flight.pose);
    }
    root.dataset.departureEndpoints = JSON.stringify(flights.map(flight => ({ id: flight.id, ...flight.end })));
  }
  function start(next: Phase, reason: string, milliseconds: number) {
    started = performance.now();duration = milliseconds;
    root.dataset.departureDuration = String(duration);
    root.dataset.departureStartedAt = String(started);
    publish(next, reason);
    schedule();
  }
  function begin(outward: -1 | 1, rapid: boolean) {
    const window = rail.getBoundingClientRect();
    const visible = [...views].filter(([,view]) => {
      if (!rail.contains(view.element) || view.element.inert) return false;
      const f = view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect();
      return f.width > 0 && f.right > window.left+1 && f.left < window.right-1 && f.bottom > window.top && f.top < window.bottom;
    }).map(([id,view]) => ({id,view,box:view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect()}))
      .sort((a,b) => Math.abs(a.box.x+a.box.width/2-window.x-window.width/2)-Math.abs(b.box.x+b.box.width/2-window.x-window.width/2))
      .slice(0,5).sort((a,b) => a.box.x-b.box.x);
    if (!visible.length) { armed = false;return; }
    direction = outward;quick = rapid;fromCurrent = false;
    flightTime = quick ? timing.quickFlight : timing.flight;
    const stagger = quick ? timing.quickStagger : timing.stagger;
    const before = visible.map(item => item.view.measure());
    root.dataset.departureSnapshot = JSON.stringify(options.capture());
    options.freeze();
    for(const view of views.values()) if(rail.contains(view.element)) { inert.set(view.element,view.element.inert);view.element.inert = true; }
    const focused = document.activeElement;
    if(focused instanceof HTMLElement && rail.contains(focused)) {
      const target = [...document.querySelectorAll<HTMLElement>('[data-reading-toggle]')]
        .find(node => !node.closest('[hidden],[inert]') && !!node.getClientRects().length);
      if(target) target.focus({preventScroll:true});else focused.blur();
    }
    flights = visible.map(({id,view,box},rank) => {
      const side = box.x+box.width/2 < window.x+window.width/2 ? -1 : 1;
      return {id,view,delay:rank*stagger,pose:{...restingFlightPose},from:{...restingFlightPose},end:{
        x:0,y:-direction*(38+(rank%2)*8),z:-(220+(rank%3)*55),
        pitch:direction*(rank%2 ? -14 : 14),yaw:side*(rank === Math.floor(visible.length/2) ? 112 : rank%2 ? 98 : 78),roll:side*(7+(rank%2)*3),
      }};
    });
    exits++;armed = false;publish('exiting',quick ? 'rapid-outward' : 'reading-boundary');
    root.dataset.departureIds = flights.map(f => f.id).join(',');root.dataset.departureDirection = String(direction);
    try {
      // The zero flight layer preserves every face and the reading width exactly.
      const error = Math.max(...flights.flatMap((flight,i) => flight.view.measure().faces.flatMap((face,j) =>
        (['left','top','right','bottom'] as const).map(axis => Math.abs(face[axis]-before[i]!.faces[j]![axis])))));
      root.dataset.departureHandoffError = String(error);
      if(error>1) throw new Error('Departure handoff moved the faces');
      aim(window);
    } catch { cancel('geometry-fallback');return; }
    layout = layoutKey();
    start('exiting',quick ? 'rapid-outward' : 'reading-boundary',flightTime+(flights.length-1)*stagger);
  }
  function recover() {
    if (layoutKey() !== layout) { cancel('layout-changed');return; }
    stop();returns++;for(const flight of flights) flight.from = {...flight.pose};restoreInert();
    start('returning','returned-to-reading',timing.return);
  }
  function redirect(outward: -1 | 1, rapid: boolean) {
    stop();for(const flight of flights) { flight.from = {...flight.pose};flight.delay = 0; }
    for(const node of inert.keys()) node.inert = true;
    if (outward !== direction) {
      direction = outward;
      for (const flight of flights) { flight.end.y *= -1;flight.end.pitch *= -1; }
      try { aim(rail.getBoundingClientRect()); }
      catch { cancel('geometry-fallback');return; }
      root.dataset.departureDirection = String(direction);
    }
    fromCurrent = true;quick = rapid;redirects++;
    start('exiting','reversed-outward',quick ? timing.shortcut : timing.redirect);
  }
  function shortenOutward() {
    const remaining = duration - (performance.now() - started);
    if (quick || remaining <= timing.shortcut) return;
    stop();
    for (const flight of flights) flight.from = { ...flight.pose };
    quick = true;fromCurrent = true;
    start('exiting','rapid-outward',timing.shortcut);
  }
  function tick(now: number) {
    if(phase !== 'exiting' && phase !== 'returning') return;
    if(document.hidden || layoutKey() !== layout || !root.isConnected) { cancel('layout-or-visibility');return; }
    const elapsed = now-started;
    if(elapsed>2500) { if(phase === 'exiting') park('time-fallback');else cancel('time-fallback');return; }
    for(const flight of flights) {
      if(phase === 'returning') flight.pose = blend(flight.from,restingFlightPose,smooth(elapsed/duration));
      else if(fromCurrent) flight.pose = blend(flight.from,flight.end,smooth(elapsed/duration));
      else {
        const u = clamp((elapsed-flight.delay)/flightTime,0,1), travel = smooth((u-.12)/.88), turn = smooth(u/.62);
        flight.pose = {x:flight.end.x*travel,y:flight.end.y*travel-14*Math.sin(Math.PI*u),z:flight.end.z*smooth(u),pitch:flight.end.pitch*turn,yaw:flight.end.yaw*turn,roll:flight.end.roll*turn};
      }
      flight.view.setFlight(flight.pose);
    }
    root.dataset.departureProgress = String(phase === 'returning' ? 1-clamp(elapsed/duration,0,1) : clamp(elapsed/duration,0,1));
    if(elapsed>=duration) {
      if(phase === 'exiting') park('completed');
      else {
        stop();for(const flight of flights) flight.view.setFlight();restoreInert();inert.clear();flights = [];
        root.dataset.departureProgress = '0';publish('idle','returned');options.release(true);
      }
    } else schedule();
  }
  // Native click must land before an interruption restores the card's home pose.
  function pausePointer() {
    if(pressed || pointerPaused) return;
    if(frame !== undefined) cancelAnimationFrame(frame);frame = undefined;root.dataset.departureFramePending = 'false';
    pointerPaused = true;pressedAt = performance.now();root.dataset.departurePointerPaused = 'true';
    options.changed?.();
  }
  function resumePointer() {
    if(!pointerPaused || pressed || phase !== 'returning') return;
    started += performance.now()-pressedAt;pointerPaused = false;root.dataset.departurePointerPaused = 'false';schedule();
    options.changed?.();
  }
  root.addEventListener('pointermove',event => {
    if(phase !== 'returning' || event.pointerType !== 'mouse' || pressed) return;
    if (!event.movementX && !event.movementY) return;
    const moved = !lastPointer || Math.hypot(event.clientX-lastPointer.x,event.clientY-lastPointer.y)>=1.5;
    lastPointer = {x:event.clientX,y:event.clientY};
    if(!moved) return;
    // An intentional approach settles the row before the user aims at a button.
    if((event.target as Element).closest('.ar-tool-card')) pausePointer();else resumePointer();
  },{...abort,capture:true});
  root.addEventListener('pointerleave',() => { lastPointer = undefined;resumePointer(); },abort);
  window.addEventListener('resize',() => cancel('resize'),abort);
  window.addEventListener('pointercancel',() => { if(pressed || pointerPaused) cancel('pointer-cancel'); },abort);
  window.addEventListener('blur',() => { if(pressed || pointerPaused) cancel('lost-pointer'); },abort);
  document.addEventListener('visibilitychange',() => { if(document.hidden) cancel('page-hidden'); },abort);
  document.fonts.addEventListener('loadingdone',() => cancel('fonts'),abort);
  fine.addEventListener('change',() => cancel('pointer-mode'),abort);reduced.addEventListener('change',() => cancel('motion-mode'),abort);
  publish('idle','initial');
  return {
    get owns() { return owns(); },get pointerHeld() { return pressed; },
    cancel,
    holdPress(held: boolean) {
      if (phase !== 'returning' || pressed === held) return;
      if (held) pausePointer();
      pressed = held;root.dataset.departurePressed = String(held);
      if (!held) resumePointer();
    },
    present(next: CardDepartureContext) {
      if(phase === 'disposed') return;
      if(!next.enabled || !fine.matches || reduced.matches || document.hidden) { cancel('static-reading');armed = false;return; }
      const p = next.progress;
      const outward = p > boundary.readEnd ? 1 : p < boundary.readStart ? -1 : 0;
      const rapid = p > boundary.quickEnd || p < boundary.quickStart;
      if(owns()) {
        if(!next.active) { if(phase !== 'departed') park('left-station');return; }
        if (phase === 'returning') {
          if (outward) redirect(outward, rapid);
          return;
        }
        const reachedReadZone = direction > 0 ? p <= boundary.returnEnd : p >= boundary.returnStart;
        // A user who stops just inside the readable band should see their deck
        // even if they never slide far enough to cross the inner return line.
        if (!outward && (reachedReadZone || next.readable) && hasWindow()) recover();
        else if (phase === 'exiting' && outward && rapid) shortenOutward();
        return;
      }
      if(next.active && next.readable && p>=boundary.armStart && p<=boundary.armEnd && hasWindow() && options.ready()) armed = true;
      if(!armed) return;
      if(!next.active || p>boundary.visibleEnd || p<boundary.visibleStart) { armed = false;root.dataset.departureReason = 'fast-skip';return; }
      if (outward && hasWindow()) begin(outward,rapid);
    },
    dispose() { if(phase === 'disposed') return;cancel('disposed');stop();events.abort();armed = false;publish('disposed','disposed'); },
  };
}
