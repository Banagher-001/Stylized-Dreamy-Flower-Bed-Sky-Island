import { initialEntryIds } from './content';
import { clamp, element } from './dom';
import type { ToolCardView } from './createToolCard';
import type { CardEntranceContext } from './types';
import './cardEntrance.css';

type Phase = 'waiting' | 'preparing' | 'playing' | 'ready' | 'cancelled' | 'disposed';
interface Pose { x: number; y: number; z: number; pitch: number; yaw: number; roll: number; }
interface Flight {
  view: ToolCardView; slot: HTMLElement; x: number; y: number; z: number;
  pitch: number; yaw: number; roll: number; delay: number; duration: number;
  originalStyle: string | null; originalSlotStyle: string | null; pose: Pose;
}
const timing = { anticipation: 150, settled: 2000, total: 2350, hold: 350, resourceWait: 1200, stable: 120, visible: 100, interrupt: 140 } as const;
const choreography = [
  { side: -1, vertical: -1, z: -480, pitch: -14, yaw: 65, roll: -8, delay: 150, duration: 1050 },
  { side: 1, vertical: -1, z: -650, pitch: 12, yaw: -118, roll: 9, delay: 300, duration: 1100 },
  { side: -1, vertical: 1, z: -420, pitch: 16, yaw: 75, roll: -7, delay: 450, duration: 1150 },
  { side: 1, vertical: 1, z: -580, pitch: -12, yaw: -125, roll: 8, delay: 600, duration: 1150 },
] as const;
const rest: Pose = { x: 0, y: 0, z: 0, pitch: 0, yaw: 0, roll: 0 };
const smooth = (value: number) => { const t = clamp(value, 0, 1);return t * t * (3 - 2 * t); };

