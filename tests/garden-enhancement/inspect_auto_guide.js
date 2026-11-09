import { autoGuideStops, createAutoGuide, guideReadingSeconds, guideStartAt } from '../../src/tour/autoGuide';

const assert = (condition, message) => { if (!condition) throw Error(message); };
function fixture(h = 0) {
  let now = 0, id = 0, position = h, blocked = '', ready = true, text = '';
  const timers = new Map(), changes = [], writes = [], callbacks = [];
  const scheduler = { now: () => now, set(fn, delay) { const key = ++id;timers.set(key, { at: now + delay, fn });callbacks.push(fn);return key; }, clear(key) { timers.delete(key); } };
  const bridge = { h: () => position, blocked: () => blocked, write(value) { position = value;writes.push({ time: now, h: value }); },
    ready: () => ({ ready, text }), prepare() {}, wake() {}, changed(s) { changes.push({ time: now, ...s }); } };
  const guide = createAutoGuide(bridge, scheduler);
  return { guide, timers, changes, writes, callbacks,
    get now() { return now; }, get h() { return position; }, set h(value) { position = value; },
    set blocked(value) { blocked = value;guide.refresh(); }, set ready(value) { ready = value; }, set text(value) { text = value; },
    advance(ms) { now += ms;for (const [key, timer] of [...timers]) if (timer.at <= now) { timers.delete(key);timer.fn(); } },
    frame(ms = 1000 / 60) { this.advance(ms);guide.tick(now);guide.afterFrame(); },
  };
}

export function inspectAutoGuide() {
  const cases = [], record = (name, evidence) => cases.push({ name, passed: true, evidence });
  const minimums = { O:4, A1:10, A2:14, A3:14, B1:12, B2:10, B3:10, B4:8, C1:10, C2:12, C3:12, W:8, S99:6 };
  assert(autoGuideStops.map(s => s.id).join(',') === Object.keys(minimums).join(','), 'Full itinerary');
  const f = fixture();f.guide.refresh();assert(f.guide.snapshot.phase === 'manual' && !f.guide.active, 'Default off');f.guide.start();
  const visits = [];let frames = 0;
  while (f.guide.active && frames < 20000) {
    if (f.guide.snapshot.phase === 'reading') {
      const s = f.guide.snapshot;
      visits.push({ id:s.stop.id, h:f.h, time:f.now, seconds:s.seconds });
      assert(s.seconds >= minimums[s.stop.id] && s.deadline - s.readyAt >= minimums[s.stop.id] * 1000, 'Reading minimum');
      const wait = s.deadline - f.now;f.advance(wait - .01);assert(f.guide.snapshot.phase === 'reading', 'Early departure');f.advance(.02);
    } else f.frame();
    frames++;
  }
  assert(f.guide.snapshot.phase === 'finished' && Math.abs(f.h - 12.3) < 1e-8 && f.timers.size === 0, 'Finish once');
  assert(visits.map(s => s.id).join(',') === Object.keys(minimums).join(','), 'All thirteen nodes held');
  f.advance(3600000);assert(f.guide.snapshot.phase === 'finished', 'No automatic loop');
  record('full deterministic itinerary, real reading deadlines and terminal stop', { visits, simulatedSeconds:visits.at(-1).time / 1000 + 6, frames, noLoopAfterHour:true });
  const join = [];
  for (const h of [.2,.45,1.5,1.74,2,2.18,2.54,2.65,2.81,3.87,5.9,8.3,10.4,11.46,11.52,11.545,12.1]) {
    const next = guideStartAt(h);assert(next.h >= h - 1e-10, 'Join rewinds');join.push({ h, station:autoGuideStops[next.index].id, target:next.h });
  }
  assert(guideStartAt(2.65).h === 2.65 && autoGuideStops[guideStartAt(2.81).index].id === 'A3', 'Hold/leave join');
  record('mid-route and reverse-manual continuation moves only forwards from actual new position',join);
  const gate=fixture(2.54);gate.ready=false;gate.guide.start();for(let i=0;i<30;i++)gate.frame();
  assert(gate.guide.snapshot.phase==='arriving'&&gate.guide.snapshot.readyAt===null,'Unready content counted');
  gate.ready=true;gate.frame();assert(gate.guide.snapshot.phase==='arriving','Only one ready frame');gate.frame();assert(gate.guide.snapshot.phase==='reading','Second ready frame');
  assert(gate.guide.snapshot.deadline-gate.guide.snapshot.readyAt>=14000,'Preparation consumed reading');
  gate.guide.stop();assert(gate.timers.size===0,'Stop leaked deadline');record('readiness and two-frame gate; no reading time consumed during preparation',{readyAt:gate.guide.snapshot.readyAt});
  const slow=fixture(4.95);slow.ready=false;slow.guide.start();slow.advance(8001);assert(slow.guide.snapshot.phase==='paused'&&slow.timers.size===0,'Slow content never stops');record('finite8s content preparation deadline',{reason:slow.guide.snapshot.reason});
  const long=guideReadingSeconds(autoGuideStops.find(s=>s.id==='A1'),'字'.repeat(300)+' English words');assert(long>44,'Long article clipped');record('long visible text extends minimum',{seconds:long});
  const cancelled=fixture(2.54);cancelled.guide.start();cancelled.frame();cancelled.frame();const stale=cancelled.callbacks.at(-1);cancelled.guide.stop();cancelled.h=6.84;cancelled.guide.start();
  const before=cancelled.writes.length;stale();assert(cancelled.writes.length===before&&cancelled.guide.snapshot.stop.id==='B3','Old deadline revived');
  for(let i=0;i<20;i++){cancelled.guide.stop();cancelled.guide.start();cancelled.frame();cancelled.guide.stop();assert(cancelled.timers.size===0,'Repeated cancellation leak');}
  record('stale callback generation and twenty cancellation cycles',{staleCallbackIgnored:true,cycles:20});
  const identity=fixture();identity.blocked='作品查看中';assert(identity.guide.snapshot.phase==='manual','Never started identity lost');identity.blocked='';assert(identity.guide.snapshot.state==='manual','Blocked restored as paused');identity.guide.start();identity.blocked='隐藏';identity.blocked='';assert(identity.guide.snapshot.phase==='paused'&&!identity.guide.active,'Hidden auto-resumed');record('blocked identity and explicit-only resumption',{neverStarted:'manual',previouslyStarted:'paused'});
  const jump=fixture(.9);jump.guide.start();jump.frame();const start=jump.h;jump.frame(60000);assert(jump.h-start<.01,'Long frame caught up');jump.guide.stop();record('foreground stall cannot jump multiple route segments',{hAfterMinuteStall:jump.h});
  f.guide.start();assert(f.h===0&&f.guide.active,'Explicit replay');f.guide.stop();f.advance(3600000);assert(!f.guide.active,'Replay cannot interrupt');record('explicit restart reuses overview position and remains cancellable',{h:f.h});
  const dispose=fixture(2.54);dispose.guide.start();dispose.frame();dispose.frame();const old=dispose.callbacks.at(-1), notifications=dispose.changes.length;dispose.guide.dispose();dispose.guide.dispose();old();dispose.advance(1e6);assert(dispose.timers.size===0&&dispose.changes.length===notifications,'Dispose revive');record('idempotent dispose clears owned deadline and callbacks',{timers:0});
  return {passed:true,method:'deterministic controller-only injected scheduler/bridge; no fake real browser visibility or physical device claim; independent approved minima and all retained cases',cases};
}
