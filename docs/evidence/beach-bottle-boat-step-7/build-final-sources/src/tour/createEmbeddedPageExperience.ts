import type { EmbeddedProjectState } from './projectContent';

export interface PageInspection {
  state: 'loading' | 'ready' | 'error';
  message?: string;
  graphicsLost?: boolean;
}
export interface EmbeddedPageProfile {
  title: string;
  canvasSelector: string;
  readyEvent?: string;
  inspect(doc: Document, win: Window, canvas: HTMLCanvasElement | null): PageInspection;
}
export interface EmbeddedPageOptions {
  container: HTMLElement;
  entry: string;
  wanted(): boolean;
  status(state: EmbeddedProjectState, message?: string): void;
}

/** Own a document, never its simulation. Retries and navigations have distinct identities. */
export function createEmbeddedPageExperience(options: EmbeddedPageOptions, profile: EmbeddedPageProfile) {
  let disposed = false, generation = 0;
  let frame: HTMLIFrameElement | undefined, layoutFrame: number | undefined, timer: number | undefined;
  let listeners: AbortController | undefined, releaseDocument: (() => void) | undefined;
  function unmount() {
    generation++;
    if (layoutFrame !== undefined) cancelAnimationFrame(layoutFrame);
    layoutFrame = undefined;clearTimeout(timer);timer = undefined;
    listeners?.abort();listeners = undefined;releaseDocument?.();releaseDocument = undefined;
    const previous = frame;frame = undefined;
    if (!previous) return;
    try {
      const doc = previous.contentDocument;
      if (doc?.pointerLockElement) doc.exitPointerLock();
      if (document.fullscreenElement === previous) void document.exitFullscreen().catch(() => {});
      else if (doc?.fullscreenElement) void doc.exitFullscreen().catch(() => {});
    } catch { /* Removal also handles inaccessible or navigating documents. */ }
    previous.remove();
  }
  function mount() {
    if (disposed || !options.wanted() || frame || layoutFrame !== undefined) return;
    const token = ++generation;
    options.status('loading');
    layoutFrame = requestAnimationFrame(() => {
      layoutFrame = undefined;
      if (disposed || generation !== token || !options.wanted() || !options.container.getClientRects().length) return;
      const item = document.createElement('iframe');frame = item;
      item.title = profile.title;item.allow = 'fullscreen';item.allowFullscreen = true;
      listeners = new AbortController();
      const expected = new URL(options.entry, document.baseURI);
      let currentDocument: Document | undefined, observedCanvas: HTMLCanvasElement | undefined;
      let documentListeners: AbortController | undefined, canvasListeners: AbortController | undefined;
      let documentGeneration = 0, graphicsLost = false, graphicsRestored = false, loaded = false, seenDocument = false;
      let startedAt = performance.now(), state: EmbeddedProjectState = 'loading', message: string | undefined;
      const owns = () => !disposed && generation === token && frame === item && options.wanted();
      releaseDocument = () => {
        documentListeners?.abort();canvasListeners?.abort();
        documentListeners = undefined;canvasListeners = undefined;currentDocument = undefined;observedCanvas = undefined;
      };
      function publish(next: EmbeddedProjectState, reason?: string) {
        if (owns() && (next !== state || reason !== message)) { state = next;message = reason;options.status(next, reason); }
      }
      function observe() {
        if (!owns()) return;
        clearTimeout(timer);timer = undefined;
        let next: EmbeddedProjectState = performance.now() - startedAt >= 12000 ? 'slow' : 'loading';
        let reason: string | undefined;
        try {
          const doc = item.contentDocument, win = item.contentWindow;
          if (doc && win && (doc.URL !== 'about:blank' || seenDocument)) {
            if (doc !== currentDocument) {
              const replacement = seenDocument;
              releaseDocument?.();documentGeneration++;seenDocument = true;
              currentDocument = doc;graphicsLost = false;graphicsRestored = false;
              documentListeners = new AbortController();
              if (replacement) { startedAt = performance.now();next = 'loading'; }
              if (profile.readyEvent) win.addEventListener(profile.readyEvent, () => {
                if (owns() && currentDocument === doc) observe();
              }, { signal: documentListeners.signal });
            }
            const url = new URL(doc.URL);
            if (url.origin !== expected.origin || url.pathname !== expected.pathname) {
              next = 'error';reason = '页面未能正常打开';
            } else {
              const canvas = doc.querySelector<HTMLCanvasElement>(profile.canvasSelector);
              if (canvas && canvas !== observedCanvas) {
                canvasListeners?.abort();canvasListeners = new AbortController();observedCanvas = canvas;
                canvas.addEventListener('webglcontextlost', () => {
                  if (!owns() || currentDocument !== doc || observedCanvas !== canvas) return;
                  graphicsLost = true;graphicsRestored = false;observe();
                }, { signal: canvasListeners.signal });
                canvas.addEventListener('webglcontextrestored', () => {
                  if (!owns() || currentDocument !== doc || observedCanvas !== canvas) return;
                  graphicsLost = true;graphicsRestored = true;observe();
                }, { signal: canvasListeners.signal });
              }
              const inspection = profile.inspect(doc, win, canvas);
              if (inspection.graphicsLost) graphicsLost = true;
              if (graphicsLost) { next = 'error';reason = graphicsRestored ? '图形连接已恢复，请重新载入场景' : '图形连接已中断，请重新载入场景'; }
              else if (inspection.state !== 'loading') { next = inspection.state;reason = inspection.message; }
            }
          } else if (loaded && !doc) {
            if (currentDocument) { releaseDocument?.();documentGeneration++; }
            next = 'error';reason = '无法确认页面状态，可重新载入或独立打开';
          }
        } catch {
          if (loaded) { next = 'error';reason = '无法确认页面状态，可重新载入或独立打开'; }
        }
        publish(next, reason);
        const docToken = documentGeneration;
        const scheduled = window.setTimeout(() => {
          if (!owns() || timer !== scheduled || docToken !== documentGeneration) return;
          timer = undefined;observe();
        }, state === 'ready' ? 500 : 200);
        timer = scheduled;
      }
      item.addEventListener('load', () => { loaded = true;observe(); }, { signal: listeners.signal });
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
