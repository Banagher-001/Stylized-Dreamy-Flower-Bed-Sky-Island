import { pagePalette } from '../config/palette';
import { createPortfolio } from './createPortfolio';
import { renderConfig } from '../config/scene';
import type { RenderMode } from '../config/scene';
import { createScene } from '../scene/createScene';
import { createRenderer } from '../rendering/createRenderer';
import type { RendererState } from '../rendering/createRenderer';
import { createAnimationController } from '../animation/createAnimationController';
import type { AnimationState } from '../animation/createAnimationController';
import { waterConfig } from '../config/water';
import { resolveVisualOptions } from '../config/visual';
import { resolveEnvironmentOptions } from '../config/environment';

for (const [name, color] of Object.entries(pagePalette)) {
  document.documentElement.style.setProperty(`--color-${name}`, color);
}

const app = document.querySelector<HTMLDivElement>('#app');
if (!app) throw new Error('Missing application root.');

let coverInView = true;
let projectOpen = false;
const portfolioPage = createPortfolio(app, (open) => {
  projectOpen = open;
  animation.resetTimestamp();
  syncAnimation(animation.state);
});

const host = app.querySelector<HTMLDivElement>('#scene-host')!;
const sceneNotice = app.querySelector<HTMLParagraphElement>('#scene-notice')!;
const status = app.querySelector<HTMLParagraphElement>('#render-status')!;
const buttons = [...app.querySelectorAll<HTMLButtonElement>('[data-mode]')];
const motionButton = app.querySelector<HTMLButtonElement>('#motion-control')!;
const query = new URLSearchParams(window.location.search);
const requestedMode = query.get('render');
let mode: RenderMode = requestedMode === 'pixel' || requestedMode === 'native'
  ? requestedMode
  : renderConfig.defaultMode;

const world = createScene(resolveEnvironmentOptions(query));
let view: ReturnType<typeof createRenderer> | undefined;
const listenerController = new AbortController();
const timeParameter = query.get('waterTime')?.trim();
const parsedTime = timeParameter ? Number(timeParameter) : NaN;
const fixedTime = Number.isFinite(parsedTime) && parsedTime >= 0 && parsedTime <= 86400 ? parsedTime : undefined;

function syncAnimation(state: AnimationState) {
  motionButton.textContent = state.playing ? '暂停动效' : '播放动效';
  motionButton.title = state.reducedMotion && !state.playing ? '已按减少动态设置暂停，点按可播放' : '';
  host.dataset.visibility = state.hidden ? 'hidden' : projectOpen ? 'covered' : coverInView ? 'visible' : 'offscreen';
  host.dataset.motionState = state.hidden ? 'hidden' : !coverInView || projectOpen ? 'offscreen' : state.playing ? 'running' : 'paused';
  view?.setSuspended(state.hidden || !coverInView || projectOpen);
  view?.setAnimating(state.playing);
}
const animation = createAnimationController(syncAnimation, fixedTime ?? waterConfig.initialTime, fixedTime !== undefined);
let recoveryTimer: number | undefined;
const coverObserver = new IntersectionObserver((entries) => {
  const visible = entries[0]?.isIntersecting ?? true;
  if (coverInView === visible) return;
  coverInView = visible;
  animation.resetTimestamp();
  syncAnimation(animation.state);
}, { rootMargin: '64px 0px', threshold: 0 });
coverObserver.observe(host);


function syncRendererState(state: RendererState) {
  if (state === 'restored') {
    animation.resetTimestamp();
    return;
  }
  window.clearTimeout(recoveryTimer);
  recoveryTimer = undefined;
  const lost = state === 'context-lost';
  sceneNotice.hidden = !lost;
  for (const button of [...buttons, motionButton]) button.disabled = lost;
  if (lost) {
    sceneNotice.textContent = '画面正在恢复，请稍候。';
    status.textContent = '图形连接中断，正在恢复画面。';
    recoveryTimer = window.setTimeout(() => {
      sceneNotice.textContent = '画面恢复较慢，可刷新页面重试。';
      status.textContent = sceneNotice.textContent;
    }, 4000);
  } else status.textContent = '画面已恢复。';
}

function updateControls() {
  for (const button of buttons) {
    button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
  }
  status.textContent = mode === 'pixel' ? '已切换为像素预览。' : '已切换为正常画面。';
}

try {
  view = createRenderer(host, mode, world.setAspect, resolveVisualOptions(query), syncRendererState);
  view.start(world.scene, world.camera, (timestamp) => {
    const time = animation.advance(timestamp);
    world.update(time);
    host.dataset.waterTime = time.toFixed(6);
    host.dataset.sceneTime = time.toFixed(6);
  });
  syncAnimation(animation.state);
  updateControls();

  motionButton.addEventListener('click', () => {
    animation.toggle();
    status.textContent = animation.state.playing ? '场景动效已继续。' : '场景动效已暂停。';
  }, { signal: listenerController.signal });

  for (const button of buttons) {
    button.addEventListener('click', () => {
      mode = button.dataset.mode as RenderMode;
      view?.setMode(mode);
      const url = new URL(window.location.href);
      if (mode === renderConfig.defaultMode) url.searchParams.delete('render');
      else url.searchParams.set('render', mode);
      window.history.replaceState(null, '', url);
      updateControls();
    }, { signal: listenerController.signal });
  }
} catch (error) {
  view?.dispose();
  world.dispose();
  host.dataset.renderState = 'error';
  const message = document.createElement('p');
  message.className = 'render-error';
  message.setAttribute('role', 'alert');
  message.textContent = '场景暂时无法显示，请开启浏览器图形加速后刷新页面。';
  host.replaceChildren(message);
  for (const button of buttons) button.disabled = true;
  motionButton.disabled = true;
  animation.dispose();
  status.textContent = '场景初始化失败。';
  console.error('Scene initialization failed.', error);
}

function dispose() {
  window.clearTimeout(recoveryTimer);
  listenerController.abort();
  coverObserver.disconnect();
  portfolioPage.dispose();
  animation.dispose();
  view?.dispose();
  world.dispose();
}

if (import.meta.hot) {
  import.meta.hot.accept();
  import.meta.hot.dispose(dispose);
}
