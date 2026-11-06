import './tour.css';
import './film.css';
import './experiment.css';
import './readingLayout.css';
import { Vector3 } from 'three';
import { pagePalette } from '../config/palette';
import { renderConfig } from '../config/scene';
import type { RenderMode } from '../config/scene';
import { waterConfig } from '../config/water';
import { resolveVisualOptions } from '../config/visual';
import { resolveEnvironmentOptions } from '../config/environment';
import { createScene } from '../scene/createScene';
import { createRenderer } from '../rendering/createRenderer';
import type { RendererState } from '../rendering/createRenderer';
import { createAnimationController } from '../animation/createAnimationController';
import type { AnimationState } from '../animation/createAnimationController';
import { sampleTour, resolveTourPose, tourStops, tourTotalH, tourPoses } from './route';
import { readingStations } from './reading';
import { createPillarReader } from './createPillarReader';
import { createPillarAppearance } from './createPillarAppearance';
import { createPillarMagic } from './createPillarMagic';
import { filmStations } from './filmReading';
import { createFilmReader } from './createFilmReader';
import { createMediaViewer } from './createMediaViewer';
import { filmAvailability } from './filmContent';
import { experimentStations } from './experimentReading';
import { createExperimentReader } from './createExperimentReader';
import { createProjectViewer } from './createProjectViewer';
import type { ProjectTab } from './createProjectViewer';
import { chapterLabels, createTourPresentation } from './presentation';
import { createReadingLayout } from './createReadingLayout';
import type { ReadingCapacity, ReadingPosition } from './createReadingLayout';

for (const [key, color] of Object.entries(pagePalette)) document.documentElement.style.setProperty(`--color-${key}`, color);
const app = document.querySelector<HTMLDivElement>('#app');
if (!app) throw new Error('Missing application root.');
const query = new URLSearchParams(location.search);
const debug = query.get('debug') === '1';
const requestedMode = query.get('render');
let mode: RenderMode = requestedMode === 'native' || requestedMode === 'pixel' ? requestedMode : renderConfig.defaultMode;
const parsed = query.get('waterTime')?.trim();
const time = parsed ? Number(parsed) : NaN;
const fixedTime = Number.isFinite(time) && time >= 0 && time <= 86400 ? time : undefined;
const originalTitle = document.title;
const previousRestoration = history.scrollRestoration;
history.scrollRestoration = 'manual';
document.title = `sakan · 张辰翰｜AIGC创作庭院${debug ? ' / DEBUG' : ''}`;
document.documentElement.classList.add('tour-document');
app.innerHTML = `
  <main class="tour-prototype" data-debug="${debug}" aria-label="sakan 的滚动庭院、个人介绍、AI影像与交互实验">
    <div id="tour-host" class="scene-host tour-stage" data-render-state="loading"><p id="tour-notice" class="scene-notice" hidden></p></div>
    <header class="tour-header"><div class="tour-brand"><span>sakan.</span><p>CREATIVE COURTYARD</p></div><div class="tour-header-actions"><button type="button" id="tour-layout-toggle" data-reading-toggle>稳定阅读</button><a id="tour-reference" class="tour-reference" ${debug ? '' : 'hidden'}>返回参考稿 <span aria-hidden="true">↗</span></a></div></header>
    <section class="tour-heading" data-kind="opening" aria-label="当前章节与回看"><p class="tour-kicker">SAKAN / 张辰翰</p><h1 id="tour-title">让想象，动起来。</h1><p id="tour-note">AI动画 · 视觉创作 · 交互实验</p><p class="tour-scroll-cue"><span aria-hidden="true">↓</span> 向下滚动，进入庭院</p><div class="tour-ending-actions" hidden inert aria-hidden="true"><button type="button" data-tour-replay="overview" data-h="0" disabled>回到开场 <span aria-hidden="true">↗</span></button><button type="button" data-tour-replay="films" data-h="4.95" disabled>回看影像 <span aria-hidden="true">↗</span></button></div></section>
    <nav class="tour-stops" aria-label="庭院章节">${tourStops.map((stop, i) => `<button type="button" id="tour-stop-${stop.id}" data-stop="${stop.id}" data-h="${stop.h}" aria-label="${stop.label}"><span class="tour-stop-index" aria-hidden="true">${i === 0 ? '○' : i === 4 ? '≈' : `0${i}`}</span><span>${stop.label.replace(/^\d+\s*/, '')}</span></button>`).join('')}</nav>
    <div id="tour-focus" class="tour-focus" hidden aria-hidden="true"><span></span><small id="tour-focus-label"></small></div>
    <div id="tour-reading-area" class="tour-reading-area" hidden aria-hidden="true"><span>READING SPACE</span><p>阅读区域预留</p><small>本步只校准柱首站构图</small></div>
    <footer class="tour-footer"><div class="tour-progress-row"><span id="tour-phase">GARDEN</span><progress id="tour-progress" max="1" value="0" aria-label="庭院浏览进度"></progress><span id="tour-percent">0%</span></div><div class="tour-footer-row"><p class="tour-instruction">滚动进入庭院 <span aria-hidden="true">↓</span><span>向上滚动可返回</span></p><div class="tour-actions"><div class="mode-controls" role="group" aria-label="画面模式"><button type="button" data-mode="native">正常画面</button><button type="button" data-mode="pixel">像素画面</button></div><button id="tour-motion" type="button" class="motion-control">暂停动效</button><details class="tour-inspector" ${debug ? '' : 'hidden inert'}><summary>镜头数据</summary><div class="tour-inspector-panel"><nav class="tour-reading-stops" aria-label="阅读站点调试定位"><span>阅读定位（调试）</span>${[...readingStations, ...filmStations, ...experimentStations].map((station) => `<button type="button" data-reading-stop="${station.id}" data-h="${station.stop}">${station.id}</button>`).join('')}</nav><pre id="tour-inspector-data"></pre></div></details></div></div></footer>
    <p id="tour-status" class="sr-only" role="status" aria-live="polite"></p>
    <div id="tour-scroll-space" class="tour-scroll-space" aria-hidden="true"></div>
    <div id="tour-viewport-probe" class="tour-viewport-probe" aria-hidden="true"></div>
  </main>`;

