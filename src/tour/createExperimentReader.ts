import { Vector3 } from 'three';
import type { Camera } from 'three';
import { experimentStations, sampleExperimentPresentation } from './experimentReading';
import type { ExperimentReadingFrame } from './experimentReading';
import { experimentContent as content } from './experimentContent';
import { projectOrder, projects } from './projectContent';
import type { ProjectId, ProjectTab } from './projectContent';
import { createReaderFlow } from './readerFlow';

/** Short pillar inscriptions; extended content lives in the project archive. */
export function createExperimentReader(app: HTMLElement, host: HTMLElement, anchorFor: (id: string) => Vector3 | undefined, open: (id: ProjectId, tab: ProjectTab, trigger: HTMLElement) => void, handover: () => void) {
  const project = projects.lawson;
  const panel = document.createElement('section');panel.className = 'experiment-reading';panel.setAttribute('aria-label', '交互实验，沿第三根石柱浏览');panel.setAttribute('aria-hidden', 'true');
  const bodies = [
    `<p data-experiment-ink>${content.C1.body}</p><ol class="experiment-process" data-experiment-ink aria-label="从想法到交互">${content.C1.steps.map((s) => `<li>${s}</li>`).join('')}</ol>`,
    `<div class="experiment-project-selector" role="tablist" aria-label="选择交互作品">${projectOrder.map((id) => `<button type="button" role="tab" id="experiment-project-${id}" data-project-select="${id}" aria-controls="experiment-project-preview" aria-selected="${id === 'lawson'}" tabindex="${id === 'lawson' ? 0 : -1}"><span>${projects[id].label}</span>${projects[id].title}</button>`).join('')}</div><div id="experiment-project-preview" role="tabpanel" aria-labelledby="experiment-project-lawson"><div class="experiment-project-summary"><figure class="experiment-cover"><img width="${project.cover.width}" height="${project.cover.height}" alt="${project.cover.alt}" decoding="async"/><span class="experiment-image-state" role="status">封面载入中</span></figure><div><p class="experiment-kind" data-experiment-ink>${project.kind}</p><p class="experiment-summary" data-experiment-ink>${project.summary}</p></div></div><div class="experiment-entry-actions"><button type="button" data-project-tab="live">进入完整网页 <span aria-hidden="true">↗</span></button><button type="button" data-project-tab="archive">项目档案 <span aria-hidden="true">＋</span></button></div></div>`,
    `<p data-experiment-ink>${content.C3.body}</p><p class="experiment-cue" data-experiment-ink><span aria-hidden="true">↓</span> ${content.C3.cue}</p>`,
  ];
  const titles = [content.C1.title, project.title, content.C3.title];
  panel.innerHTML = experimentStations.map((s, i) => `<article data-experiment-station="${s.id}" aria-labelledby="experiment-${s.id}-title" aria-hidden="true" inert hidden><p class="experiment-eyebrow">03 / 交互实验 <span>${s.label}</span></p><h2 id="experiment-${s.id}-title">${titles[i]}</h2><div class="experiment-body">${bodies[i]}</div></article>`).join('');
  const connector = document.createElementNS('http://www.w3.org/2000/svg', 'svg');connector.classList.add('experiment-reading-link');connector.setAttribute('aria-hidden', 'true');
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');connector.append(line);app.querySelector('main')!.append(connector, panel);
  const parts = [...panel.querySelectorAll<HTMLElement>('article')].map((article) => ({ article, title: article.querySelector<HTMLElement>('h2')!, eyebrow: article.querySelector<HTMLElement>('.experiment-eyebrow')!, body: article.querySelector<HTMLElement>('.experiment-body')!, buttons: [...article.querySelectorAll<HTMLButtonElement>('button')] }));
  const flow = createReaderFlow(panel);
  let image = panel.querySelector<HTMLImageElement>('img')!;
  const imageState = panel.querySelector<HTMLElement>('.experiment-image-state')!;
  let coverListeners: AbortController | undefined;
  const controller = new AbortController(), options = { signal: controller.signal };
  let primed = false, fallback = false, disposed = false, dirty = true, selected = '', signature = '';
  let projectId: ProjectId = 'lawson', unavailable = false;
  let layoutFrame: number | undefined;
  let reading: ExperimentReadingFrame | undefined, camera: Camera | undefined;
  let bounds = host.getBoundingClientRect(), header = app.querySelector<HTMLElement>('.tour-header')!.getBoundingClientRect(), heading = app.querySelector<HTMLElement>('.tour-heading')!.getBoundingClientRect(), nav = app.querySelector<HTMLElement>('.tour-stops')!.getBoundingClientRect();
  let width = 0, height = 0;
  const point = new Vector3();
  function prime() {
    if (primed || disposed) return;
    primed = true;coverListeners?.abort();coverListeners = new AbortController();
    const current = image, src = new URL(projects[projectId].cover.src, document.baseURI).href;
    const ownsCover = () => !disposed && current === image && current.src === src;
    imageState.hidden = false;imageState.textContent = '封面载入中';panel.dataset.coverState = 'loading';
    current.addEventListener('load', () => { if (ownsCover()) { imageState.hidden = true;panel.dataset.coverState = 'ready'; } }, { signal: coverListeners.signal });
    current.addEventListener('error', () => { if (ownsCover()) { imageState.hidden = false;imageState.textContent = '封面暂不可用';panel.dataset.coverState = 'error'; } }, { signal: coverListeners.signal });
    current.src = src;
  }
  function syncButtons() {
    const active = fallback || flow.active || (reading?.station.id === 'C2' && sampleExperimentPresentation(reading).body >= .999999);
    for (const button of panel.querySelectorAll<HTMLButtonElement>('[data-project-select],[data-project-tab]')) {
      button.disabled = !active || (button.dataset.projectTab === 'live' && projectId === 'courtyard' && unavailable);
      if (button.dataset.projectSelect) {
        const current = button.dataset.projectSelect === projectId;
        button.setAttribute('aria-selected', String(current));button.tabIndex = current ? 0 : -1;
      }
    }
    const liveButton = panel.querySelector<HTMLButtonElement>('[data-project-tab="live"]')!;
    liveButton.title = unavailable && projectId === 'courtyard' ? '庭院场景暂不可用，可查看项目档案。' : '';
  }
  function choose(id: ProjectId) {
    handover();projectId = id;const item = projects[id];primed = false;
    panel.dataset.projectId = id;
    panel.querySelector('#experiment-C2-title')!.textContent = item.title;
    panel.querySelector('.experiment-kind')!.textContent = item.kind;
    panel.querySelector('.experiment-summary')!.textContent = item.summary;
    panel.querySelector('#experiment-project-preview')!.setAttribute('aria-labelledby', `experiment-project-${id}`);
    // Each resource owns its image callbacks; an old response cannot mark the
    // current project ready or failed. The article and preview stay in place.
    const nextImage = document.createElement('img');
    nextImage.width = item.cover.width;nextImage.height = item.cover.height;nextImage.alt = item.cover.alt;nextImage.decoding = 'async';
    image.replaceWith(nextImage);image = nextImage;
    const liveButton = panel.querySelector<HTMLButtonElement>('[data-project-tab="live"]')!;
    liveButton.innerHTML = `${item.primaryAction} <span aria-hidden="true">↗</span>`;
    liveButton.setAttribute('aria-label', `${item.primaryAction}：${item.title}`);
    panel.querySelector('[data-project-tab="archive"]')!.setAttribute('aria-label', `查看${item.title}项目档案`);
    signature = '';dirty = true;prime();syncButtons();measure();place();
  }
  panel.addEventListener('click', (event) => {
    const selector = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('[data-project-select]') : null;
    if (selector && !selector.disabled) { choose(selector.dataset.projectSelect as ProjectId);return; }
    const button = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('[data-project-tab]') : null;
    if (button && !button.disabled) open(projectId, button.dataset.projectTab as ProjectTab, button);
  }, options);
  panel.querySelector('.experiment-project-selector')!.addEventListener('keydown', event => {
    const e = event as KeyboardEvent;if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const current = projectOrder.indexOf(projectId), next = (current + (e.key === 'ArrowLeft' ? -1 : 1) + projectOrder.length) % projectOrder.length;
    const id = e.key === 'Home' ? projectOrder[0] : e.key === 'End' ? projectOrder[projectOrder.length - 1]! : projectOrder[next]!;
    choose(id);panel.querySelector<HTMLButtonElement>(`[data-project-select="${id}"]`)!.focus({ preventScroll: true });
  }, options);
  panel.dataset.projectId = projectId;
  function measure() {
    if (flow.active) return;
    bounds = host.getBoundingClientRect();header = app.querySelector<HTMLElement>('.tour-header')!.getBoundingClientRect();heading = app.querySelector<HTMLElement>('.tour-heading')!.getBoundingClientRect();nav = app.querySelector<HTMLElement>('.tour-stops')!.getBoundingClientRect();
    connector.setAttribute('viewBox', `0 0 ${innerWidth} ${innerHeight}`);dirty = true;signature = '';
  }
  function place() {
    if (!reading || !camera || fallback || flow.active) return;
    point.copy(anchorFor(reading.station.id) ?? new Vector3(2.96, reading.station.y, 5.09)).project(camera);
    const x = bounds.left + (point.x + 1) * bounds.width / 2, y = bounds.top + (1 - point.y) * bounds.height / 2;
    const stacked = innerWidth <= 1000, right = stacked ? innerWidth - 16 : nav.left - 24;
    const desiredLeft = stacked ? 16 : x + bounds.width * .085;
    if (dirty) { width = stacked ? innerWidth - 32 : Math.min(500, right - desiredLeft);panel.style.width = `${Math.max(1, width)}px`;height = panel.getBoundingClientRect().height;dirty = false; }
    const left = Math.max(16, Math.min(desiredLeft, right - width));
    const minTop = stacked ? Math.max(heading.bottom + 16, y + 40) : Math.max(header.bottom + 16, left < heading.right + 16 ? heading.bottom + 16 : 0);
    const bottom = stacked ? Math.min(bounds.bottom - 16, nav.top - 16) : bounds.bottom - 20;
    const top = Math.max(Math.ceil(minTop), Math.min(Math.round(stacked ? y + 52 : y - height / 2), Math.floor(bottom - height)));
    panel.style.left = `${Math.round(left)}px`;panel.style.top = `${Math.round(top)}px`;
    const clear = stacked ? top >= y + 40 : left >= x + 60;
    panel.dataset.anchorX = x.toFixed(4);panel.dataset.anchorY = y.toFixed(4);panel.dataset.anchorClear = String(clear);panel.dataset.layout = stacked ? 'stacked' : 'side';panel.dataset.fits = String(clear && top + height <= bottom + .5 && top >= header.bottom + 16);
    line.setAttribute('d', stacked ? `M ${Math.round(x)} ${Math.round(y + 28)} Q ${Math.round(x)} ${Math.round(top - 14)} ${Math.round(left + width / 2)} ${Math.round(top - 8)}` : `M ${Math.round(x + 38)} ${Math.round(y)} C ${Math.round(left - 30)} ${Math.round(y)}, ${Math.round(left - 30)} ${Math.round(top + 30)}, ${Math.round(left - 8)} ${Math.round(top + 30)}`);
  }
  const observer = new ResizeObserver(() => {
    // Project entry resizes the shared host. Apply layout outside observer
    // delivery so WebKit can finish that delivery before we change panel size.
    if (disposed || flow.active || layoutFrame !== undefined) return;
    layoutFrame = requestAnimationFrame(() => { layoutFrame = undefined;if (!disposed) { measure();place(); } });
  });
  for (const el of [host, panel, app.querySelector<HTMLElement>('.tour-heading')!, app.querySelector<HTMLElement>('.tour-header')!, app.querySelector<HTMLElement>('.tour-stops')!]) observer.observe(el);
  measure();
  return {
    prime,
    update(next: ExperimentReadingFrame | undefined, nextCamera: Camera, reduced = false, measuring = false) {
      reading = next;camera = nextCamera;
      const state = sampleExperimentPresentation(reading, reduced);
      if (fallback || flow.active) return state;
      panel.dataset.progress = (reading?.progress ?? 0).toFixed(7);
      const nextSignature = `${reading?.station.id}|${reading?.phase}|${state.frame}|${state.title}|${state.body}|${state.offset}|${camera.position.toArray()}|${camera.projectionMatrix.elements[0]}`;
      if (signature === nextSignature && !dirty) return state;signature = nextSignature;
      if (selected !== (reading?.station.id ?? '')) { selected = reading?.station.id ?? '';dirty = true;for (const part of parts) part.article.hidden = part.article.dataset.experimentStation !== selected; }
      const visible = !!reading && state.frame > .000001;
      panel.dataset.visible = String(visible);panel.dataset.station = selected;panel.dataset.phase = reading?.phase ?? 'off';panel.dataset.titleOpacity = state.title.toFixed(7);panel.dataset.bodyOpacity = state.body.toFixed(7);
      panel.style.visibility = visible ? 'visible' : 'hidden';panel.setAttribute('aria-hidden', String(!visible));panel.style.setProperty('--experiment-frame-opacity', String(state.frame));connector.style.opacity = String(state.title * .6);
      for (const { article, title, eyebrow, body, buttons } of parts) {
        const active = visible && article.dataset.experimentStation === selected;
        article.inert = !active;article.setAttribute('aria-hidden', String(!active));
        for (const element of [title, eyebrow]) { element.style.opacity = String(active ? state.title : 0);element.setAttribute('aria-hidden', String(!active || state.title <= .000001)); }
        body.style.opacity = String(active ? state.body : 0);body.style.visibility = active && state.body > .000001 ? 'inherit' : 'hidden';body.style.transform = `translateY(${state.offset}px)`;body.setAttribute('aria-hidden', String(!active || state.body <= .000001));
        for (const button of buttons) button.disabled = !active || state.body < .999999;
      }
      syncButtons();
      if (reading) { if (reading.station.id === 'C2' && !measuring) prime();place(); }
      return state;
    },
    showFallback() {
      fallback = true;unavailable = true;prime();panel.classList.add('experiment-fallback');panel.style.visibility = 'visible';panel.setAttribute('aria-hidden', 'false');panel.style.setProperty('--experiment-frame-opacity', '1');connector.style.display = 'none';
      for (const part of parts) {
        part.article.hidden = false;part.article.inert = false;part.article.setAttribute('aria-hidden', 'false');
        for (const element of [part.title, part.eyebrow, part.body]) { element.style.opacity = '1';element.style.visibility = 'visible';element.removeAttribute('aria-hidden');element.style.transform = 'none'; }
        for (const button of part.buttons) { button.disabled = button.dataset.projectTab === 'live';if (button.disabled) button.title = '图形场景暂不可用，可查看项目档案。'; }
      }
      syncButtons();
    },
    setFlow(enabled: boolean, gardenUnavailable = false) { unavailable = gardenUnavailable;flow.set(enabled, unavailable && projectId === 'courtyard');signature = '';dirty = true;syncButtons();if (enabled) prime();else measure(); },
    get projectId() { return projectId; },
    get element() { return panel; },
    dispose() { disposed = true;if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);controller.abort();coverListeners?.abort();observer.disconnect();panel.remove();connector.remove(); },
  };
}
