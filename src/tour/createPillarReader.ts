import { Vector3 } from 'three';
import type { Camera } from 'three';
import type { PillarReadingFrame } from './reading';
import { sampleMagic } from './magicStyle';
import { createAboutView } from './about-refresh/createAboutView';
import type { AboutStationId } from './about-refresh/types';
import './about-refresh/host.css';

interface AboutHost {
  interaction(): void;
  layoutChanged(): void;
  continue(): void;
  overview(open: boolean): void;
  entranceChanged(): void;
}

/** One About instance, shared by projected reading, document flow and overview. */
export function createPillarReader(app: HTMLElement, host: HTMLElement, inscriptionAnchor?: (id: string) => Vector3 | undefined, lifecycle?: AboutHost) {
  const main = app.querySelector<HTMLElement>('main')!;
  const header = app.querySelector<HTMLElement>('.tour-header')!;
  const heading = app.querySelector<HTMLElement>('.tour-heading')!;
  const nav = app.querySelector<HTMLElement>('.tour-stops')!;
  const footer = app.querySelector<HTMLElement>('.tour-footer')!;
  let flow = false, disposed = false, overview = false;
  let lastReading: PillarReadingFrame | undefined;
  let lastCamera: Camera | undefined;
  let layoutFrame: number | undefined;
  let modalTrigger: HTMLElement | undefined;
  const events = new AbortController();
  const dialog = document.createElement('dialog');
  dialog.className = 'ar-overview-dialog';
  const shell = document.createElement('div');shell.className = 'about-refresh ar-overview-shell';shell.dataset.layout = 'stable';
  dialog.append(shell);app.append(dialog);
  const view = createAboutView(main, {
    onInteraction: () => lifecycle?.interaction(),
    onLayoutChange: () => { if (!disposed) lifecycle?.layoutChanged(); },
    onContinue: () => lifecycle?.continue(),
    onEntranceChange: () => lifecycle?.entranceChanged(),
    onToolModeChange: mode => {
      if (mode === 'all' && !flow) openOverview();
      else if (mode === 'cards' && overview) closeOverview();
    },
  });
  const panel = view.root;
  panel.classList.add('about-pillar-reader');
  panel.dataset.visible = 'false';panel.inert = true;panel.setAttribute('aria-hidden', 'true');
  for (const section of view.stations) {
    const id = section.dataset.aboutStation!;
    section.dataset.readingStation = id;section.dataset.flowAnchor = id;
    const title = section.querySelector('h2')!;title.id = `reading-${id}-title`;
    section.setAttribute('aria-labelledby', title.id);
  }
  const point = new Vector3();

  function openOverview() {
    if (disposed || overview) return;
    modalTrigger = panel.querySelector<HTMLElement>('[data-action="all"]') ?? undefined;
    overview = true;lifecycle?.overview(true);
    view.mountToolsInto(shell);
    dialog.setAttribute('aria-labelledby', shell.querySelector('h3')!.id);
    shell.dataset.largeText = panel.dataset.largeText;
    document.documentElement.classList.add('tour-about-open');
    dialog.showModal();
    shell.querySelector<HTMLElement>('[data-action="return"]')?.focus({ preventScroll: true });
  }
  function closeOverview() {
    if (!overview) return;
    overview = false;view.mountToolsInto();
    if (dialog.open) dialog.close();
    document.documentElement.classList.remove('tour-about-open');
    lifecycle?.overview(false);
    if (!disposed) {
      modalTrigger?.focus({ preventScroll: true });
      lifecycle?.layoutChanged();
    }
    modalTrigger = undefined;
  }
  dialog.addEventListener('cancel', event => { event.preventDefault();view.closeToolOverview(); }, { signal: events.signal });
  dialog.addEventListener('close', () => { if (overview && !dialog.open) { view.closeToolOverview();closeOverview(); } }, { signal: events.signal });

  function place(reading: PillarReadingFrame, camera: Camera) {
    const bounds = host.getBoundingClientRect();
    const navBox = nav.getBoundingClientRect();
    const stacked = innerWidth <= 1000;
    const wide = reading.station.id === 'A3';
    const topLimit = Math.max(header.getBoundingClientRect().bottom,
      !wide && getComputedStyle(heading).visibility !== 'hidden' && Number(heading.dataset.opacity) > .01 ? heading.getBoundingClientRect().bottom : 0) + 16;
    const bottomLimit = Math.min(bounds.bottom, footer.getBoundingClientRect().top, stacked ? navBox.top : Infinity) - 16;
    const rightLimit = stacked ? innerWidth - 16 : navBox.left - 16;
    const availableWidth = Math.max(1, rightLimit - 16);
    const width = Math.min(wide ? innerWidth >= 1700 ? 1100 : 1080 : 480, availableWidth);
    panel.style.width = `${width}px`;
    panel.dataset.largeText = String(parseFloat(getComputedStyle(panel).fontSize) > 24);
    view.setLayout('immersive', 0);
    const height = panel.getBoundingClientRect().height;
    const anchor = inscriptionAnchor?.(reading.station.id);
    if (anchor) point.copy(anchor);else point.set(-2.34, reading.station.y, -2.9);
    point.project(camera);
    const x = bounds.left + (point.x + 1) * bounds.width / 2;
    const y = bounds.top + (1 - point.y) * bounds.height / 2;
    const left = wide ? 16 + (availableWidth - width) / 2 : Math.max(16, Math.min(stacked ? x - width / 2 : x + bounds.width * .06, rightLimit - width));
    const top = Math.max(topLimit, Math.min(wide ? topLimit + (bottomLimit - topLimit - height) / 2 : stacked ? y + 48 : y - height / 2, bottomLimit - height));
    panel.style.left = `${left}px`;panel.style.top = `${top}px`;
    const anchorClear = wide || (stacked ? top >= y + 32 : left >= x + 40);
    panel.dataset.anchorClear = String(anchorClear);
    panel.dataset.anchorX = x.toFixed(4);panel.dataset.anchorY = y.toFixed(4);
    panel.dataset.fits = String(width <= availableWidth && height <= bottomLimit - topLimit && anchorClear && (!wide || width >= 900));
    panel.dataset.safeBounds = JSON.stringify([16,topLimit,rightLimit,bottomLimit]);
  }

  function syncStableEntrance() {
    if (disposed || !flow || overview || document.hidden || main.dataset.readingMode !== 'stable') return;
    const section = view.stations.find(node => node.dataset.aboutStation === 'A3')!;
    const box = section.getBoundingClientRect();
    view.presentToolsEntrance({ active: box.top < innerHeight * .75 && box.bottom > innerHeight * .25, enabled: false, revealed: true });
    view.presentToolsTrack({ active: box.top < innerHeight * .75 && box.bottom > innerHeight * .25,
      allowed: innerWidth >= 1180 && panel.dataset.largeText !== 'true', automatic: false,
      top: header.getBoundingClientRect().bottom + 12, bottom: innerHeight - 16 });
  }
  function update(reading: PillarReadingFrame | undefined, camera: Camera, reducedMotion = false, measuring = false) {
    if (!measuring) { lastReading = reading;lastCamera = camera; }
    const state = sampleMagic(reading, reducedMotion);
    const departureContext = () => ({
      active: !flow && !overview && reading?.station.id === 'A3',
      enabled: !flow && !overview && !reducedMotion && innerWidth >= 1180 && panel.dataset.largeText !== 'true' && main.dataset.layoutReady === 'true' && panel.dataset.fits === 'true',
      progress: reading?.station.id === 'A3' ? reading.progress : 0,
      readable: reading?.station.id === 'A3' && reading.phase === 'read' && state.body >= .999 && state.title >= .999 && host.dataset.cameraState === 'settled',
    });
    // Capture the current card geometry before the host fades or hides A3.
    if (!measuring) view.presentToolsDeparture(departureContext());
    if (flow || overview) {
      if (!measuring) syncStableEntrance();
      return state;
    }
    const visible = !!reading && state.veil > .000001;
    if (reading && view.station !== reading.station.id) view.setStation(reading.station.id, measuring);
    panel.dataset.visible = String(visible);panel.dataset.phase = reading?.phase ?? 'off';
    panel.dataset.opacity = state.body.toFixed(7);panel.dataset.titleOpacity = state.title.toFixed(7);
    panel.dataset.progress = (reading?.progress ?? 0).toFixed(7);
    panel.style.visibility = visible ? 'visible' : 'hidden';
    panel.style.setProperty('--ar-body-opacity', String(state.body));
    panel.style.setProperty('--ar-title-opacity', String(state.title));
    panel.inert = !visible || state.body < .999;
    panel.setAttribute('aria-hidden', String(!visible));
    if (!measuring) {
      main.dataset.aboutStation = reading?.station.id ?? '';
      if (reading?.station.id === 'A3') heading.setAttribute('aria-hidden','true');
    }
    if (reading) place(reading,camera);
    // A station arriving from A2 may only acquire real dimensions after place().
    if (!measuring) view.presentToolsDeparture(departureContext());
    if (!measuring) view.presentToolsEntrance({
      active: reading?.station.id === 'A3' && reading.phase !== 'leave',
      enabled: !reducedMotion && panel.dataset.largeText !== 'true' && innerWidth >= 1180 && panel.dataset.fits === 'true',
      revealed: state.body >= .999 && state.title >= .999 && reading?.phase === 'read' && host.dataset.cameraState === 'settled' && main.dataset.layoutReady === 'true',
    });
    if (!measuring) view.presentToolsTrack({
      active: reading?.station.id === 'A3' && reading.phase === 'read' && state.body >= .999 && state.title >= .999 && host.dataset.cameraState === 'settled' && !overview,
      allowed: !reducedMotion && panel.dataset.largeText !== 'true' && innerWidth >= 1180,
      automatic: true, top: header.getBoundingClientRect().bottom + 12, bottom: footer.getBoundingClientRect().top - 12,
    });
    return state;
  }
  function setFlow(enabled: boolean, measuring = false) {
    if (!measuring) view.cancelToolsHelp('reading-mode');
    if (!measuring) view.cancelToolsDeparture('reading-mode');
    if (enabled && !measuring) view.cancelToolsEntrance('reading-mode');
    flow = enabled;
    view.setContinuous(enabled, true);
    if (enabled) {
      panel.dataset.readingLayout = 'flow';panel.dataset.visible = 'true';panel.inert = false;panel.setAttribute('aria-hidden','false');
      view.setLayout('stable');panel.dataset.largeText = String(parseFloat(getComputedStyle(panel).fontSize)>24);
      if (!measuring) syncStableEntrance();
    } else {
      delete panel.dataset.readingLayout;
      if (!measuring && lastCamera) update(lastReading,lastCamera);
    }
  }
  const observer = new ResizeObserver(() => {
    if (disposed || flow || overview || layoutFrame !== undefined) return;
    layoutFrame = requestAnimationFrame(() => { layoutFrame = undefined;if (!disposed && !flow && !overview && lastReading && lastCamera) place(lastReading,lastCamera); });
  });
  for (const element of [panel,host,header,nav,footer]) observer.observe(element);
  // Native flow scrolling can occur while the environment/render loop is paused.
  const stableEntranceObserver = new IntersectionObserver(syncStableEntrance, { threshold: [0,.1,.25,.5,.75,1] });
  stableEntranceObserver.observe(view.stations.find(node => node.dataset.aboutStation === 'A3')!);
  return {
    update,setFlow,
    get element() { return panel; },
    get station() { return view.station; },
    get entranceReady() { return view.toolsEntranceReady; },
    restoreStation(id: AboutStationId) { view.setStation(id,true); },
    cancelToolsDeparture(reason: string) { view.cancelToolsDeparture(reason); },
    readingText() {
      const section = view.stations.find(node=>node.dataset.aboutStation===view.station)!;
      if (view.station !== 'A3') return section.innerText;
      const rail = view.toolsElement.querySelector<HTMLElement>('.ar-tool-rail')!;
      const bounds = rail.getBoundingClientRect();
      return [section.querySelector('.ar-tools-header')!.textContent,
        ...[...rail.querySelectorAll<HTMLElement>('.ar-tool-card')].filter(card=>{const r=card.getBoundingClientRect();return r.left>=bounds.left&&r.right<=bounds.right;}).map(card=>card.querySelector<HTMLElement>('.ar-card-front')?.innerText ?? card.innerText)].join('\n');
    },
    closeOverview() { if (overview) view.closeToolOverview(); },
    dispose() {
      if (disposed) return;
      disposed = true;events.abort();closeOverview();observer.disconnect();stableEntranceObserver.disconnect();
      if (layoutFrame!==undefined) cancelAnimationFrame(layoutFrame);
      view.dispose();dialog.remove();document.documentElement.classList.remove('tour-about-open');
    },
  };
}