const host = app.querySelector<HTMLDivElement>('#tour-host')!;
const notice = app.querySelector<HTMLParagraphElement>('#tour-notice')!;
const status = app.querySelector<HTMLElement>('#tour-status')!;
const marker = app.querySelector<HTMLElement>('#tour-focus')!;
const markerLabel = app.querySelector<HTMLElement>('#tour-focus-label')!;
const readingArea = app.querySelector<HTMLElement>('#tour-reading-area')!;
const motion = app.querySelector<HTMLButtonElement>('#tour-motion')!;
const inspector = app.querySelector<HTMLDetailsElement>('.tour-inspector')!;
const inspectorData = app.querySelector<HTMLElement>('#tour-inspector-data')!;
const stopButtons = [...app.querySelectorAll<HTMLButtonElement>('[data-stop]')];
const readingButtons = [...app.querySelectorAll<HTMLButtonElement>('[data-reading-stop]')];
const modeButtons = [...app.querySelectorAll<HTMLButtonElement>('[data-mode]')];
const reference = new URL(location.href);
reference.searchParams.set('tour', 'reference');
reference.hash = '';
app.querySelector<HTMLAnchorElement>('#tour-reference')!.href = reference.href;
const presentation = createTourPresentation(app, debug);
const listenerController = new AbortController();
const eventOptions = { signal: listenerController.signal };
const spacer = app.querySelector<HTMLElement>('#tour-scroll-space')!;
const viewportProbe = app.querySelector<HTMLElement>('#tour-viewport-probe')!;
const footer = app.querySelector<HTMLElement>('.tour-footer')!;
let magic: ReturnType<typeof createPillarMagic>;
let filmMagic: ReturnType<typeof createPillarMagic>;
let experimentMagic: ReturnType<typeof createPillarMagic>;
let mediaViewer: ReturnType<typeof createMediaViewer>;
let projectViewer: ReturnType<typeof createProjectViewer>;
const reader = createPillarReader(app, host, (id) => magic?.getAnchor(id));
const filmReader = createFilmReader(app, host, (id) => filmMagic?.getAnchor(id), (media, trigger) => mediaViewer.open(media, trigger));
const experimentReader = createExperimentReader(app, host, (id) => experimentMagic?.getAnchor(id), (tab, trigger) => projectViewer.open(tab, trigger));
const world = createScene(resolveEnvironmentOptions(query), query.get('pool') === 'legacy' ? 'legacy' : 'refined', query.get('orb') === 'legacy' ? 'legacy' : 'lively');
host.dataset.fountainStyle = world.fountainStyle;
host.dataset.fountainResources = JSON.stringify(world.fountainMetadata ?? null);
host.dataset.orbStyle = world.orbStyle;
host.dataset.orbResources = JSON.stringify(world.orbMetadata ?? null);
const appearance = createPillarAppearance(world.scene);
const filmAppearance = createPillarAppearance(world.scene, 'columnRight');
const experimentAppearance = createPillarAppearance(world.scene, 'columnLower');
try { magic = createPillarMagic(world.scene); } catch (error) { console.warn('Pillar decoration unavailable; reading remains available.', error); }
try { filmMagic = createPillarMagic(world.scene, { column: 'columnRight', number: '02', stations: filmStations, poses: [tourPoses.B, tourPoses.B2, tourPoses.B3, tourPoses.B4] }); } catch (error) { console.warn('Film pillar decoration unavailable; exhibition remains available.', error); }
try { experimentMagic = createPillarMagic(world.scene, { column: 'columnLower', number: '03', stations: experimentStations, poses: [tourPoses.C, tourPoses.C2, tourPoses.C3] }); } catch (error) { console.warn('Experiment decoration unavailable; project remains available.', error); }
host.dataset.magicStatus = magic ? 'ready' : 'fallback';
host.dataset.magicResources = JSON.stringify(magic ? { ...magic.metadata, bindings: appearance.bindings } : { bindings: appearance.bindings });
host.dataset.filmMagicStatus = filmMagic ? 'ready' : 'fallback';
host.dataset.filmMagicResources = JSON.stringify(filmMagic ? { ...filmMagic.metadata, bindings: filmAppearance.bindings } : { bindings: filmAppearance.bindings });
host.dataset.filmAvailability = JSON.stringify(filmAvailability);
host.dataset.experimentMagicStatus = experimentMagic ? 'ready' : 'fallback';
host.dataset.experimentMagicResources = JSON.stringify(experimentMagic ? { ...experimentMagic.metadata, bindings: experimentAppearance.bindings } : { bindings: experimentAppearance.bindings });
host.dataset.overlayState = 'closed';
if (!magic) status.textContent = '装饰暂不可用，仍可滚动阅读。';
let view: ReturnType<typeof createRenderer> | undefined;
let targetH = 0;
let displayH = 0;
let lastAspect = window.innerWidth / window.innerHeight;
let lastScrollAt = 0;
let cameraTimestamp: number | null = null;
let loopRequested = true;
let disposed = false;
let failed = false;
let layoutLock = false;
let mediaOpen = false;
let mediaProgress = 0;
let overlayOwner: 'media' | 'project' | undefined;
let projectTab: ProjectTab | undefined;
let contextLost = false;
let restoreFrame: number | undefined;
let recoveryTimer: number | undefined;
let lastInspection = 0;
let scrollRange = 1;
let navigationH: number | undefined;
let readingLayout: ReturnType<typeof createReadingLayout> | undefined;
let overlayPosition: ReadingPosition | undefined;
let routeWidth = 0, routeHeight = 0, routeFooter = 0;
const focusPoint = new Vector3();
const rounded = (values: number[]) => values.map((value) => Number(value.toFixed(7)));
const cameraMoving = () => !readingLayout?.stable && Math.abs(targetH - displayH) > 0.0000001;
const covered = () => mediaOpen || projectTab === 'archive';
const offscreen = () => !!readingLayout?.stable && !readingLayout.coverVisible && projectTab !== 'live';

