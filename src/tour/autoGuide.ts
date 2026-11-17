import { readingStations } from './reading';
import { filmStations } from './filmReading';
import { experimentStations } from './experimentReading';
import { sampleTour, tourTotalH, waterHold } from './route';

export interface GuideStop { id: string; h: number; label: string; seconds: number; travel: number; }
/** Latest Step4 reading minima supersede Step1's historical timing suggestions. */
const timing: Record<string, [string, number, number]> = {
  A1: ['关于我 · 身份', 10, 8], A2: ['关于我 · 经历', 14, 4], A3: ['关于我 · 工具与方法', 14, 4],
  B1: ['AI影像 · 展映', 12, 7], B2: ['AI影像 · 切片', 10, 5], B3: ['AI影像 · 探索', 10, 4.5], B4: ['AI影像 · 余韵', 8, 4],
  C1: ['交互实验 · 想法', 10, 7], C2: ['交互实验 · 交互作品', 12, 4.5], C3: ['交互实验 · 继续', 12, 4],
};
export const autoGuideStops: readonly GuideStop[] = [
  { id: 'O', h: 0, label: '庭院全景', seconds: 4, travel: 0 },
  ...[...readingStations, ...filmStations, ...experimentStations].map(s => {
    const [label, seconds, travel] = timing[s.id]!;return { id: s.id, h: s.stop, label, seconds, travel };
  }),
  { id: 'W', h: waterHold.stop, label: '水潭与水球', seconds: 8, travel: 4 },
  { id: 'S99', h: tourTotalH, label: '庭院终章', seconds: 6, travel: 5 },
];
export function guideReadingSeconds(stop: GuideStop, text: string) {
  if (!/^[ABC]/.test(stop.id)) return stop.seconds;
  const han = text.match(/[\u3400-\u9fff]/g)?.length ?? 0;
  const words = text.match(/[A-Za-z][A-Za-z0-9_-]*/g)?.length ?? 0;
  return Math.max(stop.seconds, 2 + han / 7 + words / 2.75);
}
/** Join forwards only; a held, fully readable station never rewinds to its center. */
export function guideStartAt(h: number) {
  const frame = sampleTour(h), reading = frame.reading ?? frame.filmReading ?? frame.experimentReading;
  if (h <= .35) return { index: 0, h };
  if (reading && reading.phase !== 'leave') {
    const index = autoGuideStops.findIndex(s => s.id === reading.station.id);
    return { index, h: reading.phase === 'read' && frame.hold ? h : Math.max(h, autoGuideStops[index]!.h) };
  }
  if (h >= waterHold.start && h <= waterHold.stop) return { index: autoGuideStops.length - 2, h: waterHold.stop };
  if (h > waterHold.stop && h <= waterHold.end - .02) return { index: autoGuideStops.length - 2, h };
  const index = autoGuideStops.findIndex(s => s.h > h + .001);
  return { index: index < 0 ? autoGuideStops.length - 1 : index, h: index < 0 ? tourTotalH : autoGuideStops[index]!.h };
}

export type GuidePhase = 'manual' | 'moving' | 'arriving' | 'reading' | 'paused' | 'finished';
export interface GuideSnapshot {
  state: GuidePhase | 'blocked'; phase: GuidePhase; active: boolean; reason: string;
  stop: GuideStop; targetH: number; seconds: number; readyAt: number | null; deadline: number | null; generation: number;
}
export interface GuideBridge {
  h(): number;
  blocked(): string;
  write(h: number): void;
  ready(stop: GuideStop): { ready: boolean; text: string };
  prepare(stop: GuideStop): void;
  wake(): void;
  changed(snapshot: GuideSnapshot): void;
}
export interface GuideScheduler {
  now(): number; set(callback: () => void, delay: number): number; clear(id: number): void;
}
/** One cancellable deadline and the existing renderer's frames. No owned RAF,
 * scene, camera, environment clock, recurring interval, storage or global hook.
 */
