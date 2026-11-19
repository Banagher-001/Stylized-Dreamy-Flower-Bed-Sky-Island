import type { CardInteractionRegion, CardRegionInput, CardRegionSnapshot } from './cardInteractionRegion';

/** Optional, passive observer. Lives outside the app/3D/layout-observer tree. */
export function createCardRegionDebug(root: HTMLElement, region: CardInteractionRegion) {
  const controller = new AbortController();
  const events = { capture: true, passive: true, signal: controller.signal };
  const layer = document.createElement('aside');layer.className = 'ar-card-region-debug';
  layer.setAttribute('aria-hidden', 'true');layer.inert = true;
  layer.style.cssText = 'position:fixed;inset:0;z-index:10000;pointer-events:none;overflow:hidden;contain:strict;';
  const frame = document.createElement('div');frame.dataset.regionOutline = 'true';
  frame.style.cssText = 'position:absolute;box-sizing:border-box;border:2px dashed #237b6b;pointer-events:none;';
  const panel = document.createElement('pre');
  panel.style.cssText = 'position:absolute;left:12px;bottom:12px;box-sizing:border-box;max-width:calc(100vw - 24px);margin:0;padding:9px 12px;border:1px solid #8bb69b;border-radius:4px;background:#fffcedf5;color:#244c40;font:12px/1.5 monospace;white-space:pre-wrap;overflow-wrap:anywhere;pointer-events:none;';
  layer.append(frame, panel);document.body.append(layer);
  let disposed = false, pending: number | undefined, point: CardRegionInput | undefined;
  let ancestor: HTMLElement | null = null;
  const names = { cards: '卡牌区', page: '页面／全文', overlay: '弹层阅读', browser: '浏览器手势' };
  function paint(snapshot: CardRegionSnapshot) {
    layer.dataset.snapshot = JSON.stringify(snapshot);
    layer.dataset.owner = snapshot.owner;
    const r = snapshot.visibleBounds;frame.hidden = !r;
    if (r) Object.assign(frame.style, { left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`, borderColor: snapshot.owner === 'cards' ? '#237b6b' : snapshot.owner === 'overlay' ? '#b78b32' : '#7c8a7d' });
    panel.textContent = `卡牌区域检查 · 只读，不接管输入\n建议归属：${names[snapshot.owner]} / ${snapshot.reason}\n分类：${snapshot.category}　模式：${snapshot.layout} / ${snapshot.mode}\n可横移：${snapshot.overflow ? '是' : '否'}　自动选择：${snapshot.automatic ? '开启' : '暂停'}　阅读：${snapshot.reading}\n逻辑宽度：${snapshot.contentWidth.toFixed(1)} / ${snapshot.viewportWidth.toFixed(1)}\n入场：${snapshot.entrance}　离场：${snapshot.departure}`;
  }
  function refresh() {
    pending = undefined;if (disposed) return;
    const next = root.closest<HTMLElement>('.about-refresh');
    if (next !== ancestor) {
      ancestor = next;ancestorObserver.disconnect();
      if (ancestor) ancestorObserver.observe(ancestor, { attributes: true, attributeOldValue: true, attributeFilter: ['style','hidden','inert','aria-hidden','data-layout','data-reading-layout'] });
    }
    // Keyboard focus can be elsewhere; wheel ownership follows the pointer.
    paint(region.inspect(point ? { ...point, target: document.elementFromPoint(point.clientX, point.clientY) } : undefined));
  }
  function schedule() { if (!disposed && pending === undefined) pending = requestAnimationFrame(refresh); }
  function pointer(event: MouseEvent) {
    point = { clientX: event.clientX, clientY: event.clientY, ctrlKey: event.ctrlKey, metaKey: event.metaKey, altKey: event.altKey };schedule();
  }
  function keyboard(event: KeyboardEvent) {
    if (point) point = { ...point, ctrlKey: event.ctrlKey, metaKey: event.metaKey, altKey: event.altKey };schedule();
  }
  const meaningful = (records: MutationRecord[]) => {
    if (records.some(record => record.type === 'childList' || record.oldValue !== (record.target as Element).getAttribute(record.attributeName!))) schedule();
  };
  const ancestorObserver = new MutationObserver(meaningful);
  const stateObserver = new MutationObserver(meaningful);
  stateObserver.observe(root, { attributes: true, attributeOldValue: true, attributeFilter: ['data-mode','data-category','data-detail-mode','data-track-mode','data-track-enabled','data-entrance','data-departure'], childList: true, subtree: true });
  const resize = new ResizeObserver(schedule);
  resize.observe(root);for (const node of root.querySelectorAll<HTMLElement>('.ar-tool-rail,.ar-filter-bar,.ar-tool-controls')) resize.observe(node);
  window.addEventListener('pointermove', pointer, events);
  window.addEventListener('pointerdown', pointer, events);
  window.addEventListener('wheel', pointer, events);
  window.addEventListener('keydown', keyboard, events);window.addEventListener('keyup', keyboard, events);
  window.addEventListener('scroll', schedule, events);window.addEventListener('resize', schedule, events);
  window.addEventListener('focusin', schedule, events);document.addEventListener('visibilitychange', schedule, events);
  schedule();
  return {
    dispose() {
      if (disposed) return;disposed = true;controller.abort();resize.disconnect();stateObserver.disconnect();ancestorObserver.disconnect();
      if (pending !== undefined) cancelAnimationFrame(pending);layer.remove();
    },
  };
}