/** Four original cards, one temporary visual stage; input ownership stays separate. */
export function createCardEntrance(options: {
  root: HTMLElement; rail: HTMLElement; foreground: HTMLElement;
  views: ReadonlyMap<string, ToolCardView>; changed(): void;
}) {
  const { root, rail, foreground, views } = options;
  const events = new AbortController();
  let phase: Phase = 'waiting', handled = false, generation = 0;
  let frame: number | undefined, holdTimer: number | undefined;
  let started = 0, requested = 0, stableSince = 0, candidateLayout = '', visibleSince = 0;
  let plays = 0, attempts = 0, flights: Flight[] = [];
  let context: CardEntranceContext = { active: false, enabled: false, revealed: false };
  let stage: HTMLElement | undefined, stageBox: DOMRect | undefined, railBox: DOMRect | undefined;
  let foregroundStyle: string | null = null, frozenLayout = '', safeTop = 0, safeBottom = 0;
  let clipLeft = 0, clipRight = 0;
  let interruption: { start: number; reason: string; poses: Pose[]; left: number; right: number } | undefined;
  const prepared = new Map<HTMLElement, { slot: HTMLElement; inert: boolean; aria: string | null }>();

  function publish(next: Phase, reason = '') {
    phase = next;root.dataset.entrance = next;root.dataset.entranceReady = String(next === 'ready' || next === 'cancelled');
    root.dataset.entranceReason = reason;root.dataset.entrancePlays = String(plays);
    root.dataset.entranceFramePending = String(frame !== undefined);options.changed();
  }
  function stopWork() {
    if (frame !== undefined) cancelAnimationFrame(frame);frame = undefined;
    if (holdTimer !== undefined) clearTimeout(holdTimer);holdTimer = undefined;
    root.dataset.entranceFramePending = 'false';root.dataset.entranceHoldPending = 'false';
  }
  function restore() {
    for (const flight of flights) {
      flight.view.setPose(rest);
      if (flight.originalStyle === null) flight.view.element.removeAttribute('style');else flight.view.element.setAttribute('style', flight.originalStyle);
      if (flight.originalSlotStyle === null) flight.slot.removeAttribute('style');else flight.slot.setAttribute('style', flight.originalSlotStyle);
      flight.slot.append(flight.view.element);
    }
    for (const [card, saved] of prepared) {
      card.inert = saved.inert;if (saved.aria === null) card.removeAttribute('aria-hidden');else card.setAttribute('aria-hidden', saved.aria);
      delete saved.slot.dataset.entryCard;
    }
    prepared.clear();flights = [];interruption = undefined;
    if (stage) {
      stage.remove();
      if (foregroundStyle === null) foreground.removeAttribute('style');else foreground.setAttribute('style', foregroundStyle);
      delete foreground.dataset.flightWindow;
    }
    stage = undefined;stageBox = undefined;railBox = undefined;
  }
  function finish(reason: string, cancelled = false) {
    if (phase === 'disposed') return;
    const before = reason === 'completed' ? flights.map(f => ({ node: f.view.element.querySelector<HTMLElement>('.ar-card-front')!, rect: f.view.element.querySelector<HTMLElement>('.ar-card-front')!.getBoundingClientRect() })) : [];
    generation++;stopWork();restore();handled = true;
    if (before.length) root.dataset.entranceHandoffError = String(Math.max(...before.flatMap(({ node, rect }) => {
      const after = node.getBoundingClientRect();return [Math.abs(after.left-rect.left),Math.abs(after.top-rect.top),Math.abs(after.width-rect.width),Math.abs(after.height-rect.height)];
    })));
    root.dataset.entrancePauseComplete = String(reason === 'completed');
    if (reason === 'completed') root.dataset.entranceProgress = '1';
    root.dataset.entranceFinishedAt = String(performance.now());
    root.dataset.entranceObservedDuration = String(started ? performance.now() - started : 0);
    root.dataset.entranceSubphase = 'idle';events.abort();layoutObserver.disconnect();
    publish(cancelled ? 'cancelled' : 'ready', reason);
  }
  function resetWaiting(reason: string) {
    generation++;stopWork();restore();requested = stableSince = started = visibleSince = 0;candidateLayout = '';
    root.dataset.entranceSeen = 'false';root.dataset.entranceProgress = '0';root.dataset.entranceSubphase = 'waiting';
    publish('waiting', reason);
  }
  function cancel(reason = 'interaction') {
    if (phase === 'preparing' || phase === 'playing') finish(reason, true);
  }
  function schedule() {
    if (frame !== undefined || holdTimer !== undefined) return;
    const token = generation;
    frame = requestAnimationFrame(now => {
      frame = undefined;root.dataset.entranceFramePending = 'false';
      if (token !== generation || phase === 'disposed') return;tick(now);
    });
    root.dataset.entranceFramePending = 'true';
  }
  function layoutKey() {
    const a = rail.getBoundingClientRect(), b = root.getBoundingClientRect();
    return [innerWidth,innerHeight,a.x,a.y,a.width,a.height,b.x,b.y,getComputedStyle(root).fontSize].map(v => typeof v === 'number' ? v.toFixed(2) : v).join('|');
  }
  function prepare() {
    for (const id of initialEntryIds) {
      const slot = rail.querySelector<HTMLElement>(`[data-card-id="${id}"]`), card = views.get(id)?.element;
      if (!slot || !card) { finish('restored-content');return; }
      prepared.set(card, { slot, inert: card.inert, aria: card.getAttribute('aria-hidden') });
      slot.dataset.entryCard = 'true';card.inert = true;card.setAttribute('aria-hidden', 'true');
    }
    root.dataset.entranceSubphase = 'preparing';publish('preparing');
  }
  function resourcesReady() {
    return initialEntryIds.every(id => {
      const card = views.get(id)?.element;
      return card?.dataset.geometryReady === 'true' && [...card.querySelectorAll('img')].every(img => img.complete && img.naturalWidth > 0);
    }) && document.fonts.status !== 'loading';
  }
  function sufficientlyVisible() {
    const r = rail.getBoundingClientRect();
    const w = Math.max(0,Math.min(innerWidth,r.right)-Math.max(0,r.left));
    const h = Math.max(0,Math.min(innerHeight,r.bottom)-Math.max(0,r.top));
    return r.width > 0 && r.height > 0 && w*h/(r.width*r.height) >= .6;
  }
  function windowAt(left: number, right: number) {
    clipLeft = left;clipRight = right;
    foreground.style.clipPath = `inset(0px ${Math.max(0,innerWidth-right)}px 0px ${Math.max(0,left)}px)`;
    root.dataset.entranceWindow = JSON.stringify({left,right,top:safeTop,bottom:safeBottom});
  }
  function pose(flight: Flight, value: Pose, glow = 0) {
    flight.pose = value;const card = flight.view.element;
    card.style.setProperty('--ar-card-x', `${value.x}px`);card.style.setProperty('--ar-card-y', `${value.y}px`);card.style.setProperty('--ar-card-z', `${value.z}px`);
    card.style.setProperty('--ar-entry-glow',String(glow));flight.view.setPose(value);
  }
  function paint(flight: Flight, elapsed: number) {
    const local = elapsed-flight.delay, t = clamp(local/flight.duration,0,1), travel = smooth(t);
    const turn = smooth((t-.12)/.88), arc = Math.sin(Math.PI*t);
    const settling = clamp((local-flight.duration)/250,0,1);
    const bounce = local >= flight.duration ? Math.sin(Math.PI*settling)*(1-settling) : 0;
    pose(flight,{ x:flight.x*(1-travel),y:flight.y*(1-travel)-20*arc-6*bounce,z:flight.z*(1-travel)+8*arc,
      pitch:flight.pitch*(1-turn)+1.2*bounce,yaw:flight.yaw*(1-turn),roll:flight.roll*(1-turn)-1.0*bounce },local>=flight.duration ? Math.sin(Math.PI*settling)*.65 : 0);
  }
  function begin(now: number) {
    railBox = rail.getBoundingClientRect();
    const controls = root.querySelector<HTMLElement>('.ar-tool-controls')!.getBoundingClientRect();
    const filters = root.querySelector<HTMLElement>('.ar-filter-bar')!.getBoundingClientRect();
    safeTop = Math.max(0,filters.bottom);safeBottom = Math.min(innerHeight,controls.top);
    if (safeBottom-safeTop < 100) { finish('space-fallback');return; }
    foregroundStyle = foreground.getAttribute('style');foreground.dataset.flightWindow = 'true';
    Object.assign(foreground.style,{position:'fixed',left:'0px',top:`${safeTop}px`,width:`${innerWidth}px`,height:`${safeBottom-safeTop}px`});
    stage = element('div','ar-flight-stage');foreground.append(stage);stageBox = stage.getBoundingClientRect();
    stage.style.perspectiveOrigin = `${railBox.left+railBox.width/2-stageBox.left}px ${railBox.top+railBox.height/2-stageBox.top}px`;
    const targets = initialEntryIds.map(id => ({ view:views.get(id)!,slot:rail.querySelector<HTMLElement>(`[data-card-id="${id}"]`)!,rect:views.get(id)!.element.getBoundingClientRect() }));
    for (const [i,{ view,slot,rect }] of targets.entries()) {
      const config=choreography[i]!,card=view.element;
      const flight:Flight={view,slot,...config,x:0,y:config.vertical*Math.min(54,railBox.height*.14),originalStyle:card.getAttribute('style'),originalSlotStyle:slot.getAttribute('style'),pose:{...rest}};
      flights.push(flight);slot.style.height=`${rect.height}px`;
      const sigil=element('span','ar-entry-sigil','✧');sigil.setAttribute('aria-hidden','true');
      Object.assign(sigil.style,{left:`${rect.left+rect.width/2-stageBox.left}px`,top:`${rect.top+rect.height/2-stageBox.top}px`});stage.append(sigil);
      Object.assign(card.style,{left:`${rect.left-stageBox.left}px`,top:`${rect.top-stageBox.top}px`,width:`${rect.width}px`,height:`${rect.height}px`});stage.append(card);
      paint(flight,0);
      const edge=()=>{const faces=view.measure().faces;return config.side<0?Math.max(...faces.map(r=>r.right)):Math.min(...faces.map(r=>r.left));};
      const goal=config.side<0?-42:innerWidth+42;
      for(let n=0;n<2;n++) {
        const before=edge();flight.x+=100;paint(flight,0);const slope=(edge()-before)/100;
        if(!Number.isFinite(slope)||Math.abs(slope)<.1)throw new Error('Unprojectable entrance');
        flight.x+=(goal-edge())/slope;paint(flight,0);
      }
    }
    started=now;attempts++;visibleSince=0;windowAt(0,innerWidth);frozenLayout=layoutKey();
    root.dataset.entranceStartedAt=String(now);root.dataset.entranceDuration=String(timing.total);root.dataset.entranceIds=initialEntryIds.join(',');
    root.dataset.entranceAttempts=String(attempts);root.dataset.entranceSubphase='anticipation';publish('playing');schedule();
  }
  function observeVisible(now:number) {
    if(handled)return;
    const visible=flights.some(f=>{
      const face=f.view.element.querySelector<HTMLElement>(Math.abs(f.pose.yaw)>90?'.ar-card-back':'.ar-card-front')!.getBoundingClientRect();
      return Math.max(0,Math.min(clipRight,face.right)-Math.max(clipLeft,face.left))*Math.max(0,Math.min(safeBottom,face.bottom)-Math.max(safeTop,face.top))>=2500;
    });
    if(!visible){visibleSince=0;return;}
    visibleSince ||= now;
    if(now-visibleSince>=timing.visible){handled=true;plays++;root.dataset.entrancePlays=String(plays);root.dataset.entranceSeen='true';root.dataset.entranceVisibleAt=String(visibleSince);}
  }
  function shorten(reason:string) {
    if(phase!=='playing'||interruption)return;
    generation++;stopWork();interruption={start:performance.now(),reason,poses:flights.map(f=>({...f.pose})),left:clipLeft,right:clipRight};
    root.dataset.entranceSubphase='interrupted';schedule();
  }
  function tick(now:number) {
    if(!context.active||!context.enabled||document.hidden){if(!handled&& !document.hidden)resetWaiting('left-before-visible');else cancel('presentation-changed');return;}
    if(phase==='preparing') {
      if(!context.revealed){requested=stableSince=0;return;}
      if(now-requested>timing.resourceWait){finish('resource-fallback');return;}
      const key=layoutKey();
      if(!resourcesReady()||!sufficientlyVisible()){stableSince=0;schedule();return;}
      if(key!==candidateLayout){candidateLayout=key;stableSince=now;}
      if(!stableSince)stableSince=now;
      if(now-stableSince<timing.stable){schedule();return;}
      try{begin(now);}catch{finish('geometry-fallback');}return;
    }
    if(phase!=='playing')return;
    if(layoutKey()!==frozenLayout){cancel('layout-changed');return;}
    if(interruption&&railBox) {
      const t=smooth((performance.now()-interruption.start)/timing.interrupt);
      flights.forEach((f,i)=>{const p=interruption!.poses[i]!;pose(f,{x:p.x*(1-t),y:p.y*(1-t),z:p.z*(1-t),pitch:p.pitch*(1-t),yaw:p.yaw*(1-t),roll:p.roll*(1-t)});});
      windowAt(interruption.left+(railBox.left-interruption.left)*t,interruption.right+(railBox.right-interruption.right)*t);
      if(t>=1){finish(interruption.reason,true);return;}schedule();return;
    }
    const elapsed=now-started;
    if(elapsed>3600){finish('time-fallback');return;}
    for(const flight of flights)paint(flight,elapsed);
    const crop=smooth((elapsed-1750)/250);windowAt(railBox!.left*crop,innerWidth+(railBox!.right-innerWidth)*crop);
    stage!.style.setProperty('--ar-sigil-opacity',String(Math.max(0,Math.sin(Math.PI*clamp(elapsed/450,0,1)))*.75));
    observeVisible(now);
    root.dataset.entranceProgress=String(clamp(elapsed/timing.total,0,1));
    root.dataset.entrancePose=JSON.stringify(flights.map(f=>({id:f.view.element.dataset.toolId,...f.pose})));
    root.dataset.entranceSubphase=elapsed<timing.anticipation?'anticipation':elapsed<1750?'flying':elapsed<timing.settled?'settling':'reading';
    if(elapsed>=timing.settled) {
      root.dataset.entranceHoldPending='true';
      holdTimer=window.setTimeout(()=>{holdTimer=undefined;root.dataset.entranceHoldPending='false';if(document.hidden){cancel('page-hidden');return;}if(layoutKey()!==frozenLayout){cancel('layout-changed');return;}finish('completed');},Math.max(0,timing.total-elapsed));
      return;
    }
    schedule();
  }
  const abort={signal:events.signal};
  window.addEventListener('resize',()=>cancel('resize'),abort);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel('page-hidden');},abort);
  const reduced=matchMedia('(prefers-reduced-motion:reduce)');reduced.addEventListener('change',()=>{if(reduced.matches)cancel('reduced-motion');},abort);
  const layoutObserver=new ResizeObserver(()=>{if(phase==='playing'&&layoutKey()!==frozenLayout)cancel('layout-changed');});layoutObserver.observe(root);layoutObserver.observe(rail);
  root.dataset.entrance=phase;root.dataset.entranceReady='false';root.dataset.entrancePlays='0';root.dataset.entranceAttempts='0';root.dataset.entranceFramePending='false';root.dataset.entranceHoldPending='false';root.dataset.entrancePauseComplete='false';root.dataset.entranceSeen='false';
  return {
    get ready(){return phase==='ready'||phase==='cancelled';},cancel,shorten,
    present(next:CardEntranceContext) {
      if(phase==='disposed')return;context=next;
      if(!next.active){if(phase==='playing'||phase==='preparing'){if(!handled)resetWaiting('left-before-visible');else cancel('left-station');}return;}
      if(handled)return;
      if(!next.enabled||reduced.matches){finish('static-reading');return;}
      if(phase==='waiting')prepare();
      if(phase==='preparing'&&next.revealed){if(!requested)requested=performance.now();schedule();}
    },
    dispose(){if(phase==='disposed')return;generation++;stopWork();restore();events.abort();layoutObserver.disconnect();phase='disposed';root.dataset.entranceSubphase='idle';publish('disposed');},
  };
}
