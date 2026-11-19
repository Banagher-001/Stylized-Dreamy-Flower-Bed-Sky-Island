import { createEmbeddedPageExperience } from './createEmbeddedPageExperience';
import type { EmbeddedPageOptions } from './createEmbeddedPageExperience';

interface LawsonWindow extends Window { __LAWSON__?: { ready?: boolean; error?: unknown } }

/** Preserve LAWSON's existing signals and public lifecycle. */
export function createLawsonExperience(options: EmbeddedPageOptions) {
  return createEmbeddedPageExperience(options, {
    title: '罗森便利店 · 完整交互网页',
    canvasSelector: 'canvas#viewport',
    scrollContainer: '#panel',
    inspect(doc, win, canvas) {
      const api = (win as LawsonWindow).__LAWSON__, fatal = doc.getElementById('fatal');
      const style = fatal ? win.getComputedStyle(fatal) : undefined;
      const visibleFatal = !!fatal && !!fatal.getClientRects().length && style?.display !== 'none' && style?.visibility !== 'hidden' && style?.opacity !== '0';
      if (doc.readyState === 'complete' && (!doc.getElementById('app') || !canvas)) return { state: 'error', message: '页面未能正常打开' };
      if (visibleFatal || api?.error || doc.body?.dataset.ready === 'error') return { state: 'error' };
      if (api?.ready === true && canvas?.isConnected && canvas.width > 0 && canvas.height > 0 && !doc.getElementById('loader')) {
        return { state: 'ready', message: doc.fullscreenEnabled === false ? '可在当前窗口操作罗森场景。' : undefined };
      }
      return { state: 'loading' };
    },
  });
}
