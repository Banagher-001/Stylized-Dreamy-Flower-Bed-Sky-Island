import { createAboutView } from './createAboutView';
import { aboutRefreshContent, initialEntryIds } from './content';
import type { AboutSnapshot, AboutStationId } from './types';
import './preview.css';

const host = document.querySelector<HTMLElement>('#about-refresh-preview')!;
const bar = document.querySelector<HTMLElement>('.ar-preview-bar')!;
const footer = document.querySelector<HTMLElement>('.ar-preview-footer')!;
const status = footer.querySelector<HTMLElement>('[data-preview-layout]')!;
const large = bar.querySelector<HTMLButtonElement>('[data-preview-large]')!;
const media = matchMedia('(prefers-reduced-motion: reduce)');
const listeners = new AbortController();
const events = { signal: listeners.signal };
const originalFontSize = document.documentElement.style.fontSize;
let disposed = false;
let frame: number | undefined;
let interactions = 0;
let view: ReturnType<typeof createAboutView>;

function fit() {
  if (disposed || !view.root.isConnected) return;
  const availableHeight = Math.max(0, innerHeight - bar.getBoundingClientRect().height - footer.getBoundingClientRect().height);
  const largeText = parseFloat(getComputedStyle(document.documentElement).fontSize) > 24;
  view.root.dataset.largeText = String(largeText);
  view.setLayout('immersive', availableHeight);
  const measurement = view.measure();
  const immersive = !largeText && !media.matches && measurement.width >= 1180 && availableHeight >= 600 && measurement.requiredHeight <= availableHeight;
  view.setLayout(immersive ? 'immersive' : 'stable', availableHeight);
  status.textContent = immersive ? '空间适合沉浸排版' : largeText ? '大字 · 稳定阅读' : media.matches ? '减少动态 · 稳定阅读' : '当前空间采用稳定阅读';
  for (const choice of bar.querySelectorAll<HTMLButtonElement>('[data-preview-station]')) {
    choice.setAttribute('aria-pressed', String(choice.dataset.previewStation === view.station));
  }
}

function scheduleFit() {
  if (disposed || frame !== undefined) return;
  frame = requestAnimationFrame(() => { frame = undefined;fit(); });
}

function mount(snapshot?: AboutSnapshot) {
  view?.dispose();
  view = createAboutView(host, { onInteraction: () => interactions++, onLayoutChange: scheduleFit });
  if (snapshot) view.restoreState(snapshot);
  scheduleFit();
}
mount();

bar.addEventListener('click', event => {
  const target = (event.target as Element).closest<HTMLButtonElement>('button');
  if (!target) return;
  if (target.dataset.previewStation) {
    view.setStation(target.dataset.previewStation as AboutStationId);
    scrollTo({ top: 0, behavior: 'instant' });
  } else if (target === large) {
    const enabled = large.getAttribute('aria-pressed') !== 'true';
    large.setAttribute('aria-pressed', String(enabled));
    document.documentElement.style.fontSize = enabled ? '200%' : originalFontSize;
  }
  scheduleFit();
}, events);
addEventListener('resize', scheduleFit, events);
media.addEventListener('change', scheduleFit, events);
document.fonts.addEventListener('loadingdone', scheduleFit, events);
void document.fonts.ready.then(scheduleFit);
const observer = new ResizeObserver(scheduleFit);
observer.observe(bar);observer.observe(footer);

function dispose() {
  if (disposed) return;
  disposed = true;listeners.abort();observer.disconnect();view.dispose();
  if (frame !== undefined) cancelAnimationFrame(frame);
  document.documentElement.style.fontSize = originalFontSize;
}

// Inspection surface belongs only to this development entry, never the main page.
declare global {
  interface Window {
    __aboutRefreshPreview: {
      readonly view: ReturnType<typeof createAboutView>;
      readonly content: typeof aboutRefreshContent;
      readonly initialEntryIds: readonly string[];
      readonly interactions: number;
      remount(snapshot?: AboutSnapshot): void;
      fit(): void;
      dispose(): void;
    };
  }
}
window.__aboutRefreshPreview = {
  get view() { return view; },
  content: aboutRefreshContent, initialEntryIds,
  get interactions() { return interactions; },
  remount: mount, fit, dispose,
};
addEventListener('pagehide', dispose, { once: true });
if (import.meta.hot) import.meta.hot.dispose(dispose);
