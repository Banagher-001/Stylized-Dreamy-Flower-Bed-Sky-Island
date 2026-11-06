import { Vector3 } from 'three';
import type { Camera } from 'three';
import { readingStations } from './reading';
import type { PillarReadingFrame } from './reading';
import { sampleMagic } from './magicStyle';
import { aboutContent } from './aboutContent';
import { createReaderFlow } from './readerFlow';

function renderAboutBody(content: (typeof aboutContent)[keyof typeof aboutContent]) {
  switch (content.kind) {
    case 'identity': return `<p class="about-name" data-reading-ink>${content.name}</p><p class="about-role" data-reading-ink>${content.role}</p><p class="about-note" data-reading-ink>${content.note}</p>`;
    case 'experience': return `<ol class="about-experience" role="list">${content.entries.map((entry) => `<li><p class="about-when" data-reading-ink>${entry.label} <span lang="en">${entry.english}</span></p><p class="about-company" data-reading-ink>${entry.company}</p>${'role' in entry ? `<p class="about-duty" data-reading-ink>${entry.role}</p>` : ''}</li>`).join('')}</ol>`;
    case 'practice': return `<ul class="about-practice" role="list">${content.directions.map((direction) => `<li><span class="about-practice-name" data-reading-ink>${direction.name}</span><span data-reading-ink>${direction.detail}</span></li>`).join('')}</ul><p class="about-cue" data-reading-ink><span aria-hidden="true">↓</span> ${content.cue}</p>`;
  }
}