function syncLoop() {
  if (!view || disposed || failed) return;
  const wanted = !covered() && !offscreen() && (animation.state.playing || (!projectTab && cameraMoving()));
  if (wanted !== loopRequested) {
    loopRequested = wanted;
    cameraTimestamp = null;
    view.setAnimating(wanted);
  }
}

function syncAnimation(state: AnimationState) {
  motion.textContent = state.playing ? '暂停动效' : '播放动效';
  motion.title = state.reducedMotion && !state.playing ? '已按减少动态设置暂停，可手动播放' : '';
  host.dataset.motionState = state.hidden ? 'hidden' : covered() ? 'covered' : state.playing ? 'running' : 'paused';
  host.dataset.visibility = state.hidden ? 'hidden' : 'visible';
  cameraTimestamp = null;
  view?.setSuspended(state.hidden || covered() || offscreen());
  projectViewer?.sync(mode, state.playing, failed ? 'failed' : contextLost ? 'recovering' : 'none');
  if (state.reducedMotion) displayH = targetH;
  syncLoop();
  if (view && !loopRequested && !state.hidden && !covered() && !offscreen()) view.renderOnce();
}
const animation = createAnimationController(syncAnimation, fixedTime ?? waterConfig.initialTime, fixedTime !== undefined, { retainReducedPause: true });
function beginOverlay(owner: 'media' | 'project') {
  if (!overlayOwner) { mediaProgress = displayH;overlayPosition = readingLayout?.capture(); }
  targetH = displayH;overlayOwner = owner;
  mediaOpen = owner === 'media';
  document.documentElement.classList.toggle('tour-media-open', mediaOpen);
  document.documentElement.classList.toggle('tour-project-open', owner === 'project');
  host.dataset.overlayState = 'open';
  presentation.setCovered(true);
}
function closeOverlay(owner: 'media' | 'project') {
  if (overlayOwner !== owner) return;
  overlayOwner = undefined;mediaOpen = false;projectTab = undefined;
  document.documentElement.classList.remove('tour-media-open', 'tour-project-open');host.dataset.projectView = 'closed';host.dataset.overlayState = 'closed';
  presentation.setCovered(false);
  if (disposed) return;
  displayH = targetH = mediaProgress;
  if (overlayPosition) { readingLayout?.restore(overlayPosition);overlayPosition = undefined; }
  else resizeLayout();
  if (!failed) applyCamera();
  animation.resetTimestamp();syncAnimation(animation.state);
}
mediaViewer = createMediaViewer(app, {
  open() {
    projectViewer?.close();projectTab = undefined;beginOverlay('media');
    animation.resetTimestamp();syncAnimation(animation.state);
  },
  close() { closeOverlay('media'); },
});
function setProjectTab(tab: ProjectTab) {
  projectTab = tab;host.dataset.projectView = tab;animation.resetTimestamp();
  if (!failed) applyCamera();syncAnimation(animation.state);
}
projectViewer = createProjectViewer(app, {
  open(tab) { mediaViewer.close();beginOverlay('project');setProjectTab(tab); },
  change: setProjectTab,
  close() { closeOverlay('project'); },
  mode: setMode,
  motion() { animation.toggle(); },
});

