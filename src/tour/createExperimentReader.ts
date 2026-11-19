import { Vector3 } from 'three';
import type { Camera } from 'three';
import { experimentStations, sampleExperimentPresentation } from './experimentReading';
import type { ExperimentReadingFrame } from './experimentReading';
import { experimentContent as content } from './experimentContent';
import { projects } from './projectContent';
import type { EmbeddedProjectId } from './projectContent';
import { createReaderFlow } from './readerFlow';
import { createExperimentScene } from './createExperimentScene';

const experimentProjectOrder = ['lawson', 'bottle-ocean'] as const satisfies readonly EmbeddedProjectId[];

interface ExperimentReaderActions {
  projectChanged(): void;
  sceneInput(): void;
  archiveLayoutChanged(): void;
}

/** Keep the original scenes and their archives at the third pillar. */
export function createExperimentReader(app: HTMLElement, host: HTMLElement, anchorFor: (id: string) => Vector3 | undefined, actions: ExperimentReaderActions) {
  const firstProject = experimentProjectOrder[0];
  const project = projects[firstProject];
  const panel = document.createElement('section');panel.className = 'experiment-reading';panel.setAttribute('aria-label', '交互实验，沿第三根石柱浏览');panel.setAttribute('aria-hidden', 'true');
  const projectTabs = experimentProjectOrder.map((id) => {
    const selected = id === firstProject;
    return `<button type="button" role="tab" id="experiment-project-${id}" data-project-select="${id}" aria-controls="experiment-project-preview" aria-selected="${selected}" tabindex="${selected ? 0 : -1}"><span>${projects[id].label}</span>${projects[id].title}</button>`;
  }).join('');
  const bodies = [
    `<p data-experiment-ink>${content.C1.body}</p><ol class="experiment-process" data-experiment-ink aria-label="从想法到交互">${content.C1.steps.map((s) => `<li>${s}</li>`).join('')}</ol>`,
    `<section class="experiment-window-stage" aria-label="${project.title}场景窗口" tabindex="-1">
      <img class="experiment-scene-cover" width="${project.cover.width}" height="${project.cover.height}" alt="${project.cover.alt}" decoding="async"/>
      <div class="experiment-scene-mount"></div>
      <div class="experiment-scene-feedback">
        <p class="experiment-scene-status" role="status"></p>
        <button class="experiment-scene-retry" type="button">重新载入场景</button>
      </div>
    </section>
    <div class="experiment-window-footer">
      <p class="experiment-summary" data-experiment-ink>${project.summary}</p>
      <details class="experiment-project-archive" inert>
        <summary aria-label="查看${project.title}项目档案">项目档案 <span aria-hidden="true"></span></summary>
        <div class="experiment-archive-content" tabindex="0"></div>
      </details>
    </div>`,
    `<p data-experiment-ink>${content.C3.body}</p><p class="experiment-cue" data-experiment-ink><span aria-hidden="true">↓</span> ${content.C3.cue}</p>`,
  ];
  const titles = [content.C1.title, project.title, content.C3.title];
  panel.innerHTML = experimentStations.map((s, i) => {
    const showcase = s.id === 'C2';
    const title = `<h2 id="experiment-${s.id}-title">${titles[i]}</h2>`;
    const heading = showcase
      ? `<header class="experiment-window-header">
          <div class="experiment-window-identity"><p class="experiment-eyebrow">交互实验</p>${title}</div>
          <div class="experiment-project-selector" role="tablist" aria-label="选择交互作品">${projectTabs}</div>
        </header>`
      : `<p class="experiment-eyebrow">03 / 交互实验 <span>${s.label}</span></p>${title}`;
    const bodyAttributes = showcase ? ` id="experiment-project-preview" role="tabpanel" aria-labelledby="experiment-project-${firstProject}"` : '';
    return `<article${showcase ? ' class="experiment-project-window"' : ''} data-experiment-station="${s.id}" aria-labelledby="experiment-${s.id}-title" aria-hidden="true" inert hidden>${heading}<div class="experiment-body"${bodyAttributes}>${bodies[i]}</div></article>`;
  }).join('');
  const connector = document.createElementNS('http://www.w3.org/2000/svg', 'svg');connector.classList.add('experiment-reading-link');connector.setAttribute('aria-hidden', 'true');
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');connector.append(line);app.querySelector('main')!.append(connector, panel);
  const parts = [...panel.querySelectorAll<HTMLElement>('article')].map((article) => ({ article, title: article.querySelector<HTMLElement>('h2')!, eyebrow: article.querySelector<HTMLElement>('.experiment-eyebrow')!, body: article.querySelector<HTMLElement>('.experiment-body')!, buttons: [...article.querySelectorAll<HTMLButtonElement>('button')] }));
  const flow = createReaderFlow(panel);
  const stage = panel.querySelector<HTMLElement>('.experiment-window-stage')!;
  const scene = createExperimentScene(stage, firstProject, actions.sceneInput);
  const projectSelector = panel.querySelector<HTMLElement>('.experiment-project-selector')!;
  const projectButtons = [...projectSelector.querySelectorAll<HTMLButtonElement>('button')];
  const archive = panel.querySelector<HTMLDetailsElement>('.experiment-project-archive')!;
  const archiveToggle = archive.querySelector<HTMLElement>('summary')!;
  const archiveContent = archive.querySelector<HTMLElement>('.experiment-archive-content')!;
  const controller = new AbortController(), options = { signal: controller.signal };
  let fallback = false, disposed = false, dirty = true, selected = '', signature = '';
  let inFlow = false, immersiveReady = false, covered = false;
  let layoutFrame: number | undefined, sceneFrame: number | undefined;
  let reading: ExperimentReadingFrame | undefined, camera: Camera | undefined;
  const siteHeader = app.querySelector('.tour-header')!, siteFooter = app.querySelector('.tour-footer')!;
  const chapterHeading = app.querySelector('.tour-heading')!, navigation = app.querySelector('.tour-stops')!;
  let bounds = host.getBoundingClientRect(), header = siteHeader.getBoundingClientRect(), footer = siteFooter.getBoundingClientRect();
  let heading = chapterHeading.getBoundingClientRect(), nav = navigation.getBoundingClientRect();
  let width = 0, height = 0;
  const point = new Vector3();
  const available = () => !covered && (inFlow || fallback || immersiveReady);
  function reconcileScene() {
    if (disposed || document.hidden || sceneFrame !== undefined) return;
    // Read the final layout and selection after any changes in this frame.
    sceneFrame = requestAnimationFrame(() => {
      sceneFrame = undefined;
      if (document.hidden) return;
      const interactive = available();
      archive.inert = !interactive;
      if (!interactive) archive.open = false;
      const rect = stage.getBoundingClientRect();
      const visibleTop = Math.max(0, rect.top, siteHeader.getBoundingClientRect().bottom);
      const visibleHeight = Math.min(rect.bottom, innerHeight) - visibleTop;
      scene.setActive(interactive && rect.width > 0 && visibleHeight > 1);
    });
  }
  function syncButtons() {
    const active = fallback || flow.active || (reading?.station.id === 'C2' && sampleExperimentPresentation(reading).body >= .999999);
    for (const button of projectButtons) {
      button.disabled = !active;
      const current = button.dataset.projectSelect === scene.projectId;
      button.setAttribute('aria-selected', String(current));button.tabIndex = current ? 0 : -1;
    }
  }
  function choose(id: EmbeddedProjectId) {
    if (id === scene.projectId) return;
    const item = projects[id];
    archive.open = false;scene.select(id);
    panel.dataset.projectId = id;
    panel.querySelector('#experiment-C2-title')!.textContent = item.title;
    panel.querySelector('.experiment-summary')!.textContent = item.summary;
    panel.querySelector('#experiment-project-preview')!.setAttribute('aria-labelledby', `experiment-project-${id}`);
    archiveToggle.setAttribute('aria-label', `查看${item.title}项目档案`);
    signature = '';dirty = true;syncButtons();measure();place();reconcileScene();actions.projectChanged();
  }
  projectSelector.addEventListener('click', event => {
    const button = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('[data-project-select]') : null;
    const id = experimentProjectOrder.find(id => id === button?.dataset.projectSelect);
    if (id && !button?.disabled) choose(id);
  }, options);
  archive.addEventListener('toggle', () => {
    const { projectId } = scene;
    if (archive.open && archiveContent.dataset.projectId !== projectId) {
      const item = projects[projectId];
      archiveContent.dataset.projectId = projectId;
      archiveContent.innerHTML = `<div class="experiment-archive-intro"><div><p class="experiment-eyebrow">${item.archive.kicker}</p><h3>${item.archive.headline.join('<br>')}</h3></div><p>${item.introduction}</p></div>
        <figure><img src="${item.cover.src}" width="${item.cover.width}" height="${item.cover.height}" alt="${item.cover.alt}" decoding="async"/><figcaption>${item.archive.caption}</figcaption></figure>
        <div class="experiment-archive-features">${item.features.map(feature => `<section><h4>${feature.title}</h4><p>${feature.body}</p></section>`).join('')}</div>`;
    }
    if (inFlow) actions.archiveLayoutChanged();
  }, options);
  archive.addEventListener('keydown', event => {
    if (event.key === 'Escape' && archive.open) {
      event.preventDefault();archive.open = false;archiveToggle.focus({ preventScroll: true });
    }
  }, options);
  projectSelector.addEventListener('keydown', event => {
    const e = event as KeyboardEvent;if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const current = experimentProjectOrder.indexOf(scene.projectId);
    const next = (current + (e.key === 'ArrowLeft' ? -1 : 1) + experimentProjectOrder.length) % experimentProjectOrder.length;
    const id = e.key === 'Home' ? firstProject : e.key === 'End' ? experimentProjectOrder[experimentProjectOrder.length - 1]! : experimentProjectOrder[next]!;
    choose(id);panel.querySelector<HTMLButtonElement>(`[data-project-select="${id}"]`)!.focus({ preventScroll: true });
  }, options);
  panel.dataset.projectId = scene.projectId;
  function measure() {
    if (flow.active) return;
    bounds = host.getBoundingClientRect();header = siteHeader.getBoundingClientRect();footer = siteFooter.getBoundingClientRect();
    heading = chapterHeading.getBoundingClientRect();nav = navigation.getBoundingClientRect();
    connector.setAttribute('viewBox', `0 0 ${innerWidth} ${innerHeight}`);dirty = true;signature = '';
  }
  function placeProjectWindow(stacked: boolean) {
    const left = Math.ceil(Math.max(0, bounds.left) + 24);
    const right = Math.floor(Math.min(innerWidth, bounds.right, stacked ? Infinity : nav.left) - 24);
    const top = Math.ceil(Math.max(bounds.top, header.bottom) + 16);
    const bottom = Math.floor(Math.min(bounds.bottom, footer.top, stacked ? nav.top : Infinity) - 16);
    const windowWidth = Math.max(1, Math.min(1308, right - left));
    panel.dataset.layout = 'showcase';
    panel.style.width = `${windowWidth}px`;
    const controlsHeight = panel.getBoundingClientRect().height - stage.getBoundingClientRect().height;
    const stageHeight = Math.max(0, Math.min(660, Math.floor(bottom - top - controlsHeight)));
    panel.style.setProperty('--experiment-stage-height', `${stageHeight}px`);
    panel.style.left = `${left + Math.floor((right - left - windowWidth) / 2)}px`;
    panel.style.top = `${top + Math.max(0, Math.floor((bottom - top - controlsHeight - stageHeight) / 2))}px`;
    const fits = windowWidth >= 320 && stageHeight >= 320;
    panel.dataset.anchorClear = String(fits);
    panel.dataset.fits = String(fits);
    delete panel.dataset.anchorX;delete panel.dataset.anchorY;
    dirty = false;
  }
  function place() {
    if (!reading || !camera || fallback || flow.active) return;
    const stacked = innerWidth <= 1000;
    if (reading.station.id === 'C2') {
      if (dirty) placeProjectWindow(stacked);
      return;
    }
    point.copy(anchorFor(reading.station.id) ?? new Vector3(2.96, reading.station.y, 5.09)).project(camera);
    const x = bounds.left + (point.x + 1) * bounds.width / 2, y = bounds.top + (1 - point.y) * bounds.height / 2;
    const right = stacked ? innerWidth - 16 : nav.left - 24;
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
    layoutFrame = requestAnimationFrame(() => { layoutFrame = undefined;if (!disposed) { measure();place();reconcileScene(); } });
  });
  for (const el of [host, panel, chapterHeading, siteHeader, siteFooter, navigation]) observer.observe(el);
  const visibility = new IntersectionObserver(reconcileScene);visibility.observe(stage);
  document.addEventListener('visibilitychange', reconcileScene, options);
  window.addEventListener('pageshow', reconcileScene, options);
  window.addEventListener('scroll', () => { if (inFlow || fallback) reconcileScene(); }, { ...options, passive: true });
  window.addEventListener('resize', reconcileScene, { ...options, passive: true });
  measure();
  return {
    prime: scene.prime,
    update(next: ExperimentReadingFrame | undefined, nextCamera: Camera, reduced = false, measuring = false) {
      reading = next;camera = nextCamera;
      const state = sampleExperimentPresentation(reading, reduced);
      if (!measuring) {
        const ready = reading?.station.id === 'C2' && state.body >= .999999;
        if (ready !== immersiveReady) { immersiveReady = ready;reconcileScene(); }
      }
      if (fallback || flow.active) return state;
      panel.dataset.progress = (reading?.progress ?? 0).toFixed(7);
      const nextSignature = `${reading?.station.id}|${reading?.phase}|${state.frame}|${state.title}|${state.body}|${state.offset}|${camera.position.toArray()}|${camera.projectionMatrix.elements[0]}`;
      if (signature === nextSignature && !dirty) return state;signature = nextSignature;
      if (selected !== (reading?.station.id ?? '')) { selected = reading?.station.id ?? '';dirty = true;for (const part of parts) part.article.hidden = part.article.dataset.experimentStation !== selected; }
      const visible = !!reading && state.frame > .000001;
      panel.dataset.visible = String(visible);panel.dataset.station = selected;panel.dataset.phase = reading?.phase ?? 'off';panel.dataset.titleOpacity = state.title.toFixed(7);panel.dataset.bodyOpacity = state.body.toFixed(7);
      panel.style.visibility = visible ? 'visible' : 'hidden';panel.setAttribute('aria-hidden', String(!visible));panel.style.setProperty('--experiment-frame-opacity', String(state.frame));connector.style.opacity = String(selected === 'C2' ? 0 : state.title * .6);
      projectSelector.style.opacity = String(selected === 'C2' ? state.title : 0);
      for (const { article, title, eyebrow, body, buttons } of parts) {
        const active = visible && article.dataset.experimentStation === selected;
        article.inert = !active;article.setAttribute('aria-hidden', String(!active));
        for (const element of [title, eyebrow]) { element.style.opacity = String(active ? state.title : 0);element.setAttribute('aria-hidden', String(!active || state.title <= .000001)); }
        body.style.opacity = String(active ? state.body : 0);body.style.visibility = active && state.body > .000001 ? 'inherit' : 'hidden';body.style.transform = `translateY(${state.offset}px)`;body.setAttribute('aria-hidden', String(!active || state.body <= .000001));
        for (const button of buttons) button.disabled = !active || state.body < .999999;
      }
      syncButtons();
      if (reading) { if (reading.station.id === 'C2' && !measuring) scene.prime();place(); }
      return state;
    },
    showFallback() {
      fallback = true;scene.prime();panel.classList.add('experiment-fallback');panel.style.visibility = 'visible';panel.setAttribute('aria-hidden', 'false');panel.style.setProperty('--experiment-frame-opacity', '1');connector.style.display = 'none';
      projectSelector.style.opacity = '1';
      for (const part of parts) {
        part.article.hidden = false;part.article.inert = false;part.article.setAttribute('aria-hidden', 'false');
        for (const element of [part.title, part.eyebrow, part.body]) { element.style.opacity = '1';element.style.visibility = 'visible';element.removeAttribute('aria-hidden');element.style.transform = 'none'; }
      }
      syncButtons();reconcileScene();
    },
    setFlow(enabled: boolean, measuring = false) {
      flow.set(enabled);
      if (enabled) projectSelector.style.opacity = '1';
      signature = '';dirty = true;syncButtons();
      if (!enabled) measure();
      if (!measuring) { inFlow = enabled;reconcileScene(); }
      archive.inert = !available();
    },
    setCovered(value: boolean) { covered = value;reconcileScene(); },
    get element() { return panel; },
    dispose() {
      disposed = true;
      if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);
      if (sceneFrame !== undefined) cancelAnimationFrame(sceneFrame);
      controller.abort();scene.dispose();observer.disconnect();visibility.disconnect();panel.remove();connector.remove();
    },
  };
}