export function createAutoGuide(bridge: GuideBridge, scheduler: GuideScheduler = {
  now: () => performance.now(), set: (fn, delay) => window.setTimeout(fn, delay), clear: id => clearTimeout(id),
}) {
  let phase: GuidePhase = 'manual', started = false, disposed = false, index = 0, generation = 0;
  let timer: number | undefined, lastFrame: number | null = null, readyFrames = 0;
  let from = 0, target = 0, duration = 0, elapsed = 0, seconds = 0, lastReason = '';
  let readyAt: number | null = null, deadline: number | null = null, signature = '';
  const active = () => phase === 'moving' || phase === 'arriving' || phase === 'reading';
  const needsFrames = () => phase === 'moving' || phase === 'arriving' && readyFrames > 0;
  function snapshot(): GuideSnapshot {
    const blocked = bridge.blocked();
    return { state: blocked ? 'blocked' : phase, phase, active: active(), reason: blocked || lastReason,
      stop: autoGuideStops[index]!, targetH: target, seconds, readyAt, deadline, generation };
  }
  function notify() {
    if (disposed) return;
    const s = snapshot(), key = JSON.stringify([s.state, s.phase, s.reason, s.stop.id, s.targetH, s.seconds, s.readyAt, s.deadline, s.generation, needsFrames()]);
    if (key === signature) return;signature = key;bridge.changed(s);
  }
  function clear() { if (timer !== undefined) scheduler.clear(timer);timer = undefined;lastFrame = null;readyFrames = 0;deadline = null; }
  function stop(reason = '导览已停止，可从当前位置继续。') {
    if (disposed) return;
    if (active()) { generation++;clear();phase = started ? 'paused' : 'manual';lastReason = reason; }
    notify();
  }
  function refresh() {
    if (disposed) return;
    if (bridge.blocked() && active()) { stop(bridge.blocked());return; }
    if (!active()) {
      if (bridge.h() >= tourTotalH - .001) phase = 'finished';
      else if (phase === 'finished') phase = started ? 'paused' : 'manual';
    }
    notify();
  }
  function arm(delay: number, callback: () => void) {
    if (timer !== undefined) scheduler.clear(timer);
    const token = generation;
    const scheduled = scheduler.set(() => {
      // An already queued, cancelled callback must not erase a newer handle.
      if (disposed || token !== generation || !active() || timer !== scheduled) return;
      timer = undefined;
      if (bridge.blocked()) { stop(bridge.blocked());return; }
      callback();
    }, delay);
    timer = scheduled;
  }
  function arrive() {
    clear();phase = 'arriving';readyAt = null;seconds = 0;
    arm(8000, () => stop('内容尚在准备，导览已暂停，可稍后继续。'));
    notify();bridge.wake();
  }
  function move(nextIndex: number, h = autoGuideStops[nextIndex]!.h) {
    clear();index = nextIndex;target = h;from = bridge.h();elapsed = 0;readyAt = null;seconds = 0;
    bridge.prepare(autoGuideStops[index]!);
    const previous = autoGuideStops[Math.max(0, index - 1)]!.h;
    const span = Math.max(.001, autoGuideStops[index]!.h - previous);
    duration = Math.max(.45, autoGuideStops[index]!.travel * Math.min(1, Math.abs(target - from) / span));
    if (Math.abs(target - from) < .001) { arrive();return; }
    phase = 'moving';notify();bridge.wake();
  }
  function start() {
    if (disposed || bridge.blocked()) { refresh();return; }
    const replay = phase === 'finished' || bridge.h() >= tourTotalH - .001;
    generation++;clear();started = true;lastReason = '';
    if (replay) {
      index = 0;target = 0;phase = 'arriving';
      // Reuse native overview navigation and the original camera convergence.
      bridge.write(0);arrive();
    } else { const next = guideStartAt(bridge.h());move(next.index, next.h); }
  }
  function tick(timestamp: number) {
    if (disposed || !active()) return;
    if (bridge.blocked()) { stop(bridge.blocked());return; }
    if (phase !== 'moving') return;
    elapsed += lastFrame === null ? 0 : Math.min(.05, Math.max(0, (timestamp - lastFrame) / 1000));lastFrame = timestamp;
    const u = Math.min(1, elapsed / duration), ease = u * u * u * (u * (u * 6 - 15) + 10);
    bridge.write(from + (target - from) * ease);
    // A synchronous native-scroll bridge may have relinquished control.
    if (!active() || phase !== 'moving') return;
    if (u >= 1) arrive();
  }
  function afterFrame() {
    if (disposed || phase !== 'arriving') return;
    if (bridge.blocked()) { stop(bridge.blocked());return; }
    const content = bridge.ready(autoGuideStops[index]!);
    if (!content.ready) { readyFrames = 0;notify();return; }
    // Two actual settled, fully readable frames precede the reading deadline.
    if (++readyFrames < 2) { notify();bridge.wake();return; }
    clear();phase = 'reading';readyAt = scheduler.now();seconds = guideReadingSeconds(autoGuideStops[index]!, content.text);deadline = readyAt + seconds * 1000;
    arm(seconds * 1000, () => {
      if (index === autoGuideStops.length - 1) { clear();phase = 'finished';lastReason = '导览结束，可重新导览或自由浏览。';notify(); }
      else move(index + 1);
    });
    notify();
  }
  return {
    get snapshot() { return snapshot(); }, get active() { return active(); }, get needsFrames() { return needsFrames(); },
    start, stop, refresh, tick, afterFrame,
    toggle() { if (active()) stop();else start(); },
    poke() { if (!disposed && phase === 'arriving') bridge.wake(); },
    dispose() { if (disposed) return;generation++;clear();disposed = true; },
  };
}