function experiencePose() {
  const area = projectViewer.liveBounds, bounds = host.getBoundingClientRect();
  if (area.width < 1 || area.height < 1) return resolveTourPose(tourPoses.O, lastAspect);
  const pose = resolveTourPose(tourPoses.O, area.width / area.height);
  pose.viewHeight *= bounds.height / area.height;
  const eye = new Vector3(...pose.position), target = new Vector3(...pose.target);
  const direction = eye.clone().sub(target).normalize();
  const right = new Vector3(0, 1, 0).cross(direction).normalize(), up = direction.clone().cross(right).normalize();
  const x = .5 - (area.left + area.width / 2 - bounds.left) / bounds.width;
  const y = (area.top + area.height / 2 - bounds.top) / bounds.height - .5;
  const shift = right.multiplyScalar(x * pose.viewHeight * lastAspect).add(up.multiplyScalar(y * pose.viewHeight));
  pose.position = eye.add(shift).toArray();pose.target = target.add(shift).toArray();
  return pose;
}

function applyCamera() {
  const frame = sampleTour(displayH);
  const pose = projectTab === 'live' ? experiencePose() : resolveTourPose(readingLayout?.stable ? tourPoses.O : frame.pose, lastAspect);
  world.setViewHeight(pose.viewHeight);
  world.camera.position.set(...pose.position);
  world.camera.up.set(0, 1, 0);
  world.camera.lookAt(...pose.target);
  world.camera.updateMatrixWorld(true);
  presentation.update(frame, animation.state.reducedMotion, !cameraMoving(), scrollRange - window.scrollY <= 1);
  host.dataset.stage = frame.stage;
  host.dataset.chapter = frame.chapter;
  host.dataset.displayH = displayH.toFixed(7);
  host.dataset.targetH = targetH.toFixed(7);
  host.dataset.cameraState = cameraMoving() ? 'moving' : 'settled';
  host.dataset.cameraPosition = JSON.stringify(rounded(pose.position));
  host.dataset.cameraTarget = JSON.stringify(rounded(pose.target));
  host.dataset.viewHeight = pose.viewHeight.toFixed(7);
  host.dataset.aspect = lastAspect.toFixed(7);
  host.dataset.readingStation = frame.reading?.station.id ?? '';
  host.dataset.readingPhase = frame.reading?.phase ?? 'off';
  const lettering = reader.update(projectTab ? undefined : frame.reading, world.camera, animation.state.reducedMotion);
  host.dataset.readingOpacity = lettering.body.toFixed(7);
  host.dataset.readingTitleOpacity = lettering.title.toFixed(7);
  const exhibition = filmReader.update(projectTab ? undefined : frame.filmReading, world.camera, animation.state.reducedMotion);
  host.dataset.filmStation = frame.filmReading?.station.id ?? '';
  host.dataset.filmPhase = frame.filmReading?.phase ?? 'off';
  host.dataset.filmPresentation = JSON.stringify(exhibition);
  if (displayH >= 3.7 && displayH < 8) filmReader.prime();
  const experiment = experimentReader.update(projectTab ? undefined : frame.experimentReading, world.camera, animation.state.reducedMotion);
  host.dataset.experimentStation = frame.experimentReading?.station.id ?? '';host.dataset.experimentPhase = frame.experimentReading?.phase ?? 'off';host.dataset.experimentPresentation = JSON.stringify(experiment);
  if (displayH >= 8 && displayH < 11.1) experimentReader.prime();
  if (navigationH !== undefined && !cameraMoving()) {
    if (Math.abs(displayH - navigationH) < .003) status.textContent = `已到达${chapterLabels[frame.chapter]}。`;
    navigationH = undefined;
  }
  marker.hidden = !debug || !frame.column || !!frame.reading || !!frame.filmReading || !!frame.experimentReading;
  readingArea.hidden = marker.hidden;
  if (debug && frame.column) {
    focusPoint.set(...frame.pose.target).project(world.camera);
    const bounds = host.getBoundingClientRect();
    marker.style.left = `${bounds.left + (focusPoint.x * 0.5 + 0.5) * bounds.width}px`;
    marker.style.top = `${bounds.top + (-focusPoint.y * 0.5 + 0.5) * bounds.height}px`;
    markerLabel.textContent = frame.reading ? `${frame.reading.station.id} / ${frame.reading.station.label}` : `${frame.title.slice(0, 2)} / 柱首站`;
    markerLabel.style.opacity = String(frame.reading?.opacity ?? 1);
  }
  return frame;
}

