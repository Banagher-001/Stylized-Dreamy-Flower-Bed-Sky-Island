import { clamp } from './dom';
import { restingFlightPose } from './createToolCard';
import type { ToolCardFlightPose, ToolCardView } from './createToolCard';
import type { CardDepartureContext, ToolBrowserSnapshot } from './types';

type Phase = 'idle' | 'exiting' | 'departed' | 'returning' | 'disposed';
interface Flight {
  id: string; view: ToolCardView; end: ToolCardFlightPose;
  pose: ToolCardFlightPose; from: ToolCardFlightPose; delay: number;
}
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
  let frame: number | undefined, releaseTimer: number | undefined;
  let started = 0, duration = 0, layout = '', generation = 0, exits = 0, returns = 0;
  let redirected = false, pressed = false, pointerPaused = false, pressedAt = 0;
  let lastPointer: {x:number;y:number} | undefined;
  const inert = new Map<HTMLElement,boolean>();
  const owns = () => phase === 'exiting' || phase === 'departed' || phase === 'returning';
  function publish(next: Phase, reason: string) {
    phase = next;root.dataset.departure = next;root.dataset.departureOwned = String(owns());
    root.dataset.departureReason = reason;root.dataset.departureFramePending = String(frame !== undefined);
    root.dataset.departurePlays = String(exits);root.dataset.departureReturns = String(returns);
    options.changed?.();
  }
  function stop() {
    generation++;if (frame !== undefined) cancelAnimationFrame(frame);frame = undefined;root.dataset.departureFramePending = 'false';
    if (releaseTimer !== undefined) clearTimeout(releaseTimer);releaseTimer = undefined;
    pressed = false;pointerPaused = false;root.dataset.departurePressed = 'false';root.dataset.departurePointerPaused = 'false';
  }
  function schedule() {
    if (frame !== undefined || pressed || pointerPaused || phase === 'disposed') return;
    const token = generation;
    frame = requestAnimationFrame(now => { frame = undefined;root.dataset.departureFramePending = 'false';if(token === generation) tick(now); });
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
    if (!owns()) return;
    stop();for(const flight of flights) flight.view.setFlight();restoreInert();inert.clear();flights = [];armed = false;
    root.dataset.departureProgress = '0';publish('idle',reason);options.release(false);
  }
  function park(reason: string) {
    stop();for(const flight of flights) { flight.pose = {...flight.end};flight.view.setFlight(flight.pose); }
    for(const node of inert.keys()) node.inert = true;
    root.dataset.departureProgress = '1';publish('departed',reason);
  }
  function begin(direction: -1 | 1) {
    const window = rail.getBoundingClientRect();
    const visible = [...views].filter(([,view]) => {
      if (!rail.contains(view.element) || view.element.inert) return false;
      const f = view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect();
      return f.width > 0 && f.right > window.left+1 && f.left < window.right-1 && f.bottom > window.top && f.top < window.bottom;
    }).map(([id,view]) => ({id,view,box:view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect()}))
      .sort((a,b) => Math.abs(a.box.x+a.box.width/2-window.x-window.width/2)-Math.abs(b.box.x+b.box.width/2-window.x-window.width/2))
      .slice(0,5).sort((a,b) => a.box.x-b.box.x);
    if (!visible.length) { armed = false;return; }
    const before = visible.map(item => item.view.measure());
    root.dataset.departureSnapshot = JSON.stringify(options.capture());
    options.freeze();
    for(const view of views.values()) if(rail.contains(view.element)) { inert.set(view.element,view.element.inert);view.element.inert = true; }
    const focused = document.activeElement;
    if(focused instanceof HTMLElement && rail.contains(focused)) {
      const target = document.querySelector<HTMLElement>('[data-reading-toggle]');
      if(target) target.focus({preventScroll:true});else focused.blur();
    }
    flights = visible.map(({id,view,box},rank) => {
      const side = box.x+box.width/2 < window.x+window.width/2 ? -1 : 1;
      return {id,view,delay:rank*45,pose:{...restingFlightPose},from:{...restingFlightPose},end:{
        x:0,y:-direction*(38+(rank%2)*8),z:-(220+(rank%3)*55),
        pitch:direction*(rank%2 ? -14 : 14),yaw:side*(rank === Math.floor(visible.length/2) ? 112 : rank%2 ? 98 : 78),roll:side*(7+(rank%2)*3),
      }};
    });
    exits++;armed = false;redirected = false;publish('exiting','reading-boundary');
    root.dataset.departureIds = flights.map(f => f.id).join(',');root.dataset.departureDirection = String(direction);
    try {
      // The zero flight layer preserves every face and the reading width exactly.
      const error = Math.max(...flights.flatMap((flight,i) => flight.view.measure().faces.flatMap((face,j) =>
        (['left','top','right','bottom'] as const).map(axis => Math.abs(face[axis]-before[i]!.faces[j]![axis])))));
      root.dataset.departureHandoffError = String(error);
      for(const flight of flights) {
        const side = flight.end.yaw < 0 ? -1 : 1, goal = side < 0 ? window.left-36 : window.right+36;
        const edge = () => { const b = flight.view.measure().bounds;return side < 0 ? b.right : b.left; };
        flight.view.setFlight(flight.end);
        for(let pass=0;pass<3;pass++) {
          const previous = edge();flight.end.x += 100;flight.view.setFlight(flight.end);
          const slope = (edge()-previous)/100;
          if(!Number.isFinite(slope) || Math.abs(slope)<.1) throw new Error('Unprojectable departure');
          flight.end.x += (goal-edge())/slope;flight.view.setFlight(flight.end);
        }
        if(Math.abs(edge()-goal)>1) throw new Error('Departure outside projection budget');
        flight.view.setFlight();
      }
      if(error>1) throw new Error('Departure handoff moved the faces');
    } catch { cancel('geometry-fallback');return; }
    started = performance.now();duration = 420+(flights.length-1)*45;layout = layoutKey();
    root.dataset.departureDuration = String(duration);root.dataset.departureStartedAt = String(started);
    root.dataset.departureEndpoints = JSON.stringify(flights.map(f => ({id:f.id,...f.end})));
    schedule();
  }
  function recover() {
    stop();returns++;for(const flight of flights) flight.from = {...flight.pose};restoreInert();
    started = performance.now();duration = 300;publish('returning','returned-to-reading');schedule();
  }
  function redirect() {
    stop();for(const flight of flights) { flight.from = {...flight.pose};flight.delay = 0; }
    for(const node of inert.keys()) node.inert = true;
    redirected = true;exits++;started = performance.now();duration = 360;publish('exiting','reversed-outward');schedule();
  }
  function tick(now: number) {
    if(phase !== 'exiting' && phase !== 'returning') return;
    if(document.hidden || layoutKey() !== layout || !root.isConnected) { cancel('layout-or-visibility');return; }
    const elapsed = now-started;
    if(elapsed>2500) { if(phase === 'exiting') park('time-fallback');else cancel('time-fallback');return; }
    for(const flight of flights) {
      if(phase === 'returning') flight.pose = blend(flight.from,restingFlightPose,smooth(elapsed/duration));
      else if(redirected) flight.pose = blend(flight.from,flight.end,smooth(elapsed/duration));
      else {
        const u = clamp((elapsed-flight.delay)/420,0,1), travel = smooth((u-.12)/.88), turn = smooth(u/.62);
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
    const moved = !lastPointer || Math.hypot(event.clientX-lastPointer.x,event.clientY-lastPointer.y)>=1.5;
    lastPointer = {x:event.clientX,y:event.clientY};
    if(!moved) return;
    // An intentional approach settles the row before the user aims at a button.
    if((event.target as Element).closest('.ar-tool-card')) pausePointer();else resumePointer();
  },{...abort,capture:true});
  root.addEventListener('pointerleave',() => { lastPointer = undefined;resumePointer(); },abort);
  root.addEventListener('pointerdown',event => {
    if(phase !== 'returning') return;
    if((event.target as Element).closest('.ar-tool-card')) {
      pausePointer();pressed = true;root.dataset.departurePressed = 'true';
    } else cancel('pointer');
  },{...abort,capture:true});
  window.addEventListener('pointerup',() => {
    if(!pressed) return;
    releaseTimer = window.setTimeout(() => { releaseTimer = undefined;if(pressed && phase === 'returning') { pressed = false;root.dataset.departurePressed = 'false';resumePointer(); } },0);
  },abort);
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
    present(next: CardDepartureContext) {
      if(phase === 'disposed') return;
      if(!next.enabled || !fine.matches || reduced.matches || document.hidden) { cancel('static-reading');armed = false;return; }
      if(owns()) {
        if(!next.active) { if(phase !== 'departed') park('left-station');return; }
        if(next.progress>=.3 && next.progress<=.8 && hasWindow()) { if(phase !== 'returning') recover(); }
        else if(phase === 'returning') redirect();
        return;
      }
      if(next.active && next.readable && next.progress>=.32 && next.progress<=.78 && hasWindow() && options.ready()) armed = true;
      if(!armed) return;
      if(!next.active || next.progress>.96 || next.progress<.2) { armed = false;root.dataset.departureReason = 'fast-skip';return; }
      if((next.progress>.8 || next.progress<.3) && hasWindow()) begin(next.progress>.8 ? 1 : -1);
    },
    dispose() { if(phase === 'disposed') return;cancel('disposed');stop();events.abort();armed = false;publish('disposed','disposed'); },
  };
}
