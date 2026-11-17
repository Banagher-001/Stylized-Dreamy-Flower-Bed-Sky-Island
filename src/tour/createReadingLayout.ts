import { readingStations } from './reading';
import { filmStations } from './filmReading';
import { experimentStations } from './experimentReading';
import { sampleTour, tourTotalH } from './route';
import { chapterLabels } from './presentation';

export interface ReadingCapacity {
  fits: boolean;
  margin: number;
  stations: { id: string; fits: boolean; margin: number; mediaHeight: number | null; bounds: number[]; anchorClear: boolean; projectedFits: boolean }[];
}
export interface ReadingPosition {
  stable: boolean; h: number; y: number; width: number; height: number; viewport: number; font: number;
  anchor: string; ratio: number; top: number; blockHeight: number;
}
interface LayoutBridge {
  h(): number;
  restore(h: number, y?: number): void;
  flow(enabled: boolean): void;
  refresh(): void;
  measure(): ReadingCapacity;
  unavailable(): boolean;
  overlay(): boolean;
  visible(): void;
  live(trigger: HTMLElement): void;
}
const stations = [...readingStations, ...filmStations, ...experimentStations];
const stops = new Map(stations.map(s => [s.id as string, s.stop as number]));
const marks = { overview: 'GARDEN', about: 'ABOUT', films: 'FILM', experiments: 'LAB', water: 'WATER' };
const clamp = (v: number) => Math.max(0, Math.min(1, v));