function update(timestamp: number) {
  if (disposed || failed || covered() || offscreen()) return;
  const now = performance.now();
  if (!projectTab && cameraMoving()) {
    const elapsed = cameraTimestamp === null ? 1 / 60 : Math.max(0, Math.min(0.05, (timestamp - cameraTimestamp) / 1000));
    if (animation.state.reducedMotion || now - lastScrollAt >= 140) displayH = targetH;
    else displayH += (targetH - displayH) * (1 - Math.exp(-elapsed / 0.012));
    if (Math.abs(targetH - displayH) < 0.0000001) displayH = targetH;
  }
  cameraTimestamp = timestamp;
  const frame = applyCamera();
  const sceneTime = animation.advance(timestamp);
  world.update(sceneTime);
  const inscriptions = !projectTab && !readingLayout?.stable;
  const magicFrame = magic?.update(inscriptions ? frame.reading : undefined, world.camera, sceneTime, animation.state.reducedMotion, mode);
  const filmMagicFrame = filmMagic?.update(inscriptions ? frame.filmReading : undefined, world.camera, sceneTime, animation.state.reducedMotion, mode);
  const experimentMagicFrame = experimentMagic?.update(inscriptions ? frame.experimentReading : undefined, world.camera, sceneTime, animation.state.reducedMotion, mode);
  host.dataset.magicFrame = JSON.stringify(magicFrame ?? null);
  host.dataset.filmMagicFrame = JSON.stringify(filmMagicFrame ?? null);
  host.dataset.experimentMagicFrame = JSON.stringify(experimentMagicFrame ?? null);
  host.dataset.sceneTime = sceneTime.toFixed(6);
  if (now - lastInspection >= 200 || !cameraMoving()) {
    lastInspection = now;
    const stats = view?.getStats();
    host.dataset.rendererStats = JSON.stringify(stats ?? null);
    if (inspector.open) inspectorData.textContent = JSON.stringify({ stage: frame.stage, progressH: Number(displayH.toFixed(4)), targetH: Number(targetH.toFixed(4)), position: rounded(world.camera.position.toArray()), lookAt: JSON.parse(host.dataset.cameraTarget!), viewHeight: Number(host.dataset.viewHeight), reading: frame.reading ? { station: frame.reading.station.id, phase: frame.reading.phase, progress: Number(frame.reading.progress.toFixed(4)), titleOpacity: Number(host.dataset.readingTitleOpacity), bodyOpacity: Number(host.dataset.readingOpacity), fits: reader.element.dataset.fits } : null, magic: { status: host.dataset.magicStatus, state: magicFrame, resources: magic?.metadata }, sceneTime: Number(sceneTime.toFixed(3)), renderer: stats }, null, 2);
  }
  syncLoop();
}

