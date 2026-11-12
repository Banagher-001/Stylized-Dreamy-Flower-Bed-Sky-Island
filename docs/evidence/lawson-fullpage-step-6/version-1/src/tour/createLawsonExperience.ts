import type { EmbeddedProjectState } from './projectContent';

interface LawsonWindow extends Window { __LAWSON__?: { ready?: boolean; error?: unknown } }
interface LawsonExperienceOptions {
  container: HTMLElement;
  entry: string;
  wanted(): boolean;
  status(state: EmbeddedProjectState, message?: string): void;
}

/** Own one original, unmodified document. Never reuse its API across reloads. */
export function createLawsonExperience(options: LawsonExperienceOptions) {
  let disposed = false, generation = 0;
  let frame: HTMLIFrameElement | undefined, layoutFrame: number | undefined, timer: number | undefined;
  let listeners: AbortController | undefined;
  let documentListeners: AbortController | undefined;
  function unmount() {
    generation++;
    if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);
    layoutFrame = undefined;clearTimeout(timer);timer = undefined;listeners?.abort();listeners = undefined;
    documentListeners?.abort();documentListeners = undefined;
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
      let observedCanvas: HTMLCanvasElement | undefined, graphicsLost = false, graphicsRestored = false;
      let message: string | undefined;
      const owns = () => !disposed && generation === token && frame === item && options.wanted();
      function publish(next: EmbeddedProjectState, reason?: string) {
        if (owns() && (next !== state || reason !== message)) { state = next;message = reason;options.status(next, reason); }
      }
      function observe() {
        if (!owns()) return;
        clearTimeout(timer);timer = undefined;
        let next: EmbeddedProjectState = performance.now() - startedAt >= 12000 ? 'slow' : 'loading';
        let reason: string | undefined;
        try {
          const doc = item.contentDocument;
          if (doc && doc.URL !== 'about:blank') {
            if (doc !== currentDocument) {
              currentDocument = doc;documentGeneration++;startedAt = performance.now();next = 'loading';
              documentListeners?.abort();documentListeners = new AbortController();
              observedCanvas = undefined;graphicsLost = false;graphicsRestored = false;
              publish('loading');
            }
            const canvas = doc.querySelector<HTMLCanvasElement>('canvas#viewport');
            if (canvas && canvas !== observedCanvas) {
              observedCanvas = canvas;
              canvas.addEventListener('webglcontextlost', () => {
                if (!owns() || currentDocument !== doc || observedCanvas !== canvas) return;
                graphicsLost = true;graphicsRestored = false;observe();
              }, { signal: documentListeners!.signal });
              canvas.addEventListener('webglcontextrestored', () => {
                if (!owns() || currentDocument !== doc || observedCanvas !== canvas) return;
                // The original ready flag predates this GPU generation. A
                // fresh document is the reliable recovery boundary available.
                graphicsRestored = true;observe();
              }, { signal: documentListeners!.signal });
            }
            const api = (item.contentWindow as LawsonWindow | null)?.__LAWSON__;
            const fatal = doc.getElementById('fatal');
            const style = fatal ? item.contentWindow!.getComputedStyle(fatal) : undefined;
            const visibleFatal = !!fatal && !!fatal.getClientRects().length && style?.display !== 'none' && style?.visibility !== 'hidden' && style?.opacity !== '0';
            const wrongDocument = doc.readyState === 'complete' && (!doc.getElementById('app') || !canvas);
            if (wrongDocument) { next = 'error';reason = '页面未能正常打开'; }
            else if (visibleFatal || api?.error || doc.body?.dataset.ready === 'error') next = 'error';
            else if (graphicsLost) { next = 'error';reason = graphicsRestored ? '图形连接已恢复，请重新载入场景' : '图形连接已中断'; }
            else if (api?.ready === true) next = 'ready';
          }
        } catch { /* No trustworthy signal yet: retain loading/slow and exits. */ }
        publish(next, reason);
        const docToken = documentGeneration;
        const scheduled = window.setTimeout(() => {
          if (!owns() || timer !== scheduled || docToken !== documentGeneration) return;
          timer = undefined;observe();
        }, state === 'ready' ? 500 : 200);
        timer = scheduled;
      }
      item.addEventListener('load', observe, { signal: listeners.signal });
      document.addEventListener('visibilitychange', () => { if (!document.hidden) observe(); }, { signal: listeners.signal });
      window.addEventListener('pageshow', observe, { signal: listeners.signal });
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
