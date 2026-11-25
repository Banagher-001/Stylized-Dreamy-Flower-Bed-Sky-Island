export interface ViewerMedia {
  kind: 'image' | 'video';
  src: string;
  title: string;
  description: string;
  statusLabel: string;
  alt?: string;
  poster?: string;
}

export type ViewerImage = ViewerMedia & { kind: 'image' };
interface ViewerGallery {
  images: readonly ViewerImage[];
  index: number;
}
export type ViewerRequest = ViewerMedia | ViewerGallery;

const detailScale = 2;
const panKeys = new Map<string, [number, number]>([
  ['ArrowLeft', [44, 0]], ['ArrowRight', [-44, 0]], ['ArrowUp', [0, 44]], ['ArrowDown', [0, -44]],
]);

/** One native dialog/decoder, also usable with supplied media outside the tour. */
export function createMediaViewer(root: HTMLElement, lifecycle: { open(): void; close(): void }) {
  const dialog = document.createElement('dialog');
  dialog.className = 'film-dialog';
  dialog.setAttribute('aria-labelledby', 'film-media-title');
  dialog.setAttribute('aria-describedby', 'film-media-description');
  dialog.innerHTML = `
    <div class="film-dialog-shell">
      <header class="film-dialog-header">
        <div class="film-dialog-title">
          <p class="film-dialog-label"></p><h2 id="film-media-title"></h2><p class="film-dialog-count" hidden></p>
        </div>
        <button type="button" class="film-dialog-close" aria-label="关闭画面" autofocus>关闭 <span aria-hidden="true">×</span></button>
      </header>
      <div class="film-dialog-viewport" id="film-media-frame"></div>
      <footer class="film-dialog-footer">
        <p id="film-media-description"></p>
        <div class="film-dialog-actions" role="group" aria-label="查看图片" hidden>
          <button type="button" data-media-step="previous">上一张</button>
          <button type="button" class="film-dialog-zoom" aria-controls="film-media-frame">查看细节</button>
          <button type="button" data-media-step="next">下一张</button>
        </div>
        <div class="film-dialog-feedback">
          <p class="film-dialog-status" role="status" aria-live="polite"></p>
          <button type="button" class="film-media-retry" hidden>重新载入</button>
        </div>
      </footer>
    </div>`;
  root.append(dialog);
  const closeButton = dialog.querySelector<HTMLButtonElement>('.film-dialog-close')!;
  const retryButton = dialog.querySelector<HTMLButtonElement>('.film-media-retry')!;
  const title = dialog.querySelector<HTMLElement>('#film-media-title')!;
  const description = dialog.querySelector<HTMLElement>('#film-media-description')!;
  const label = dialog.querySelector<HTMLElement>('.film-dialog-label')!;
  const viewport = dialog.querySelector<HTMLElement>('.film-dialog-viewport')!;
  const feedback = dialog.querySelector<HTMLElement>('.film-dialog-feedback')!;
  const status = dialog.querySelector<HTMLElement>('.film-dialog-status')!;
  const count = dialog.querySelector<HTMLElement>('.film-dialog-count')!;
  const actions = dialog.querySelector<HTMLElement>('.film-dialog-actions')!;
  const previous = actions.querySelector<HTMLButtonElement>('[data-media-step="previous"]')!;
  const next = actions.querySelector<HTMLButtonElement>('[data-media-step="next"]')!;
  const zoom = actions.querySelector<HTMLButtonElement>('.film-dialog-zoom')!;
  const listeners = new AbortController();
  let loadListeners: AbortController | undefined;
  let media: ViewerMedia | undefined;
  let gallery: ViewerGallery | undefined;
  let image: HTMLImageElement | undefined;
  let video: HTMLVideoElement | undefined;
  let trigger: HTMLElement | undefined;
  let timer: number | undefined;
  let focusFrame: number | undefined;
  let generation = 0;
  let engaged = false;
  let disposed = false;
  let zoomed = false;
  let panX = 0, panY = 0;
  let pointer: { id: number; x: number; y: number } | undefined;

  function clearPointer() {
    const id = pointer?.id;
    pointer = undefined;
    viewport.removeAttribute('data-dragging');
    if (id !== undefined && viewport.hasPointerCapture(id)) viewport.releasePointerCapture(id);
  }
  function pan(dx = 0, dy = 0) {
    if (!zoomed || !image?.naturalWidth || !image.naturalHeight) return;
    const width = viewport.clientWidth, height = viewport.clientHeight;
    const fit = Math.min(width / image.naturalWidth, height / image.naturalHeight);
    const maxX = Math.max(0, (fit * image.naturalWidth * detailScale - width) / 2);
    const maxY = Math.max(0, (fit * image.naturalHeight * detailScale - height) / 2);
    panX = Math.max(-maxX, Math.min(maxX, panX + dx));
    panY = Math.max(-maxY, Math.min(maxY, panY + dy));
    image.style.transform = `translate3d(${panX}px, ${panY}px, 0) scale(${detailScale})`;
  }
  function setZoom(value: boolean) {
    clearPointer();
    zoomed = value;
    panX = panY = 0;
    viewport.toggleAttribute('data-zoomed', value);
    zoom.textContent = value ? '还原' : '查看细节';
    if (value) pan();
    else image?.style.removeProperty('transform');
  }
  function releaseMedia() {
    clearTimeout(timer);loadListeners?.abort();generation++;
    setZoom(false);
    image?.removeAttribute('src');image = undefined;
    if (video) { video.pause();video.removeAttribute('src');video.load();video = undefined; }
    viewport.replaceChildren();
  }
  function state(value: 'loading' | 'ready' | 'error' | 'slow', message: string) {
    dialog.dataset.state = value;status.textContent = message;
    retryButton.hidden = value !== 'error' && value !== 'slow';
    feedback.classList.toggle('sr-only', !!gallery && value === 'ready');
    zoom.disabled = value !== 'ready';
  }
  function load(requestPlay: boolean) {
    if (!media || disposed) return;
    releaseMedia();
    const token = generation;
    const item = media;
    loadListeners = new AbortController();
    const options = { signal: loadListeners.signal };
    state('loading', item.kind === 'image' ? '画面载入中。' : '影片载入中。');
    const ready = () => {
      if (token !== generation || !dialog.open) return;
      clearTimeout(timer);
      state('ready', item.kind === 'video' ? '使用影片控件播放，可按 ESC 返回。' : gallery ? `已载入《${item.title}》原图。` : '完整画面，可按 ESC 返回。');
    };
    const failed = () => { if (token === generation && dialog.open) { clearTimeout(timer);state('error', item.kind === 'image' ? '画面暂时无法载入，可重试或关闭返回。' : '影片暂时无法播放，可重试或关闭返回。'); } };
    if (item.kind === 'image') {
      image = document.createElement('img');
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
  function show(item: ViewerMedia) {
    media = item;
    title.textContent = item.title;
    title.title = gallery ? item.title : '';
    description.textContent = item.description;
    label.textContent = item.statusLabel;
    dialog.dataset.kind = item.kind;
    closeButton.setAttribute('aria-label', item.kind === 'video' ? '关闭放映' : '关闭画面');
    if (gallery && gallery.images.length > 1) {
      const format = (value: number) => String(value).padStart(2, '0');
      count.textContent = `${format(gallery.index + 1)} / ${format(gallery.images.length)}`;
      count.setAttribute('aria-label', `第 ${gallery.index + 1} 张，共 ${gallery.images.length} 张`);
      previous.setAttribute('aria-disabled', String(gallery.index === 0));
      next.setAttribute('aria-disabled', String(gallery.index === gallery.images.length - 1));
    }
    load(item.kind === 'video');
  }
  function step(direction: -1 | 1) {
    if (!gallery) return;
    const index = gallery.index + direction;
    const adjacent = gallery.images[index];
    if (!adjacent) return;
    gallery.index = index;
    show(adjacent);
  }
  function finish() {
    if (dialog.open) return; // An earlier queued close must not clear a rapid reopen.
    releaseMedia();media = undefined;gallery = undefined;
    dialog.removeAttribute('data-gallery');
    if (!engaged) return;
    engaged = false;lifecycle.close();
    const target = trigger;trigger = undefined;
    focusFrame = requestAnimationFrame(() => {
      focusFrame = undefined;
      if (!disposed && !root.querySelector('dialog[open]') && target?.isConnected && !target.closest('[hidden],[inert]') && target.getClientRects().length) target.focus({ preventScroll: true });
    });
  }
  const options = { signal: listeners.signal };
  closeButton.addEventListener('click', () => { video?.pause();dialog.close(); }, options);
  dialog.addEventListener('cancel', () => video?.pause(), options);
  dialog.addEventListener('close', finish, options);
  dialog.addEventListener('click', (event) => { if (event.target === dialog) { video?.pause();dialog.close(); } }, options);
  retryButton.addEventListener('click', () => {
    load(false);
    if (gallery) closeButton.focus({ preventScroll: true });
  }, options);
  document.addEventListener('visibilitychange', () => { if (document.hidden) video?.pause(); }, options);

  previous.addEventListener('click', () => step(-1), options);
  next.addEventListener('click', () => step(1), options);
  zoom.addEventListener('click', () => {
    if (gallery && dialog.dataset.state === 'ready') setZoom(!zoomed);
  }, options);
  dialog.addEventListener('keydown', event => {
    if (!gallery || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const displacement = panKeys.get(event.key);
    if (zoomed && displacement) {
      event.preventDefault();
      pan(...displacement);
    } else if (gallery.images.length > 1 && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
      event.preventDefault();
      step(event.key === 'ArrowLeft' ? -1 : 1);
    }
  }, options);
  viewport.addEventListener('wheel', event => {
    if (gallery && !event.ctrlKey && !event.metaKey) event.preventDefault();
  }, { ...options, passive: false });
  viewport.addEventListener('pointerdown', event => {
    if (!gallery || !event.isPrimary || event.button !== 0 || dialog.dataset.state !== 'ready') return;
    if (!zoomed && (event.pointerType !== 'touch' || gallery.images.length < 2)) return;
    pointer = { id: event.pointerId, x: event.clientX, y: event.clientY };
    if (zoomed) {
      event.preventDefault();
      viewport.setPointerCapture(event.pointerId);
      viewport.setAttribute('data-dragging', '');
    }
  }, options);
  viewport.addEventListener('pointermove', event => {
    if (!zoomed || pointer?.id !== event.pointerId) return;
    pan(event.clientX - pointer.x, event.clientY - pointer.y);
    pointer.x = event.clientX;pointer.y = event.clientY;
  }, options);
  viewport.addEventListener('pointerup', event => {
    if (pointer?.id !== event.pointerId) return;
    const x = event.clientX - pointer.x, y = event.clientY - pointer.y;
    clearPointer();
    if (!zoomed && Math.abs(x) >= Math.min(70, viewport.clientWidth * .2) && Math.abs(x) > Math.abs(y) * 1.25) step(x < 0 ? 1 : -1);
  }, options);
  const cancelPointer = (event: PointerEvent) => { if (pointer?.id === event.pointerId) clearPointer(); };
  viewport.addEventListener('pointercancel', cancelPointer, options);
  viewport.addEventListener('lostpointercapture', cancelPointer, options);
  const observer = new ResizeObserver(() => pan());
  observer.observe(viewport);

  return {
    open(request: ViewerRequest, source?: HTMLElement) {
      const item = 'images' in request ? request.images[request.index] : request;
      if (disposed || !item) return;
      if (focusFrame !== undefined) { cancelAnimationFrame(focusFrame);focusFrame = undefined; }
      // Moving inside the viewer uses this copy of the index. The gallery retains its opener.
      gallery = 'images' in request ? { ...request } : undefined;
      const multiple = !!gallery && gallery.images.length > 1;
      dialog.toggleAttribute('data-gallery', !!gallery);
      if (gallery) dialog.removeAttribute('aria-describedby');
      else dialog.setAttribute('aria-describedby', 'film-media-description');
      label.hidden = description.hidden = !!gallery;
      actions.hidden = !gallery;
      count.hidden = previous.hidden = next.hidden = !multiple;
      if (!dialog.open) {
        if (!engaged) {
          trigger = source ?? (document.activeElement instanceof HTMLElement ? document.activeElement : undefined);
          engaged = true;lifecycle.open();
        } else if (source) trigger = source;
        dialog.showModal();
      }
      show(item);
      closeButton.focus({ preventScroll: true });
    },
    close() { video?.pause();if (dialog.open) dialog.close(); },
    get element() { return dialog; },
    dispose() {
      if (disposed) return;
      disposed = true;
      if (focusFrame !== undefined) cancelAnimationFrame(focusFrame);
      listeners.abort();observer.disconnect();releaseMedia();media = undefined;gallery = undefined;
      if (dialog.open) dialog.close();
      if (engaged) { engaged = false;lifecycle.close(); }
      dialog.remove();
    },
  };
}