function readScroll() {
  if (disposed || layoutLock || overlayOwner) return;
  if (readingLayout?.stable) { readingLayout.scroll();return; }
  if (failed) return;
  const range = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  scrollRange = range;
  const next = Math.min(tourTotalH, Math.max(0, window.scrollY / range * tourTotalH));
  if (navigationH !== undefined && Math.abs(next - navigationH) >= .003) navigationH = undefined;
  if (Math.abs(next - targetH) < 0.0000001) return;
  targetH = next;
  lastScrollAt = performance.now();
  if (animation.state.reducedMotion) { displayH = targetH;applyCamera(); }
  syncLoop();
  if (view && !loopRequested && !animation.state.hidden) view.renderOnce();
}

function resizeLayout() {
  if (disposed) return;
  if (readingLayout?.stable) return;
  if (overlayOwner) return;
  const preserved = displayH;
  layoutLock = true;
  const footerHeight = footer.getBoundingClientRect().height;
  app!.style.setProperty('--tour-footer-height', `${footerHeight}px`);
  const h = viewportProbe.getBoundingClientRect().height || window.innerHeight;
  spacer.style.height = `${tourTotalH * h + window.innerHeight}px`;
  const range = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  scrollRange = range;
  if (routeWidth !== innerWidth || routeHeight !== h || routeFooter !== footerHeight) window.scrollTo({ top: preserved / tourTotalH * range, behavior: 'instant' });
  routeWidth = innerWidth;routeHeight = h;routeFooter = footerHeight;
  targetH = preserved;
  displayH = preserved;
  cameraTimestamp = null;
  if (restoreFrame !== undefined) cancelAnimationFrame(restoreFrame);
  restoreFrame = requestAnimationFrame(() => { restoreFrame = undefined;layoutLock = false;readScroll(); });
}

function rendererState(state: RendererState) {
  contextLost = state === 'context-lost';
  presentation.setUnavailable(failed || state === 'context-lost' || state === 'restored');
  projectViewer.sync(mode, animation.state.playing, contextLost ? 'recovering' : 'none');
  if (state === 'restored') { animation.resetTimestamp();cameraTimestamp = null;readingLayout?.available();return; }
  clearTimeout(recoveryTimer);
  const lost = state === 'context-lost';
  notice.hidden = !lost;
  for (const button of [...modeButtons, motion]) button.disabled = lost;
  if (lost) {
    readingLayout?.unavailable();
    notice.textContent = '画面正在恢复，请稍候。';
    status.textContent = '图形连接中断，正在恢复画面。';
    recoveryTimer = window.setTimeout(() => { notice.textContent = '画面恢复较慢，可刷新重试或返回参考稿。';status.textContent = notice.textContent; }, 4000);
  } else { status.textContent = '画面已恢复。';readingLayout?.available(); }
}