/** Clear DOM text, projected from the pillar; no second animation clock. */
export function createPillarReader(app: HTMLElement, host: HTMLElement, inscriptionAnchor?: (id: string) => Vector3 | undefined) {
  const panel = document.createElement('section');
  panel.className = 'pillar-reading';
  panel.setAttribute('aria-label', '关于我，沿石柱阅读');
  panel.setAttribute('aria-hidden', 'true');
  panel.dataset.visible = 'false';
  panel.innerHTML = readingStations.map((station) => {
    const content = aboutContent[station.id];
    return `<article data-reading-station="${station.id}" data-reading-layout="${content.kind}" aria-labelledby="reading-${station.id}-title" aria-hidden="true" inert><p class="pillar-reading-eyebrow">01 / 关于我 <span>${content.label}</span></p><h2 id="reading-${station.id}-title">${content.title}</h2><div class="pillar-reading-body">${renderAboutBody(content)}</div></article>`;
  }).join('');
  const connector = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  connector.classList.add('pillar-reading-link');
  connector.setAttribute('aria-hidden', 'true');
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  connector.append(line);
  app.querySelector('main')!.append(connector, panel);
  const articles = [...panel.querySelectorAll<HTMLElement>('[data-reading-station]')];
  const flow = createReaderFlow(panel);
  const point = new Vector3();
  const header = app.querySelector<HTMLElement>('.tour-header')!;
  const heading = app.querySelector<HTMLElement>('.tour-heading')!;
  const nav = app.querySelector<HTMLElement>('.tour-stops')!;
  let bounds = host.getBoundingClientRect();
  let panelWidth = 0;
  let panelHeight = 0;
  let headingBottom = 0;
  let navBounds = nav.getBoundingClientRect();
  let lastReading: PillarReadingFrame | undefined;
  let lastCamera: Camera | undefined;
  let disposed = false;
  let lastSignature = '';
  let layoutFrame: number | undefined;

  function measure() {
    if (flow.active) return;
    lastSignature = '';
    bounds = host.getBoundingClientRect();
    const box = panel.getBoundingClientRect();
    panelWidth = box.width;
    panelHeight = box.height;
    headingBottom = Math.max(header.getBoundingClientRect().bottom, heading.getBoundingClientRect().bottom);
    navBounds = nav.getBoundingClientRect();
    connector.setAttribute('viewBox', `0 0 ${window.innerWidth} ${window.innerHeight}`);
  }

  function place(reading: PillarReadingFrame, camera: Camera) {
    if (flow.active) return;
    const anchor = inscriptionAnchor?.(reading.station.id);
    if (anchor) point.copy(anchor);else point.set(-2.34, reading.station.y, -2.9);
    point.project(camera);
    const x = bounds.left + (point.x + 1) * bounds.width / 2;
    const y = bounds.top + (1 - point.y) * bounds.height / 2;
    const stacked = window.innerWidth <= 1000;
    const minTop = headingBottom + 18;
    const bottom = stacked ? Math.min(bounds.bottom - 16, navBounds.top - 16) : bounds.bottom - 20;
    const maxTop = bottom - panelHeight;
    const top = Math.max(minTop, Math.min(stacked ? y + 60 : y - panelHeight / 2, maxTop));
    const right = stacked ? window.innerWidth - 16 : navBounds.left - 24;
    const left = Math.max(16, Math.min(stacked ? x - panelWidth / 2 : x + bounds.width * 0.085, right - panelWidth));
    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
    panel.dataset.anchorX = x.toFixed(4);
    panel.dataset.anchorY = y.toFixed(4);
    panel.dataset.layout = stacked ? 'stacked' : 'side';
    const anchorClear = stacked ? top >= y + 40 : left >= x + 60;
    panel.dataset.anchorClear = String(anchorClear);
    panel.dataset.fits = String(panelWidth <= right - 16 && maxTop >= minTop && anchorClear);
    const sx = Math.round(x), sy = Math.round(y), sl = Math.round(left), st = Math.round(top), mid = Math.round(top + panelHeight / 2);
    line.setAttribute('d', stacked ? `M ${sx} ${sy + 28} Q ${sx} ${st - 16} ${Math.round(left + panelWidth / 2)} ${st - 10}` : `M ${sx + 38} ${sy} C ${sl - 28} ${sy}, ${sl - 36} ${mid}, ${sl - 10} ${mid}`);
  }

  function update(reading: PillarReadingFrame | undefined, camera: Camera, reducedMotion = false) {
    lastReading = reading;
    lastCamera = camera;
    const state = sampleMagic(reading, reducedMotion);
    if (flow.active) return state;
    const progress = (reading?.progress ?? 0).toFixed(7);
    if (panel.dataset.progress !== progress) panel.dataset.progress = progress;
    const signature = `${reading?.station.id}|${reading?.phase}|${state.title}|${state.body}|${state.glyph}|${state.titleY}|${state.bodyY}|${reducedMotion}|${camera.position.x}|${camera.position.y}|${camera.position.z}|${camera.projectionMatrix.elements[0]}`;
    if (signature === lastSignature) return state;
    lastSignature = signature;
    const visible = !!reading && state.veil > 0.000001;
    panel.dataset.visible = String(visible);
    panel.dataset.station = reading?.station.id ?? '';
    panel.dataset.phase = reading?.phase ?? 'off';
    panel.dataset.progress = (reading?.progress ?? 0).toFixed(7);
    panel.dataset.opacity = state.body.toFixed(7);
    panel.dataset.titleOpacity = state.title.toFixed(7);
    panel.dataset.glyphOpacity = state.glyph.toFixed(7);
    panel.style.opacity = '1';
    panel.style.setProperty('--veil-opacity', String(state.veil));
    panel.style.visibility = visible ? 'visible' : 'hidden';
    panel.setAttribute('aria-hidden', String(!visible));
    connector.style.opacity = visible ? String(state.title * .65) : '0';
    for (const article of articles) {
      const selected = visible && article.dataset.readingStation === reading?.station.id;
      article.style.visibility = selected ? 'inherit' : 'hidden';
      article.setAttribute('aria-hidden', String(!selected));
      article.inert = !selected;
      const title = article.querySelector<HTMLElement>('h2')!;
      const eyebrow = article.querySelector<HTMLElement>('.pillar-reading-eyebrow')!;
      const body = article.querySelector<HTMLElement>('.pillar-reading-body')!;
      for (const element of [title, eyebrow]) element.style.opacity = String(selected ? state.title : 0);
      title.style.transform = `translateY(${state.titleY}px)`;
      body.style.opacity = String(selected ? state.body : 0);
      body.style.transform = `translateY(${state.bodyY}px)`;
      body.style.visibility = selected && state.body > .000001 ? 'inherit' : 'hidden';
      body.setAttribute('aria-hidden', String(!selected || state.body <= .000001));
      body.style.maskImage = reducedMotion || state.body === 1 ? 'none' : `linear-gradient(to right, #000 ${state.body * 112 - 12}%, transparent ${state.body * 112}%)`;
    }
    if (reading) place(reading, camera);
    return state;
  }

  const observer = new ResizeObserver(() => {
    if (disposed || flow.active || layoutFrame !== undefined) return;
    layoutFrame = requestAnimationFrame(() => {
      layoutFrame = undefined;if (disposed || flow.active) return;
      measure();if (lastReading && lastCamera) place(lastReading, lastCamera);
    });
  });
  for (const element of [panel, host, header, heading, nav]) observer.observe(element);
  measure();
  return {
    update,
    setFlow(enabled: boolean) { flow.set(enabled);lastSignature = '';if (!enabled) measure(); },
    get element() { return panel; },
    dispose() { disposed = true;if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);observer.disconnect();panel.remove();connector.remove(); },
  };
}
