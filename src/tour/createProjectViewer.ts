import type { RenderMode } from '../config/scene';
import { courtyardProject as project } from './experimentContent';
import type { ProjectTab } from './projectContent';

interface ProjectLifecycle {
  open(): void;
  change(): void;
  close(): void;
  mode(mode: RenderMode): void;
  motion(): void;
}

/** The water stop opens the garden's existing canvas and its media archive. */
export function createProjectViewer(root: HTMLElement, lifecycle: ProjectLifecycle, sceneLabel = '庭院全景：三根深色石柱与小花围绕蓝白水潭') {
  const dialog = document.createElement('dialog');dialog.className = 'tour-project-dialog';dialog.setAttribute('aria-labelledby', 'project-title');
  dialog.dataset.projectId = 'courtyard';dialog.dataset.experienceKind = 'host-scene';
  dialog.innerHTML = `<div class="tour-project-shell">
    <header class="tour-project-header">
      <div class="tour-project-identity"><p>03 / 交互实验 <span>交互网页场景</span></p><h2 id="project-title">${project.title}</h2></div>
      <div class="tour-project-tabs" role="tablist" aria-label="项目内容">
        <button type="button" role="tab" id="project-tab-live" aria-controls="tour-project-live" data-project-view="live">现场体验</button>
        <button type="button" role="tab" id="project-tab-archive" aria-controls="tour-project-archive" data-project-view="archive">项目档案</button>
      </div>
      <div class="tour-project-header-actions"><button type="button" class="tour-project-close" aria-label="关闭项目，返回阅读" autofocus><span>返回阅读</span><span aria-hidden="true">×</span></button></div>
    </header>
    <section id="tour-project-live" class="tour-project-live" role="tabpanel" aria-labelledby="project-tab-live">
      <div class="tour-project-live-space" role="img"><p class="tour-project-scene-status" role="status" hidden></p></div>
      <div class="tour-project-live-controls"><p>停一会儿，看风经过。</p><div><div role="group" aria-label="体验画面模式"><button type="button" data-project-mode="native">正常画面</button><button type="button" data-project-mode="pixel">像素画面</button></div><button type="button" class="tour-project-motion">播放动效</button></div></div>
    </section>
    <section id="tour-project-archive" class="tour-project-archive" role="tabpanel" aria-labelledby="project-tab-archive" tabindex="0" hidden></section>
  </div>`;
  root.append(dialog);
  const listeners = new AbortController(), options = { signal: listeners.signal };
  const tabs = [...dialog.querySelectorAll<HTMLButtonElement>('[data-project-view]')], closeButton = dialog.querySelector<HTMLButtonElement>('.tour-project-close')!;
  const live = dialog.querySelector<HTMLElement>('#tour-project-live')!, archive = dialog.querySelector<HTMLElement>('#tour-project-archive')!, liveSpace = dialog.querySelector<HTMLElement>('.tour-project-live-space')!;
  liveSpace.setAttribute('aria-label', sceneLabel);
  const shell = dialog.querySelector<HTMLElement>('.tour-project-shell')!;
  const modeButtons = [...dialog.querySelectorAll<HTMLButtonElement>('[data-project-mode]')], motion = dialog.querySelector<HTMLButtonElement>('.tour-project-motion')!, sceneStatus = dialog.querySelector<HTMLElement>('.tour-project-scene-status')!;
  let selected: ProjectTab = 'live', engaged = false, disposed = false;
  let initialized = false, gardenUnavailable: 'none' | 'recovering' | 'failed' = 'none';
  let trigger: HTMLElement | undefined, focusFrame: number | undefined;
  let video: HTMLVideoElement | undefined, loadListeners: AbortController | undefined, loadTimer: number | undefined;
  let generation = 0, archiveScroll = 0;
  let viewport: HTMLElement | undefined, mediaStatus: HTMLElement | undefined, retry: HTMLButtonElement | undefined;
  const archiveScroller = () => getComputedStyle(archive).overflowY === 'visible' ? shell : archive;
  function releaseVideo() {
    generation++;clearTimeout(loadTimer);loadListeners?.abort();loadListeners = undefined;
    if (video) { video.pause();video.removeAttribute('src');video.load();video.remove();video = undefined; }
    dialog.dataset.mediaState = 'idle';
  }
  function poster() {
    if (!viewport) return;
    viewport.innerHTML = `<img src="${project.frames[0].src}" width="680" height="680" alt="${project.frames[0].alt}"/><button type="button" class="tour-project-play" aria-label="播放固定视角动效片段">播放片段 <span aria-hidden="true">▷</span></button>`;
    if (mediaStatus) mediaStatus.textContent = '点击播放片段。';if (retry) retry.hidden = true;
  }
  function setMediaState(value: string, message: string) {
    dialog.dataset.mediaState = value;if (mediaStatus) mediaStatus.textContent = message;if (retry) retry.hidden = value !== 'error' && value !== 'slow';
  }
  function loadVideo(play: boolean) {
    if (selected !== 'archive' || !dialog.open || !viewport) return;
    releaseVideo();viewport.replaceChildren();loadListeners = new AbortController();const token = generation, loadOptions = { signal: loadListeners.signal };
    video = document.createElement('video');const item = video;
    item.controls = true;item.playsInline = true;item.preload = 'metadata';item.poster = project.frames[0].src;item.width = 680;item.height = 680;item.setAttribute('aria-label', project.clip.label);
    item.addEventListener('loadedmetadata', () => { if (token === generation) { clearTimeout(loadTimer);setMediaState('ready', '使用影片控件播放或暂停。'); } }, loadOptions);
    item.addEventListener('error', () => { if (token === generation) { clearTimeout(loadTimer);setMediaState('error', '片段暂时无法载入，可重试或返回阅读。'); } }, loadOptions);
    viewport.append(item);item.src = project.clip.src;setMediaState('loading', '片段载入中。');
    if (play) void item.play().catch(() => { if (token === generation && dialog.dataset.mediaState !== 'error') setMediaState('ready', '请使用影片控件开始播放。'); });
    loadTimer = window.setTimeout(() => { if (token === generation && dialog.dataset.mediaState === 'loading') setMediaState('slow', '载入较慢，可重试或返回阅读。'); }, 12000);
  }
  function initializeArchive() {
    if (initialized) return;
    initialized = true;archive.dataset.projectId = 'courtyard';
    archive.innerHTML = `<div class="project-archive-intro"><p class="tour-project-section-label">PROJECT / 庭院习作</p><p class="tour-project-introduction">${project.introduction}</p></div><figure class="project-current-cover"><img src="${project.cover.src}" width="${project.cover.width}" height="${project.cover.height}" alt="${project.cover.alt}" decoding="async"/><figcaption>当前庭院 · 全景</figcaption></figure><section class="tour-project-features"><h3>当前可体验</h3><ol>${project.features.map((f) => `<li>${f}</li>`).join('')}</ol></section><section class="tour-project-clip"><div><p class="tour-project-section-label">EARLIER STUDY / 早期习作</p><h3>${project.clip.label}</h3><p>${project.clip.note}</p><p>记录最初的水面与悬浮球，也保留庭院逐渐生长的痕迹。</p></div><div><div class="tour-project-video-viewport"></div><p class="tour-project-media-status" role="status" aria-live="polite"></p><button type="button" class="tour-project-media-retry" hidden>重新载入片段</button></div></section><div class="tour-project-frame-pair">${project.frames.map((f) => `<figure><img src="${f.src}" width="680" height="680" alt="${f.alt}" loading="lazy" decoding="async"/><figcaption>${f.label}</figcaption></figure>`).join('')}</div>`;
    viewport = archive.querySelector<HTMLElement>('.tour-project-video-viewport')!;mediaStatus = archive.querySelector<HTMLElement>('.tour-project-media-status')!;retry = archive.querySelector<HTMLButtonElement>('.tour-project-media-retry')!;
    for (const img of archive.querySelectorAll<HTMLImageElement>('img')) img.addEventListener('error', () => {
      const figure = img.closest('figure');if (!figure || figure.querySelector('.tour-project-image-error')) return;
      const text = document.createElement('p');text.className = 'tour-project-image-error';text.textContent = '画面暂不可用。';
      const button = document.createElement('button');button.type = 'button';button.textContent = '重新载入画面';button.addEventListener('click', () => { const src = img.src;img.removeAttribute('src');img.src = src; }, options);
      text.append(button);figure.append(text);
      img.addEventListener('load', () => text.remove(), { ...options, once: true });
    }, options);
    poster();
  }
  function select(tab: ProjectTab, notify: boolean) {
    if (notify && selected === tab) return;
    if (engaged && selected === 'archive') { archiveScroll = archiveScroller().scrollTop;releaseVideo();poster(); }
    selected = tab;dialog.dataset.tab = tab;live.hidden = tab !== 'live';archive.hidden = tab !== 'archive';
    for (const button of tabs) { const active = button.dataset.projectView === tab;button.setAttribute('aria-selected', String(active));button.tabIndex = active ? 0 : -1; }
    if (tab === 'archive') { initializeArchive();archiveScroller().scrollTop = archiveScroll; }
    else shell.scrollTop = 0;
    if (notify) lifecycle.change();
  }
  function finish() {
    if (dialog.open || !engaged) return;
    releaseVideo();poster();engaged = false;lifecycle.close();
    const target = trigger;trigger = undefined;
    focusFrame = requestAnimationFrame(() => {
      focusFrame = undefined;if (disposed || root.querySelector('dialog[open]')) return;
      const usable = target?.isConnected && !target.closest('[hidden],[inert]') && target.getClientRects().length;
      const fallback = root.querySelector<HTMLElement>('[data-reading-toggle]');
      (usable ? target : fallback)?.focus({ preventScroll: true });
    });
  }
  function close() { if (dialog.open) dialog.close();finish(); }
  closeButton.addEventListener('click', close, options);dialog.addEventListener('close', finish, options);
  dialog.addEventListener('cancel', (event) => { event.preventDefault();close(); }, options);
  for (const tab of tabs) tab.addEventListener('click', () => select(tab.dataset.projectView as ProjectTab, true), options);
  dialog.querySelector('.tour-project-tabs')!.addEventListener('keydown', (event) => {
    const key = (event as KeyboardEvent).key;if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(key)) return;
    event.preventDefault();const index = key === 'Home' ? 0 : key === 'End' ? 1 : selected === 'live' ? 1 : 0;
    if (!tabs[index]!.disabled) { tabs[index]!.focus();select(tabs[index]!.dataset.projectView as ProjectTab, true); }
  }, options);
  for (const button of modeButtons) button.addEventListener('click', () => lifecycle.mode(button.dataset.projectMode as RenderMode), options);
  motion.addEventListener('click', () => lifecycle.motion(), options);
  archive.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (target?.closest('.tour-project-play')) loadVideo(true);else if (target?.closest('.tour-project-media-retry')) loadVideo(false);
  }, options);
  document.addEventListener('visibilitychange', () => { if (document.hidden) video?.pause(); }, options);
  // The modal's document lock owns the background; preserve native pan/pinch
  // and video gestures inside the dialog, including short-screen layouts.
  return {
    open(source: HTMLElement) {
      if (disposed || dialog.open) return;
      if (focusFrame !== undefined) { cancelAnimationFrame(focusFrame);focusFrame = undefined; }
      trigger = source;archiveScroll = 0;engaged = true;
      select(gardenUnavailable === 'failed' ? 'archive' : 'live', false);lifecycle.open();dialog.showModal();shell.scrollTop = 0;archive.scrollTop = 0;closeButton.focus({ preventScroll: true });
    },
    close,
    sync(mode: RenderMode, playing: boolean, unavailable: 'none' | 'recovering' | 'failed' = 'none') {
      gardenUnavailable = unavailable;
      for (const button of modeButtons) { button.setAttribute('aria-pressed', String(button.dataset.projectMode === mode));button.disabled = unavailable !== 'none'; }
      motion.textContent = playing ? '暂停动效' : '播放动效';motion.disabled = unavailable !== 'none';tabs[0]!.disabled = unavailable === 'failed';
      sceneStatus.hidden = unavailable === 'none';sceneStatus.textContent = unavailable === 'recovering' ? '画面正在恢复，仍可查看档案或返回阅读。' : unavailable === 'failed' ? '图形场景暂不可用，可查看项目档案。' : '';
    },
    get active() { return engaged ? { id: 'courtyard' as const, tab: selected } : undefined; },
    get liveBounds() { return liveSpace.getBoundingClientRect(); },
    get element() { return dialog; },
    dispose() { if (disposed) return;disposed = true;listeners.abort();if (focusFrame !== undefined) cancelAnimationFrame(focusFrame);releaseVideo();if (dialog.open) dialog.close();if (engaged) { engaged = false;lifecycle.close(); }dialog.remove(); },
  };
}