/** One semantic document, two layouts. No animation loop or second scene. */
export function createReadingLayout(app: HTMLElement, host: HTMLElement, panels: HTMLElement[], bridge: LayoutBridge) {
  const main = app.querySelector<HTMLElement>('main')!;
  const header = app.querySelector<HTMLElement>('.tour-header')!;
  const heading = app.querySelector<HTMLElement>('.tour-heading')!;
  const nav = app.querySelector<HTMLElement>('.tour-stops')!;
  const footer = app.querySelector<HTMLElement>('.tour-footer')!;
  const media = matchMedia('(prefers-reduced-motion: reduce)');
  const listeners = new AbortController(), options = { signal: listeners.signal };
  const surface = document.createElement('div');surface.className = 'tour-reading-flow';
  surface.innerHTML = `<section class="tour-flow-opening" data-flow-anchor="opening"><div class="tour-flow-intro tour-flow-only"><p class="tour-flow-kicker">SAKAN / 张辰翰</p><h1 id="tour-stable-title">让想象，动起来。</h1><p>AI动画 · 视觉创作 · 交互实验</p><p id="tour-layout-note" class="tour-layout-note"></p><a class="tour-flow-start" href="#reading-A1-title">开始阅读 <span aria-hidden="true">↓</span></a></div><div class="tour-cover-slot" aria-label="庭院封面"></div></section>${['关于我', 'AI影像', '交互实验'].map((title, i) => `<section class="tour-flow-chapter" aria-label="${title}"><div class="tour-flow-label tour-flow-only"><span aria-hidden="true">0${i + 1} /</span><p>${title}</p><span class="tour-flow-rune" aria-hidden="true">✧</span></div></section>`).join('')}<section class="tour-flow-water tour-flow-only" data-flow-anchor="water"><p class="tour-flow-kicker">WATER / STILLNESS</p><h2>停一会儿，看风经过。</h2><p>回到庭院，看看水潭与悬浮的水球。</p><button type="button" data-flow-live>进入庭院现场 <span aria-hidden="true">↗</span></button></section><section class="tour-flow-ending tour-flow-only" data-flow-anchor="ending"><p class="tour-flow-kicker">UNTIL THE NEXT IDEA</p><h2>sakan · 张辰翰</h2><p>AI动画 · 视觉创作 · 交互实验</p><div class="tour-flow-ending-actions"><button type="button" data-flow-go="opening">回到开场 <span aria-hidden="true">↑</span></button><button type="button" data-flow-go="B1">回看影像 <span aria-hidden="true">↗</span></button><button type="button" data-reading-toggle>沉浸浏览</button></div></section>`;
  // display:contents in immersive mode preserves the original fixed coordinates.
  surface.querySelector('.tour-cover-slot')!.append(host);
  for (const [i, chapter] of [...surface.querySelectorAll('.tour-flow-chapter')].entries()) chapter.append(panels[i]!);
  for (const panel of panels) for (const article of panel.querySelectorAll<HTMLElement>('[data-reading-station],[data-film-station],[data-experiment-station]')) {
    article.dataset.flowAnchor = article.dataset.readingStation ?? article.dataset.filmStation ?? article.dataset.experimentStation!;
  }
  main.append(surface, footer);
  const skip = document.createElement('a');skip.className = 'tour-skip';skip.href = '#reading-A1-title';skip.textContent = '跳到阅读内容';main.prepend(skip);
  const probe = document.createElement('span');probe.className = 'tour-font-probe';probe.textContent = '庭院';probe.setAttribute('aria-hidden', 'true');main.append(probe);
  const note = surface.querySelector<HTMLElement>('#tour-layout-note')!;
  const toggles = [...main.querySelectorAll<HTMLButtonElement>('[data-reading-toggle]')];
  const anchors = [...surface.querySelectorAll<HTMLElement>('[data-flow-anchor]')];
  const progress = main.querySelector<HTMLProgressElement>('#tour-progress')!;
  const percent = main.querySelector<HTMLElement>('#tour-percent')!;
  const phase = main.querySelector<HTMLElement>('#tour-phase')!;
  const status = main.querySelector<HTMLElement>('#tour-status')!;
  let stable = false, disposed = false, measuring = false, coverVisible = true;
  let capacity: ReadingCapacity = { fits: false, margin: 0, stations: [] };
  let savedImmersive: ReadingPosition | undefined, entryAnchor = '', flowMoved = false;
  let cached: ReadingPosition | undefined, pending: string | undefined;
  let timer: number | undefined, frame: number | undefined, lastKey = '';
  let toolTouching = false, toolScrolling = false, deferredMeasure = false, forcePending = false;
  let toolScrollTimer: number | undefined, lastGeometry = '';
  const fontSize = () => probe.getBoundingClientRect().height;
  const viewportProbe = app.querySelector<HTMLElement>('.tour-viewport-probe')!;
  const stableHeight = () => viewportProbe.getBoundingClientRect().height;
  const layoutChanged = (position: ReadingPosition) => {
    if (position.width !== innerWidth || position.viewport !== stableHeight() || position.font !== fontSize()) return true;
    const r = element(position.anchor).getBoundingClientRect();
    return Math.abs(r.top + scrollY - position.top) > 1 || Math.abs(r.height - position.blockHeight) > 1;
  };
  const safeTop = () => Math.max(0, header.getBoundingClientRect().bottom) + 16;
  const element = (id: string) => anchors.find(e => e.dataset.flowAnchor === id) ?? anchors[0]!;
  function fromH(h: number) {
    const f = sampleTour(h);
    return f.reading?.station.id ?? f.filmReading?.station.id ?? f.experimentReading?.station.id ?? (h < .5 ? 'opening' : h < 1.3 ? 'A1' : h < 4.4 ? 'B1' : h < 8.7 ? 'C1' : h < 11.8 ? 'water' : 'ending');
  }
  function currentAnchor() {
    let result = anchors[0]!;
    for (const node of anchors) { if (node.getBoundingClientRect().top <= safeTop() + 1) result = node;else break; }
    if (scrollY >= document.documentElement.scrollHeight - innerHeight - 1) result = anchors.at(-1)!;
    return result;
  }
  function capture(): ReadingPosition {
    const node = stable ? currentAnchor() : element(fromH(bridge.h()));
    const r = node.getBoundingClientRect();
    return { stable, h: bridge.h(), y: scrollY, width: innerWidth, height: innerHeight, viewport: stableHeight(), font: fontSize(), anchor: node.dataset.flowAnchor!, ratio: stable ? clamp((safeTop() - r.top) / Math.max(1, r.height)) : 0, top: r.top + scrollY, blockHeight: r.height };
  }
  function align(id: string, ratio = 0) {
    const node = element(id), r = node.getBoundingClientRect();
    scrollTo({ top: id === 'opening' && ratio === 0 ? 0 : scrollY + r.top + ratio * r.height - safeTop(), behavior: 'instant' });
  }
  function updateProgress(restored = false) {
    if (!stable || disposed || measuring || bridge.overlay()) return;
    // WebKit may deliver the layout-induced scroll before its resize event.
    // Keep the last reading anchor until that layout has been restored.
    if (!restored && cached?.stable && layoutChanged(cached)) { schedule();return; }
    const node = currentAnchor(), id = node.dataset.flowAnchor!;
    const chapter = id.startsWith('A') ? 'about' : id.startsWith('B') ? 'films' : id.startsWith('C') ? 'experiments' : id === 'water' ? 'water' : 'overview';
    const range = Math.max(1, document.documentElement.scrollHeight - innerHeight), value = clamp(scrollY / range);
    const count = scrollY >= range - 1 ? 100 : Math.min(99, Math.floor(value * 100));
    if (progress.value !== value) progress.value = value;
    const label = `${chapterLabels[chapter]}，${count}%`;
    if (progress.getAttribute('aria-valuetext') !== label) { progress.setAttribute('aria-valuetext', label);percent.textContent = `${count}%`; }
    if (phase.textContent !== marks[chapter]) phase.textContent = marks[chapter];
    const brandNote = main.querySelector('.tour-brand p')!;
    const brandLabel = chapter === 'about' ? '01 / ABOUT' : chapter === 'films' ? '02 / FILMS' : chapter === 'experiments' ? '03 / EXPERIMENTS' : chapter === 'water' ? 'WATER / STILLNESS' : 'CREATIVE COURTYARD';
    if (brandNote.textContent !== brandLabel) brandNote.textContent = brandLabel;
    for (const button of nav.querySelectorAll<HTMLButtonElement>('[data-stop]')) {
      if (button.dataset.stop === chapter) button.setAttribute('aria-current', 'location');else button.removeAttribute('aria-current');
    }
    main.dataset.flowAnchor = id;
    cached = capture();
    if (entryAnchor && id !== entryAnchor) flowMoved = true;
  }
  function visibility() {
    const r = host.getBoundingClientRect();
    const next = r.bottom > 0 && r.top < innerHeight;
    if (coverVisible !== next) { coverVisible = next;bridge.visible(); }
  }
  function availability() {
    const enabled = !bridge.unavailable() && capacity.fits && capacity.margin >= 16;
    for (const button of toggles) {
      button.textContent = stable ? '沉浸浏览' : '稳定阅读';button.disabled = stable && !enabled;
      button.setAttribute('aria-pressed', String(stable));button.setAttribute('aria-describedby', 'tour-layout-note');
      button.title = stable && !enabled ? '当前空间适合稳定阅读，文字与作品保持完整。' : stable ? '开启由滚动控制的镜头移动' : '使用完整、稳定的章节阅读';
    }
    main.dataset.immersiveAvailable = String(enabled);
  }
  function change(next: boolean, reason: string) {
    if (disposed) return;
    if (bridge.overlay()) { if (next) pending = reason;return; }
    if (stable === next) { bridge.flow(stable);availability();return; }
    const selection = getSelection();
    const ranges = selection ? Array.from({ length: selection.rangeCount }, (_, i) => selection.getRangeAt(i).cloneRange()) : [];
    if (next) { savedImmersive = capture();entryAnchor = fromH(bridge.h());flowMoved = false; }
    const destination = stable ? capture() : undefined;
    stable = next;main.dataset.readingMode = next ? 'stable' : 'immersive';main.dataset.layoutReason = reason;
    document.documentElement.classList.toggle('tour-stable-reading', next);
    if (next) surface.querySelector('.tour-flow-opening')!.append(footer);else main.append(footer);
    heading.inert = next;if (next) heading.setAttribute('aria-hidden', 'true');else heading.removeAttribute('aria-hidden');
    bridge.flow(next);
    note.textContent = reason === 'reduced-motion' ? '已按减少动态设置使用稳定阅读。环境动效与滚动运镜可分别选择。' : reason === 'unavailable' ? '图形暂不可用，个人介绍与作品档案仍可完整阅读。' : reason === 'capacity' ? '当前空间使用稳定阅读，保留完整文字与作品。' : '稳定阅读 · 按章节慢慢浏览。';
    availability();bridge.refresh();
    if (next) align(entryAnchor);
    else {
      const original = savedImmersive;
      const h = !flowMoved && original ? original.h : stops.get(destination?.anchor ?? '') ?? (destination?.anchor === 'ending' ? tourTotalH : destination?.anchor === 'water' ? 11.5 : 0);
      const exact = original && !flowMoved && original.width === innerWidth && original.height === innerHeight && original.font === fontSize();
      bridge.restore(h, exact ? original.y : undefined);
    }
    if (selection && ranges.length) { selection.removeAllRanges();for (const range of ranges) if (range.startContainer.isConnected && range.endContainer.isConnected) selection.addRange(range); }
    const focused = document.activeElement;
    if (focused instanceof HTMLElement && focused.closest('[inert],[hidden]')) toggles[0]?.focus({ preventScroll: true });
    updateProgress(true);visibility();cached = capture();
    status.textContent = next ? '已切换为稳定阅读。' : '已开启沉浸浏览，滚动可控制镜头。';
  }
  function key() {
    return JSON.stringify([innerWidth, app.querySelector('.tour-viewport-probe')!.getBoundingClientRect().height, fontSize(), ...panels.map(p => p.textContent)]);
  }
  const geometryKey = () => JSON.stringify([innerWidth, stableHeight(), fontSize()]);
  // Capacity probes temporarily hide the real stations. Doing that during a
  // native gesture detaches its browser scroll chain, even if scrollLeft survives.
  // Content-only probes wait for input to settle; a new viewport/font size still
  // takes priority so orientation and accessibility changes remain responsive.
  const measurementHeld = () => document.hidden || (toolTouching || toolScrolling) && geometryKey() === lastGeometry;
  function settleToolScroll() {
    if (toolScrollTimer !== undefined) clearTimeout(toolScrollTimer);
    toolScrollTimer = window.setTimeout(() => {
      toolScrollTimer = undefined;
      if (toolTouching) return;
      toolScrolling = false;
      if (deferredMeasure) schedule();
    }, 160);
  }
  function schedule(force = false) {
    if (disposed) return;forcePending ||= force;clearTimeout(timer);
    timer = window.setTimeout(() => {
      if (disposed || bridge.overlay()) return;
      if (measurementHeld()) { deferredMeasure = true;return; }
      const next = key();if (!forcePending && next === lastKey) { deferredMeasure = false;return; }
      // One deferred batch; the second frame confirms a stable viewport/font.
      frame = requestAnimationFrame(() => { frame = undefined;if (disposed) return;
        if (measurementHeld()) { deferredMeasure = true;return; }
        if (key() !== next) { schedule();return; }
        document.documentElement.classList.toggle('tour-large-text', fontSize() > 24);
        const previous = cached;
        lastKey = next;lastGeometry = geometryKey();forcePending = deferredMeasure = false;measuring = true;capacity = bridge.measure();measuring = false;
        main.dataset.readingCapacity = JSON.stringify(capacity);main.dataset.layoutReady = 'true';
        availability();
        if (!stable && !capacity.fits) change(true, 'capacity');
        else if (stable) {
          if (previous && layoutChanged(previous)) align(previous.anchor, previous.ratio);
          updateProgress(true);visibility();
        } else bridge.refresh();
      });
    }, 120);
  }
  function go(id: string) {
    if (!stable) return;
    flowMoved = true;align(id);updateProgress(true);
  }
  for (const toggle of toggles) toggle.addEventListener('click', () => change(!stable, 'manual'), options);
  for (const button of surface.querySelectorAll<HTMLButtonElement>('[data-flow-go]')) button.addEventListener('click', () => {
    const id = button.dataset.flowGo!;go(id);
    const title = element(id).querySelector<HTMLElement>('h1,h2');
    if (title) { title.tabIndex = -1;title.focus({ preventScroll: true }); }
  }, options);
  surface.querySelector<HTMLButtonElement>('[data-flow-live]')!.addEventListener('click', e => bridge.live(e.currentTarget as HTMLElement), options);
  const skipToContent = (event: Event) => {
    event.preventDefault();change(true, 'manual');go('A1');const title = main.querySelector<HTMLElement>('#reading-A1-title')!;title.tabIndex = -1;title.focus({ preventScroll: true });
  };
  skip.addEventListener('click', skipToContent, options);surface.querySelector('.tour-flow-start')!.addEventListener('click', skipToContent, options);
  const observer = new IntersectionObserver(visibility);observer.observe(host);
  const onToolRail = (target: EventTarget | null) => target instanceof Element && !!target.closest('.ar-tool-rail');
  document.addEventListener('touchstart', event => { if (onToolRail(event.target)) toolTouching = true; }, { ...options, capture: true, passive: true });
  const endTouch = (event: TouchEvent) => { if (toolTouching && event.touches.length === 0) { toolTouching = false;settleToolScroll(); } };
  document.addEventListener('touchend', endTouch, { ...options, passive: true });
  document.addEventListener('touchcancel', endTouch, { ...options, passive: true });
  document.addEventListener('wheel', event => {
    if (onToolRail(event.target) && !event.ctrlKey && !event.metaKey && !event.altKey) { toolScrolling = true;settleToolScroll(); }
  }, { ...options, capture: true, passive: true });
  document.addEventListener('scroll', event => {
    if (event.target instanceof HTMLElement && event.target.matches('.ar-tool-rail') && event.target.dataset.trackMode !== 'program') { toolScrolling = true;settleToolScroll(); }
  }, { ...options, capture: true, passive: true });
  document.addEventListener('visibilitychange', () => {
    if (toolScrollTimer !== undefined) clearTimeout(toolScrollTimer);toolScrollTimer = undefined;
    toolTouching = toolScrolling = false;
    if (!document.hidden && deferredMeasure) schedule();
  }, options);
  const fontObserver = new ResizeObserver(() => schedule());fontObserver.observe(probe);
  fontObserver.observe(viewportProbe);
  const contentObserver = new MutationObserver(() => schedule());
  for (const panel of panels) contentObserver.observe(panel, { childList: true, characterData: true, subtree: true });
  document.fonts.addEventListener('loadingdone', () => schedule(true), options);
  const reducedChanged = () => { if (media.matches) change(true, 'reduced-motion');schedule(true); };
  media.addEventListener('change', reducedChanged, options);
  main.dataset.readingMode = 'immersive';availability();
  return {
    get stable() { return stable; },
    get coverVisible() { return coverVisible; },
    capture,
    contentChanged() { schedule(true); },
    start() { if (bridge.unavailable()) change(true, 'unavailable');else if (media.matches) change(true, 'reduced-motion');void document.fonts.ready.then(() => { if (!disposed) schedule(true); }); },
    scroll() { updateProgress(); },
    navigate(h: number) { if (!stable) return false;go(fromH(h));return true; },
    unavailable() { change(true, 'unavailable');availability();schedule(true); },
    available() {
      bridge.flow(stable);availability();
      if (!bridge.unavailable() && main.dataset.layoutReason === 'unavailable') note.textContent = '图形连接已恢复，当前阅读位置已保留。';
      schedule(true);
    },
    restore(position: ReadingPosition) {
      const hadPending = !!pending;
      if (pending) { const why = pending;pending = undefined;change(true, why); }
      if (stable && (!hadPending || position.stable)) {
        const exact = position.stable && position.width === innerWidth && position.height === innerHeight && position.font === fontSize();
        if (exact) scrollTo({ top: position.y, behavior: 'instant' });else align(position.anchor, position.ratio);
        updateProgress(true);visibility();
      } else if (!stable) bridge.restore(position.h, position.width === innerWidth && position.height === innerHeight ? position.y : undefined);
      schedule();
    },
    resize() {
      const previous = cached;
      if (stable && previous && layoutChanged(previous) && !bridge.overlay()) { align(previous.anchor, previous.ratio);updateProgress(true);visibility(); }
      schedule();
    },
    dispose() {
      disposed = true;clearTimeout(timer);if (frame !== undefined) cancelAnimationFrame(frame);
      if (toolScrollTimer !== undefined) clearTimeout(toolScrollTimer);
      listeners.abort();observer.disconnect();fontObserver.disconnect();contentObserver.disconnect();
      document.documentElement.classList.remove('tour-stable-reading', 'tour-large-text');
    },
  };
}
