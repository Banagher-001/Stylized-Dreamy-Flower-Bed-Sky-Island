import type { EmbeddedProjectState } from './projectContent';

interface LawsonWindow extends Window { __LAWSON__?: { ready?: boolean; error?: unknown } }
interface LawsonExperienceOptions {
  container: HTMLElement;
  entry: string;
  wanted(): boolean;
  status(state: EmbeddedProjectState): void;
}

/** Own one original, unmodified document. Never reuse its API across reloads. */
export function createLawsonExperience(options: LawsonExperienceOptions) {
  let disposed = false, generation = 0;
  let frame: HTMLIFrameElement | undefined, layoutFrame: number | undefined, timer: number | undefined;
  let listeners: AbortController | undefined;
  function unmount() {
    generation++;
    if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);
    layoutFrame = undefined;clearTimeout(timer);timer = undefined;listeners?.abort();listeners = undefined;
    const previous = frame;frame = undefined;
    if (!previous) return;
    try {
      const doc = previous.contentDocument;
      if (doc?.pointerLockElement) doc.exitPointerLock();
      if (document.fullscreenElement === previous) void document.exitFullscreen().catch(() => {});
      else if (doc?.fullscreenElement) void doc.exitFullscreen().catch(() => {});
    } catch { /* Removal still releases an inaccessible or navigating document. */ }
    previous.remove();
  }
  function mount() {
    if (disposed || !options.wanted() || frame || layoutFrame !== undefined) return;
    const token = ++generation;
    options.status('loading');
    // The viewer's open callback precedes showModal. Size the original document
    // only after that synchronous open has completed, and cancel fast exits.
    layoutFrame = requestAnimationFrame(() => {
      layoutFrame = undefined;
      if (disposed || generation !== token || !options.wanted() || !options.container.getClientRects().length) return;
      const item = document.createElement('iframe');frame = item;
      item.title = '罗森便利店 · 完整交互网页';item.allow = 'fullscreen';item.allowFullscreen = true;
      listeners = new AbortController();
      let currentDocument: Document | undefined, documentGeneration = 0;
      let startedAt = performance.now(), state: EmbeddedProjectState = 'loading';
      const owns = () => !disposed && generation === token && frame === item && options.wanted();
      function publish(next: EmbeddedProjectState) { if (owns() && next !== state) { state = next;options.status(next); } }
      function observe() {
        if (!owns()) return;
        clearTimeout(timer);timer = undefined;
        let next: EmbeddedProjectState = performance.now() - startedAt >= 12000 ? 'slow' : 'loading';
        try {
          const doc = item.contentDocument;
          if (doc && doc.URL !== 'about:blank') {
            if (doc !== currentDocument) {
              currentDocument = doc;documentGeneration++;startedAt = performance.now();next = 'loading';
              publish('loading');
            }
            const api = (item.contentWindow as LawsonWindow | null)?.__LAWSON__;
            const fatal = doc.getElementById('fatal');
            const style = fatal ? item.contentWindow!.getComputedStyle(fatal) : undefined;
            const visibleFatal = !!fatal && !!fatal.getClientRects().length && style?.display !== 'none' && style?.visibility !== 'hidden' && style?.opacity !== '0';
            if (visibleFatal || api?.error || doc.body?.dataset.ready === 'error') next = 'error';
            else if (api?.ready === true) next = 'ready';
          }
        } catch { /* No trustworthy signal yet: retain loading/slow and exits. */ }
        publish(next);
        const docToken = documentGeneration;
        const scheduled = window.setTimeout(() => {
          if (!owns() || timer !== scheduled || docToken !== documentGeneration) return;
          timer = undefined;observe();
        }, state === 'ready' ? 500 : 200);
        timer = scheduled;
      }
      item.addEventListener('load', observe, { signal: listeners.signal });
      item.src = options.entry;options.container.append(item);observe();
    });
  }
  return {
    mount,
    retry() { if (!disposed && options.wanted()) { unmount();mount(); } },
    unmount,
    dispose() { if (!disposed) { disposed = true;unmount(); } },
  };
}
