import { createEmbeddedPageExperience } from './createEmbeddedPageExperience';
import type { EmbeddedPageOptions } from './createEmbeddedPageExperience';

interface BottleWindow extends Window {
  __bottleError?: unknown;
  __bottleOcean?: {
    ready?: boolean;
    renderer?: { domElement: HTMLCanvasElement; getContext(): WebGLRenderingContext | WebGL2RenderingContext };
    getDiagnostics?(): { renderer?: { calls?: number; triangles?: number } };
  };
}

/** Read the original's signals without controlling its clock, parameters or camera. */
export function createBottleOceanExperience(options: EmbeddedPageOptions) {
  return createEmbeddedPageExperience(options, {
    title: '瓶中海洋 · 完整交互网页',
    canvasSelector: 'canvas#gl',
    scrollContainer: '.panel-scroll',
    readyEvent: 'bottle-ocean-ready',
    inspect(doc, win, canvas) {
      const source = win as BottleWindow, api = source.__bottleOcean;
      const loader = doc.getElementById('loader'), errorText = doc.getElementById('loader-error')?.textContent?.trim();
      const context = api?.renderer?.getContext();
      if (context?.isContextLost()) return { state: 'error', graphicsLost: true };
      if (source.__bottleError || errorText) return { state: 'error', message: '场景暂时无法完成载入' };
      if (doc.readyState === 'complete' && (!canvas || !loader || !api)) return { state: 'error', message: '页面未能正常打开' };
      if (api?.ready === true && canvas?.isConnected && api.renderer?.domElement === canvas && context) {
        const bounds = canvas.getBoundingClientRect(), draw = api.getDiagnostics?.().renderer;
        if (bounds.width > 0 && bounds.height > 0 && canvas.width > 0 && canvas.height > 0 && loader && win.getComputedStyle(loader).display === 'none' && (draw?.calls ?? 0) > 0 && (draw?.triangles ?? 0) > 0) return { state: 'ready' };
      }
      return { state: 'loading' };
    },
  });
}
