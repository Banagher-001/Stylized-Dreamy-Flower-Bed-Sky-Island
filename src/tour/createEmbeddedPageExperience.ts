import type { EmbeddedProjectState } from './projectContent';

const slowAfterMs = 12_000;

export interface PageInspection {
  state: 'loading' | 'ready' | 'error';
  message?: string;
  graphicsLost?: boolean;
}
export interface EmbeddedPageProfile {
  title: string;
  canvasSelector: string;
  scrollContainer: string;
  readyEvent?: string;
  inspect(doc: Document, win: Window, canvas: HTMLCanvasElement | null): PageInspection;
}
export interface EmbeddedPageOptions {
  container: HTMLElement;
  entry: string;
  wanted(): boolean;
  interact(): void;
  status(state: EmbeddedProjectState, message?: string): void;
}

const controlKeys = new Set(['Tab', 'Enter', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown']);

function bindSceneInput(doc: Document, scrollContainer: string, signal: AbortSignal, interact: () => void) {
  const style = doc.createElement('style');
  // Scroll chaining happens inside the child document, including at its viewport edge.
  style.textContent = `html, body, ${scrollContainer} { overscroll-behavior: contain; }`;
  doc.head.append(style);
  signal.addEventListener('abort', () => style.remove(), { once: true });

  const listen = { capture: true, passive: true, signal };
  doc.addEventListener('pointerdown', event => {
    if (event.isTrusted && event.button <= 2) interact();
  }, listen);
  doc.addEventListener('wheel', event => {
    if (event.isTrusted && (event.deltaX || event.deltaY || event.deltaZ)) interact();
  }, listen);
  doc.addEventListener('keydown', event => {
    if (!event.isTrusted || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key.length === 1 || controlKeys.has(event.key)) interact();
  }, listen);
}

/** Own a document, never its simulation. Retries and navigations have distinct identities. */
export function createEmbeddedPageExperience(options: EmbeddedPageOptions, profile: EmbeddedPageProfile) {
  let disposed = false, generation = 0;
  let frame: HTMLIFrameElement | undefined, timer: number | undefined;
  let listeners: AbortController | undefined, releaseDocument: (() => void) | undefined;
  function stopPolling() {
    clearTimeout(timer);timer = undefined;
  }
  function unmount() {
    generation++;stopPolling();
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
    if (disposed || frame || document.hidden || !options.wanted() || !options.container.getClientRects().length) return;
    const token = ++generation;
    options.status('loading');
    const item = document.createElement('iframe');frame = item;
    item.title = profile.title;item.allow = 'fullscreen';item.allowFullscreen = true;
    listeners = new AbortController();
    const expected = new URL(options.entry, document.baseURI);
    let currentDocument: Document | undefined, observedCanvas: HTMLCanvasElement | undefined;
    let documentListeners: AbortController | undefined, canvasListeners: AbortController | undefined;
    let inputBound = false;
    let documentGeneration = 0, graphicsLost = false, graphicsRestored = false, loaded = false, seenDocument = false;
    let visibleSince: number | undefined, elapsedVisible = 0;
    let state: EmbeddedProjectState = 'loading', message: string | undefined;
    const owns = () => !disposed && generation === token && frame === item && options.wanted();
    releaseDocument = () => {
      documentListeners?.abort();canvasListeners?.abort();
      documentListeners = undefined;canvasListeners = undefined;currentDocument = undefined;observedCanvas = undefined;
      inputBound = false;
    };
    function publish(next: EmbeddedProjectState, reason?: string) {
      if (owns() && (next !== state || reason !== message)) { state = next;message = reason;options.status(next, reason); }
    }
    function observe() {
      if (!owns()) return;
      stopPolling();
      const now = performance.now();
      if (document.hidden) {
        if (visibleSince !== undefined) elapsedVisible += now - visibleSince;
        visibleSince = undefined;
        return;
      }
      visibleSince ??= now;
      let next: EmbeddedProjectState = elapsedVisible + now - visibleSince >= slowAfterMs ? 'slow' : 'loading';
      let reason: string | undefined;
      try {
        const doc = item.contentDocument, win = item.contentWindow;
        if (doc && win && (doc.URL !== 'about:blank' || seenDocument)) {
          if (doc !== currentDocument) {
            const replacement = seenDocument;
            releaseDocument?.();documentGeneration++;seenDocument = true;
            currentDocument = doc;graphicsLost = false;graphicsRestored = false;
            documentListeners = new AbortController();
            if (replacement) { visibleSince = now;elapsedVisible = 0;next = 'loading'; }
            if (profile.readyEvent) win.addEventListener(profile.readyEvent, () => {
              if (owns() && currentDocument === doc) observe();
            }, { signal: documentListeners.signal });
          }
          const url = new URL(doc.URL);
          if (url.origin !== expected.origin || url.pathname !== expected.pathname) {
            next = 'error';reason = '页面未能正常打开';
          } else {
            if (!inputBound && doc.head && documentListeners) {
              bindSceneInput(doc, profile.scrollContainer, documentListeners.signal, () => {
                if (owns() && currentDocument === doc && item.contentDocument === doc && state === 'ready' && !document.hidden) options.interact();
              });
              inputBound = true;
            }
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
          next = 'error';reason = '无法确认页面状态';
        }
      } catch {
        if (loaded) { next = 'error';reason = '无法确认页面状态'; }
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
    document.addEventListener('visibilitychange', observe, { signal: listeners.signal });
    window.addEventListener('pageshow', observe, { signal: listeners.signal });
    item.src = options.entry;options.container.append(item);observe();
  }
  return {
    mount,
    retry() { if (!disposed && !document.hidden && options.wanted()) { unmount();mount(); } },
    unmount,
    dispose() { if (!disposed) { disposed = true;unmount(); } },
  };
}
