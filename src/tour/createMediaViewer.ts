export interface ViewerMedia {
  kind: 'image' | 'video';
  src: string;
  title: string;
  description: string;
  statusLabel: string;
  alt?: string;
  poster?: string;
}

/** One native dialog/decoder, also usable with supplied media outside the tour. */
export function createMediaViewer(root: HTMLElement, lifecycle: { open(): void; close(): void }) {
  const dialog = document.createElement('dialog');
  dialog.className = 'film-dialog';
  dialog.setAttribute('aria-labelledby', 'film-media-title');
  dialog.setAttribute('aria-describedby', 'film-media-description');
  dialog.innerHTML = `<div class="film-dialog-shell"><header class="film-dialog-header"><div><p class="film-dialog-label"></p><h2 id="film-media-title"></h2></div><button type="button" class="film-dialog-close" aria-label="关闭画面" autofocus>关闭 <span aria-hidden="true">×</span></button></header><div class="film-dialog-viewport"></div><footer class="film-dialog-footer"><p id="film-media-description"></p><p class="film-dialog-status" role="status" aria-live="polite"></p><button type="button" class="film-media-retry" hidden>重新载入</button></footer></div>`;
  root.append(dialog);
  const closeButton = dialog.querySelector<HTMLButtonElement>('.film-dialog-close')!;
  const retryButton = dialog.querySelector<HTMLButtonElement>('.film-media-retry')!;
  const title = dialog.querySelector<HTMLElement>('#film-media-title')!;
  const description = dialog.querySelector<HTMLElement>('#film-media-description')!;
  const label = dialog.querySelector<HTMLElement>('.film-dialog-label')!;
  const viewport = dialog.querySelector<HTMLElement>('.film-dialog-viewport')!;
  const status = dialog.querySelector<HTMLElement>('.film-dialog-status')!;
  const listeners = new AbortController();
  let loadListeners: AbortController | undefined;
  let media: ViewerMedia | undefined;
  let video: HTMLVideoElement | undefined;
  let trigger: HTMLElement | undefined;
  let timer: number | undefined;
  let focusFrame: number | undefined;
  let generation = 0;
  let engaged = false;
  let disposed = false;

  function releaseMedia() {
    clearTimeout(timer);loadListeners?.abort();generation++;
    if (video) { video.pause();video.removeAttribute('src');video.load();video = undefined; }
    viewport.replaceChildren();
  }
  function state(value: 'loading' | 'ready' | 'error' | 'slow', message: string) {
    dialog.dataset.state = value;status.textContent = message;
    retryButton.hidden = value !== 'error' && value !== 'slow';
  }
  function load(requestPlay: boolean) {
    if (!media || disposed) return;
    releaseMedia();
    const token = generation;
    const item = media;
    loadListeners = new AbortController();
    const options = { signal: loadListeners.signal };
    state('loading', item.kind === 'image' ? '画面载入中。' : '影片载入中。');
    const ready = () => { if (token === generation && dialog.open) { clearTimeout(timer);state('ready', item.kind === 'image' ? '完整画面，可按 ESC 返回。' : '使用影片控件播放，可按 ESC 返回。'); } };
    const failed = () => { if (token === generation && dialog.open) { clearTimeout(timer);state('error', item.kind === 'image' ? '画面暂时无法载入，可重试或关闭返回。' : '影片暂时无法播放，可重试或关闭返回。'); } };
    if (item.kind === 'image') {
      const image = document.createElement('img');
      image.alt = item.alt ?? item.title;image.decoding = 'async';
      image.addEventListener('load', ready, options);image.addEventListener('error', failed, options);
      viewport.append(image);image.src = item.src;
    } else {
      video = document.createElement('video');
      video.controls = true;video.playsInline = true;video.preload = 'metadata';
      video.setAttribute('aria-label', item.title);
      if (item.poster) video.poster = item.poster;
      video.addEventListener('loadedmetadata', ready, options);video.addEventListener('error', failed, options);
      viewport.append(video);video.src = item.src;
      if (requestPlay) void video.play().catch(() => { if (token === generation && dialog.open && dialog.dataset.state !== 'error') status.textContent = '请使用影片控件开始播放。'; });
    }
    timer = window.setTimeout(() => { if (token === generation && dialog.open && dialog.dataset.state === 'loading') state('slow', '载入较慢，可重试或关闭返回。'); }, 12000);
  }
  function finish() {
    if (dialog.open) return; // An earlier queued close must not clear a rapid reopen.
    releaseMedia();media = undefined;
    if (!engaged) return;
    engaged = false;lifecycle.close();
    const target = trigger;trigger = undefined;
    focusFrame = requestAnimationFrame(() => { focusFrame = undefined;if (!disposed && !dialog.open && target?.isConnected) target.focus({ preventScroll: true }); });
  }
  const options = { signal: listeners.signal };
  closeButton.addEventListener('click', () => { video?.pause();dialog.close(); }, options);
  dialog.addEventListener('cancel', () => video?.pause(), options);
  dialog.addEventListener('close', finish, options);
  dialog.addEventListener('click', (event) => { if (event.target === dialog) { video?.pause();dialog.close(); } }, options);
  retryButton.addEventListener('click', () => load(false), options);
  document.addEventListener('visibilitychange', () => { if (document.hidden) video?.pause(); }, options);

  return {
    open(item: ViewerMedia, source?: HTMLElement) {
      if (disposed) return;
      if (focusFrame !== undefined) { cancelAnimationFrame(focusFrame);focusFrame = undefined; }
      media = item;
      if (!dialog.open) {
        if (!engaged) {
          trigger = source ?? (document.activeElement instanceof HTMLElement ? document.activeElement : undefined);
          engaged = true;lifecycle.open();
        } else if (source) trigger = source;
        dialog.showModal();
      }
      title.textContent = item.title;description.textContent = item.description;label.textContent = item.statusLabel;
      dialog.dataset.kind = item.kind;closeButton.setAttribute('aria-label', item.kind === 'video' ? '关闭放映' : '关闭画面');
      closeButton.focus({ preventScroll: true });load(item.kind === 'video');
    },
    close() { video?.pause();if (dialog.open) dialog.close(); },
    get element() { return dialog; },
    dispose() {
      if (disposed) return;
      disposed = true;
      if (focusFrame !== undefined) cancelAnimationFrame(focusFrame);
      listeners.abort();releaseMedia();media = undefined;
      if (dialog.open) dialog.close();
      if (engaged) { engaged = false;lifecycle.close(); }
      dialog.remove();
    },
  };
}