function restoreReadingH(h: number, y?: number) {
  displayH = targetH = Math.max(0, Math.min(tourTotalH, h));
  routeWidth = 0;resizeLayout();
  if (y !== undefined) window.scrollTo({ top: y, behavior: 'instant' });
  if (!failed) { applyCamera();syncLoop();if (!animation.state.hidden && !offscreen()) view?.renderOnce(); }
}
function flowReaders(enabled: boolean) {
  reader.setFlow(enabled);filmReader.setFlow(enabled);experimentReader.setFlow(enabled, failed || contextLost);
}
function measureReadingCapacity(): ReadingCapacity {
  if (failed || contextLost) return { fits: false, margin: 0, stations: [] };
  const main = app!.querySelector<HTMLElement>('main')!, wasStable = !!readingLayout?.stable;
  const beforeY = scrollY, rows: ReadingCapacity['stations'] = [];
  const current = sampleTour(displayH), camera = world.camera.clone();
  main.dataset.readingMode = 'immersive';document.documentElement.classList.remove('tour-stable-reading');
  presentation.update(sampleTour(1.74), true, true, false);
  flowReaders(false);
  app!.style.setProperty('--tour-footer-height', `${footer.getBoundingClientRect().height}px`);
  try {
    const bounds = host.getBoundingClientRect(), aspect = bounds.width / bounds.height;
    for (const station of [...readingStations, ...filmStations, ...experimentStations]) {
      const frame = sampleTour(station.stop), pose = resolveTourPose(frame.pose, aspect);
      camera.top = pose.viewHeight / 2;camera.bottom = -camera.top;camera.left = -camera.top * aspect;camera.right = camera.top * aspect;
      camera.updateProjectionMatrix();camera.position.set(...pose.position);camera.up.set(0, 1, 0);camera.lookAt(...pose.target);camera.updateMatrixWorld(true);
      presentation.update(frame, true, true, false);
      // These are the real nodes, full reading state and actual projected pose.
      flowReaders(false);
      reader.update(frame.reading, camera, true);filmReader.update(frame.filmReading, camera, true, true);experimentReader.update(frame.experimentReading, camera, true, true);
      const panel = frame.reading ? reader.element : frame.filmReading ? filmReader.element : experimentReader.element;
      const r = panel.getBoundingClientRect(), nav = app!.querySelector('.tour-stops')!.getBoundingClientRect(), header = app!.querySelector('.tour-header')!.getBoundingClientRect();
      const bottom = innerWidth <= 1000 ? Math.min(bounds.bottom, nav.top) : bounds.bottom;
      const margin = Math.min(r.left, innerWidth - r.right, r.top - header.bottom, bottom - r.bottom);
      const media = frame.filmReading ? panel.querySelector<HTMLElement>(`[data-film-station="${station.id}"] .film-media`) : null;
      const mediaHeight = media?.getBoundingClientRect().height ?? null;
      const fits = panel.dataset.fits === 'true' && margin >= 16 && (mediaHeight === null || mediaHeight >= 64);
      rows.push({ id: station.id, fits, margin, mediaHeight, bounds: [r.x, r.y, r.width, r.height, bottom], anchorClear: panel.dataset.anchorClear === 'true', projectedFits: panel.dataset.fits === 'true' });
    }
    return { fits: rows.every(r => r.fits), margin: Math.min(...rows.map(r => r.margin)), stations: rows };
  } finally {
    main.dataset.readingMode = wasStable ? 'stable' : 'immersive';document.documentElement.classList.toggle('tour-stable-reading', wasStable);
    if (wasStable) { flowReaders(true);app!.querySelector<HTMLElement>('.tour-heading')!.setAttribute('aria-hidden', 'true'); }
    else { presentation.update(current, animation.state.reducedMotion, !cameraMoving(), scrollRange - beforeY <= 1);flowReaders(false);reader.update(current.reading, world.camera, animation.state.reducedMotion);filmReader.update(current.filmReading, world.camera, animation.state.reducedMotion);experimentReader.update(current.experimentReading, world.camera, animation.state.reducedMotion); }
    if (Math.abs(scrollY - beforeY) > .5) scrollTo({ top: beforeY, behavior: 'instant' });
  }
}
readingLayout = createReadingLayout(app, host, [reader.element, filmReader.element, experimentReader.element], {
  h: () => displayH, restore: restoreReadingH, flow: flowReaders, measure: measureReadingCapacity,
  unavailable: () => failed || contextLost, overlay: () => !!overlayOwner,
  refresh() { resizeLayout();if (!failed) applyCamera();animation.resetTimestamp();syncAnimation(animation.state); },
  visible() { animation.resetTimestamp();syncAnimation(animation.state); },
  live: trigger => projectViewer.open('live', trigger),
});

resizeLayout();
window.scrollTo({ top: 0, behavior: 'instant' });
try {
  view = createRenderer(host, mode, (aspect) => { lastAspect = aspect;world.setAspect(aspect);applyCamera(); }, resolveVisualOptions(query), rendererState);
  view.canvas.setAttribute('aria-label', '滚动庭院：第一柱介绍，第二柱AI影像设计样片，第三柱交互实验与真实庭院体验，随后回到水潭。');
  view.start(world.scene, world.camera, update);
  syncAnimation(animation.state);
} catch (error) {
  failed = true;
  presentation.setUnavailable(true);
  view?.dispose();
  animation.dispose();
  magic?.dispose();filmMagic?.dispose();experimentMagic?.dispose();appearance.dispose();filmAppearance.dispose();experimentAppearance.dispose();
  world.dispose();
  host.dataset.renderState = 'error';
  host.innerHTML = '<p class="render-error" role="alert">场景暂时无法显示，请开启图形加速后刷新，或使用上方入口返回参考稿。</p>';
  reader.update(undefined, world.camera);
  filmReader.update(undefined, world.camera);
  spacer.hidden = true;projectViewer.sync(mode, false, 'failed');
  for (const button of [...modeButtons, motion]) button.disabled = true;
  status.textContent = '场景初始化失败。';
  console.error('Tour scene initialization failed.', error);
}
readingLayout.start();

