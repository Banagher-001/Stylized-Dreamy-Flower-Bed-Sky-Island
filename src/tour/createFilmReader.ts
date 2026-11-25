import { Camera, Vector3 } from 'three';
import { filmStations, sampleFilmPresentation } from './filmReading';
import type { FilmReadingFrame } from './filmReading';
import { filmSliceWorks, filmWorks, workLabel } from './filmContent';
import type { ExhibitionWork } from './filmContent';
import { createFilmGallery } from './createFilmGallery';
import type { ViewerImage, ViewerRequest } from './createMediaViewer';
import { resolveTourPose, tourPoses } from './route';
import { createReaderFlow } from './readerFlow';

const escape = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);

function imageMedia(work: ExhibitionWork, src = work.image.src): ViewerImage {
  return {
    kind: 'image', src, title: work.title, description: work.summary,
    statusLabel: workLabel(work), alt: work.image.alt, poster: work.image.src,
  };
}

export function createFilmReader(app: HTMLElement, host: HTMLElement, anchorFor: (id: string) => Vector3 | undefined, openMedia: (media: ViewerRequest, trigger: HTMLElement) => void, gallerySettled: () => void) {
  const primary = filmWorks[0]!, secondary = filmWorks[1]!;
  function picture(work: ExhibitionWork, caption?: string) {
    const image = `<img data-work-image="${escape(work.id)}" width="${work.image.width}" height="${work.image.height}" alt="${escape(work.image.alt)}" decoding="async" />`;
    return `<figure class="film-picture"><button type="button" class="film-image-button" data-work="${escape(work.id)}" aria-label="查看《${escape(work.title)}》完整画面，${escape(workLabel(work))}">${image}<span class="film-image-placeholder" aria-hidden="true">载入中</span><span class="film-view-mark" aria-hidden="true">↗</span></button>${caption ? `<figcaption data-film-ink>${escape(caption)}</figcaption>` : ''}</figure>`;
  }
  const badge = `<p class="film-provenance" data-film-ink>${escape(workLabel(primary))}</p>`;
  const heroAction = primary.provenance === 'real' && primary.video ? primary.video.kind === 'file' ? '<button class="film-play" type="button" data-play-film>播放影片 ↗</button>' : `<a class="film-play" href="${escape(primary.video.src)}" target="_blank" rel="noopener noreferrer">打开影片 ↗</a>` : '';
  const panel = document.createElement('section');panel.className = 'film-reading';
  panel.setAttribute('aria-label', 'AI影像，沿第二根石柱浏览');panel.setAttribute('aria-hidden', 'true');panel.dataset.visible = 'false';
  const bodies = [
    `<div class="film-media film-hero">${picture(primary)}</div><p class="film-caption" data-film-ink>${escape(primary.summary)}</p>${badge}${heroAction}`,
    '',
    `<div class="film-media film-diptych">${picture(secondary, secondary.title)}${picture(primary, primary.title)}</div>${badge}`,
    '<p class="film-epilogue" data-film-ink>继续向下，进入交互实验。</p><span class="film-closing-trace" aria-hidden="true">↓</span>',
  ];
  const titles = [primary.title, '画面切片', '视觉探索', '影像，仍在继续。'];
  panel.innerHTML = filmStations.map((s, i) => `<article data-film-station="${s.id}" aria-labelledby="film-${s.id}-title" aria-hidden="true" inert hidden><p class="film-eyebrow">02 / AI 影像 ${s.id === 'B2' ? '<span class="film-slice-count"></span>' : `<span>${s.label}</span>`}</p><h2 id="film-${s.id}-title">${escape(titles[i]!)}</h2><div class="film-body">${bodies[i]}</div></article>`).join('');
  const connector = document.createElementNS('http://www.w3.org/2000/svg', 'svg');connector.classList.add('film-reading-link');connector.setAttribute('aria-hidden', 'true');
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');connector.append(line);
  app.querySelector('main')!.append(connector, panel);
  const articles = [...panel.querySelectorAll<HTMLElement>('article')];
  const galleryArticle = articles[1]!;
  const sliceImages = filmSliceWorks.map(({ work, originalSrc }) => imageMedia(work, originalSrc));
  const gallery = createFilmGallery(galleryArticle, filmSliceWorks, (index, trigger) => openMedia({ images: sliceImages, index }, trigger), gallerySettled);
  const flow = createReaderFlow(panel);
  const parts = articles.map((article) => ({
    article, title: article.querySelector<HTMLElement>('h2')!, eyebrow: article.querySelector<HTMLElement>('.film-eyebrow')!, body: article.querySelector<HTMLElement>('.film-body')!, media: article.querySelector<HTMLElement>('.film-media'),
    inks: [...article.querySelectorAll<HTMLElement>('[data-film-ink],.film-play')], buttons: article === galleryArticle ? [] : [...article.querySelectorAll<HTMLButtonElement>('button')],
  }));
  const listeners = new AbortController();
  const point = new Vector3();
  const fitPoint = new Vector3(), fitCamera = new Camera();
  let reading: FilmReadingFrame | undefined, camera: Camera | undefined;
  let selected = '';
  let previousPhase = '';
  let primed = false;
  let lastProjection = 0;
  let disposed = false, dirty = true;
  let reduced = false;
  let lastSignature = '';
  let layoutFrame: number | undefined;
  let bounds = host.getBoundingClientRect();
  let header = app.querySelector<HTMLElement>('.tour-header')!.getBoundingClientRect();
  let heading = app.querySelector<HTMLElement>('.tour-heading')!.getBoundingClientRect();
  let nav = app.querySelector<HTMLElement>('.tour-stops')!.getBoundingClientRect();
  let panelHeight = 0, panelWidth = 0;

  function sourceImages(article: HTMLElement) {
    if (article === galleryArticle) { gallery.prepare();return; }
    for (const img of article.querySelectorAll<HTMLImageElement>('img[data-work-image]')) {
      if (img.hasAttribute('src')) continue;
      const work = filmWorks.find((w) => w.id === img.dataset.workImage)!;
      const button = img.closest<HTMLButtonElement>('.film-image-button')!;
      img.addEventListener('load', () => { button.dataset.imageState = 'ready'; }, { once: true, signal: listeners.signal });
      img.addEventListener('error', () => { button.dataset.imageState = 'error';const placeholder = button.querySelector<HTMLElement>('.film-image-placeholder')!;placeholder.textContent = '载入失败'; }, { once: true, signal: listeners.signal });
      img.src = work.image.src;
    }
  }
  function measure() {
    if (flow.active) return;
    bounds = host.getBoundingClientRect();header = app.querySelector<HTMLElement>('.tour-header')!.getBoundingClientRect();heading = app.querySelector<HTMLElement>('.tour-heading')!.getBoundingClientRect();nav = app.querySelector<HTMLElement>('.tour-stops')!.getBoundingClientRect();
    connector.setAttribute('viewBox', `0 0 ${window.innerWidth} ${window.innerHeight}`);
    dirty = true;lastSignature = '';
  }
  function place() {
    if (!reading || !camera || flow.active) return;
    const anchor = anchorFor(reading.station.id);
    if (anchor) point.copy(anchor);else point.set(4.41, reading.station.y, -1);
    point.project(camera);
    const x = bounds.left + (point.x + 1) * bounds.width / 2, y = bounds.top + (1 - point.y) * bounds.height / 2;
    const gallery = reading.station.id === 'B2';
    const stacked = window.innerWidth <= 1000;
    const right = stacked ? window.innerWidth - 16 : nav.left - 24;
    const desiredLeft = stacked ? 16 : x + (gallery ? 64 : bounds.width * .085);
    if (dirty) {
      panelWidth = stacked ? window.innerWidth - 32 : Math.min(gallery ? 944 : 560, right - desiredLeft);
      panel.style.width = `${Math.max(1, panelWidth)}px`;
      panel.style.setProperty('--film-media-height', '0px');
      const chrome = panel.getBoundingClientRect().height;
      // Size from this station's held pose, so a reverse entry cannot inherit
      // a different media height from an earlier point in the descent.
      const base = tourPoses[reading.station.id === 'B1' ? 'B' : reading.station.id];
      const fit = resolveTourPose(base, bounds.width / bounds.height);
      fitCamera.copy(camera, false);fitCamera.position.set(...fit.position);fitCamera.up.set(0, 1, 0);fitCamera.lookAt(...fit.target);fitCamera.updateMatrixWorld(true);
      fitPoint.copy(anchor ?? new Vector3(4.41, reading.station.y, -1)).project(fitCamera);
      const heldY = bounds.top + (1 - fitPoint.y) * bounds.height / 2;
      const minTop = stacked ? Math.max(heading.bottom + 16, heldY + 40) : Math.max(header.bottom + 16, desiredLeft < heading.right + 16 ? heading.bottom + 16 : 0);
      const bottom = stacked ? Math.min(bounds.bottom - 20, nav.top - 20) : bounds.bottom - 20;
      const desiredHeight = gallery ? Math.min(520, panelWidth * .61) : reading.station.id === 'B3' ? 280 : (panelWidth - (stacked ? 28 : 40)) * primary.image.height / primary.image.width;
      const mediaHeight = Math.max(0, Math.min(desiredHeight, Math.floor(bottom) - Math.ceil(minTop) - chrome - 1));
      panel.style.setProperty('--film-media-height', `${mediaHeight}px`);
      panelHeight = panel.getBoundingClientRect().height;
      dirty = false;
    }
    const left = Math.max(16, Math.min(desiredLeft, right - panelWidth));
    const minTop = stacked ? Math.max(heading.bottom + 16, y + 40) : Math.max(header.bottom + 16, left < heading.right + 16 ? heading.bottom + 16 : 0);
    const bottom = stacked ? Math.min(bounds.bottom - 20, nav.top - 20) : bounds.bottom - 20;
    const top = Math.max(Math.ceil(minTop), Math.min(Math.round(stacked ? y + 60 : y - panelHeight / 2), Math.floor(bottom - panelHeight)));
    panel.style.left = `${Math.round(left)}px`;panel.style.top = `${Math.round(top)}px`;
    panel.dataset.anchorX = x.toFixed(4);panel.dataset.anchorY = y.toFixed(4);panel.dataset.layout = stacked ? 'stacked' : 'side';
    const clear = stacked ? top >= y + 40 : left >= x + 60;
    panel.dataset.anchorClear = String(clear);panel.dataset.fits = String(clear && panelWidth <= right - 16 && top + panelHeight <= bottom + .5 && top >= header.bottom + 16);
    const sx = Math.round(x), sy = Math.round(y), sl = Math.round(left), st = Math.round(top);
    line.setAttribute('d', stacked ? `M ${sx} ${sy + 28} Q ${sx} ${st - 14} ${Math.round(left + panelWidth / 2)} ${st - 8}` : `M ${sx + 38} ${sy} C ${sl - 30} ${sy}, ${sl - 30} ${st + 30}, ${sl - 8} ${st + 30}`);
  }
  function viewWork(work: ExhibitionWork, trigger: HTMLElement, play = false) {
    const video = play && work.video?.kind === 'file' ? work.video : undefined;
    const image = imageMedia(work);
    openMedia(video ? { ...image, kind: 'video', src: video.src } : image, trigger);
  }
  panel.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('button[data-work],button[data-play-film]') : null;
    if (!target || target.disabled) return;
    const play = target.hasAttribute('data-play-film');
    viewWork(play ? primary : filmWorks.find((w) => w.id === target.dataset.work)!, target, play);
  }, { signal: listeners.signal });
  const observer = new ResizeObserver(() => {
    if (disposed || flow.active || layoutFrame !== undefined) return;
    layoutFrame = requestAnimationFrame(() => { layoutFrame = undefined;if (!disposed && !flow.active) { measure();place(); } });
  });
  for (const element of [host, panel, app.querySelector<HTMLElement>('.tour-header')!, app.querySelector<HTMLElement>('.tour-heading')!, app.querySelector<HTMLElement>('.tour-stops')!]) observer.observe(element);
  measure();
  return {
    prime() { if (!disposed && !primed) { primed = true;sourceImages(articles[0]!); } },
    setFlow(enabled: boolean, measuring = false) {
      flow.set(enabled);lastSignature = '';dirty = true;
      if (!measuring) gallery.setFlow(enabled);
      if (enabled) {
        for (const article of articles) sourceImages(article);
      } else measure();
    },
    setCovered(value: boolean) { gallery.setCovered(value); },
    get galleryReady() { return gallery.ready; },
    get galleryImage() { return gallery.image; },
    update(next: FilmReadingFrame | undefined, nextCamera: Camera, reducedMotion = false, measuring = false) {
      reading = next;camera = nextCamera;reduced = reducedMotion;
      const state = sampleFilmPresentation(reading, reduced);
      if (flow.active) return state;
      if (!measuring) {
        const held = host.dataset.cameraState === 'settled';
        const side = Number(host.dataset.displayH) > filmStations[1].stop ? -1 : 1;
        gallery.setImmersive(reading?.station.id === 'B2' && reading.phase === 'read', held, side);
      }
      if (lastProjection !== camera.projectionMatrix.elements[0]) { lastProjection = camera.projectionMatrix.elements[0]!;dirty = true; }
      if (previousPhase !== (reading?.phase ?? 'off')) { previousPhase = reading?.phase ?? 'off';dirty = true; }
      const progress = (reading?.progress ?? 0).toFixed(7);
      if (panel.dataset.progress !== progress) panel.dataset.progress = progress;
      const signature = `${reading?.station.id}|${reading?.phase}|${state.frame}|${state.media}|${state.title}|${state.body}|${state.offset}|${reduced}|${camera.position.x}|${camera.position.y}|${camera.position.z}|${camera.projectionMatrix.elements[0]}`;
      if (signature === lastSignature && !dirty) return state;
      lastSignature = signature;
      if (selected !== (reading?.station.id ?? '')) {
        selected = reading?.station.id ?? '';dirty = true;
        for (const article of articles) article.hidden = article.dataset.filmStation !== selected;
        if (reading && !measuring) {
          const i = filmStations.indexOf(reading.station);sourceImages(articles[i]!);if (articles[i + 1]) sourceImages(articles[i + 1]!);
        }
      }
      const visible = !!reading && state.frame > .000001;
      panel.dataset.visible = String(visible);panel.dataset.station = reading?.station.id ?? '';panel.dataset.phase = reading?.phase ?? 'off';
      panel.dataset.frameOpacity = state.frame.toFixed(7);panel.dataset.mediaOpacity = state.media.toFixed(7);panel.dataset.titleOpacity = state.title.toFixed(7);panel.dataset.bodyOpacity = state.body.toFixed(7);
      panel.style.visibility = visible ? 'visible' : 'hidden';panel.setAttribute('aria-hidden', String(!visible));panel.style.setProperty('--film-frame-opacity', String(state.frame));
      connector.style.opacity = String(state.frame * .6);
      for (const { article, title, eyebrow, body, media, inks, buttons } of parts) {
        const active = visible && article.dataset.filmStation === selected;
        article.setAttribute('aria-hidden', String(!active));article.inert = !active;
        for (const element of [title, eyebrow]) { element.style.opacity = String(active ? state.title : 0);element.setAttribute('aria-hidden', String(!active || state.title <= .000001)); }
        body.style.visibility = active && Math.max(state.media, state.body) > .000001 ? 'inherit' : 'hidden';body.setAttribute('aria-hidden', String(!active || Math.max(state.media, state.body) <= .000001));
        for (const ink of inks) { const opacity = ink.classList.contains('film-provenance') ? state.media : state.body;ink.style.opacity = String(opacity);ink.setAttribute('aria-hidden', String(!active || opacity <= .000001)); }
        if (media) { media.style.opacity = String(state.media);media.style.transform = `translateY(${state.offset}px)`;media.style.clipPath = reduced || state.media >= 1 ? 'none' : `inset(0 ${(1 - state.media) * 100}% 0 0)`;media.setAttribute('aria-hidden', String(!active || state.media <= .000001)); }
        for (const button of buttons) button.disabled = !active || state.body < .999999 || state.media < .999999;
      }
      if (reading) place();
      return state;
    },
    get element() { return panel; },
    dispose() { disposed = true;if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);gallery.dispose();listeners.abort();observer.disconnect();panel.remove();connector.remove(); },
  };
}