function navigate(h: number) {
  if (disposed || overlayOwner || !Number.isFinite(h)) return;
  if (readingLayout?.navigate(h)) return;
  if (failed || contextLost) return;
  navigationH = Math.max(0, Math.min(tourTotalH, h));
  status.textContent = '';
  const range = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  window.scrollTo({ top: navigationH / tourTotalH * range, behavior: 'instant' });
  readScroll();
  if (!cameraMoving()) applyCamera();
}
for (const button of [...stopButtons, ...readingButtons]) button.addEventListener('click', () => {
  navigate(Number(button.dataset.h));
}, eventOptions);
for (const button of presentation.replayButtons) button.addEventListener('click', () => {
  if (button.disabled || overlayOwner || contextLost || failed) return;
  navigate(Number(button.dataset.h));
  stopButtons.find((stop) => stop.dataset.stop === button.dataset.tourReplay)?.focus({ preventScroll: true });
}, eventOptions);
function setMode(next: RenderMode) {
    mode = next;
    view?.setMode(mode);
    for (const item of modeButtons) item.setAttribute('aria-pressed', String(item.dataset.mode === mode));
    const url = new URL(location.href);
    if (mode === renderConfig.defaultMode) url.searchParams.delete('render');
    else url.searchParams.set('render', mode);
    history.replaceState(null, '', url);
    status.textContent = mode === 'pixel' ? '已切换为像素预览。' : '已切换为正常画面。';
    projectViewer.sync(mode, animation.state.playing, contextLost ? 'recovering' : 'none');
}
for (const button of modeButtons) {
  button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
  button.addEventListener('click', () => setMode(button.dataset.mode as RenderMode), eventOptions);
}
motion.addEventListener('click', () => { animation.toggle();status.textContent = animation.state.playing ? '环境动效已继续。' : readingLayout?.stable ? '环境动效已暂停。' : '环境动效已暂停，仍可滚动运镜。'; }, eventOptions);
inspector.addEventListener('toggle', () => { lastInspection = 0;if (view && !loopRequested && !animation.state.hidden) view.renderOnce(); }, eventOptions);
window.addEventListener('scroll', readScroll, { passive: true, signal: listenerController.signal });
window.addEventListener('resize', () => { resizeLayout();readingLayout?.resize(); }, { passive: true, signal: listenerController.signal });
window.visualViewport?.addEventListener('resize', () => readingLayout?.resize(), { passive: true, signal: listenerController.signal });
let experienceLayoutFrame: number | undefined;
function queueExperienceLayout() {
  if (disposed || failed || projectTab !== 'live' || experienceLayoutFrame !== undefined) return;
  experienceLayoutFrame = requestAnimationFrame(() => {
    experienceLayoutFrame = undefined;
    if (!disposed && !failed && projectTab === 'live') { applyCamera();if (!animation.state.hidden) view?.renderOnce(); }
  });
}
const experienceResize = new ResizeObserver(queueExperienceLayout);
experienceResize.observe(projectViewer.element.querySelector('.tour-project-live-space')!);
projectViewer.element.addEventListener('scroll', queueExperienceLayout, { passive: true, capture: true, signal: listenerController.signal });

function dispose() {
  if (disposed) return;
  disposed = true;
  listenerController.abort();
  if (restoreFrame !== undefined) cancelAnimationFrame(restoreFrame);
  clearTimeout(recoveryTimer);
  experienceResize.disconnect();
  if (experienceLayoutFrame !== undefined) cancelAnimationFrame(experienceLayoutFrame);
  animation.dispose();
  readingLayout?.dispose();
  presentation.dispose();
  view?.dispose();
  mediaViewer.dispose();
  projectViewer.dispose();
  magic?.dispose();filmMagic?.dispose();experimentMagic?.dispose();appearance.dispose();filmAppearance.dispose();experimentAppearance.dispose();
  world.dispose();
  reader.dispose();
  filmReader.dispose();
  experimentReader.dispose();
  document.documentElement.classList.remove('tour-document', 'tour-media-open', 'tour-project-open');
  app!.style.removeProperty('--tour-footer-height');
  document.title = originalTitle;
  history.scrollRestoration = previousRestoration;
}
if (import.meta.hot) { import.meta.hot.accept();import.meta.hot.dispose(dispose); }
