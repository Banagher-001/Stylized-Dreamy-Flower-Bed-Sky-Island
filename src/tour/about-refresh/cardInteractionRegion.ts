/** Read-only input contract. The wheel controller can consume this in step 3. */
export type CardInputOwner = 'cards' | 'page' | 'overlay' | 'browser';
export type CardReadingState = 'summary' | 'preview' | 'pinned';
export interface CardRegionBounds {
  left: number; top: number; right: number; bottom: number; width: number; height: number;
}
export interface CardRegionInput {
  clientX: number; clientY: number; ctrlKey?: boolean; metaKey?: boolean; altKey?: boolean;
  target?: EventTarget | null;
}
export interface CardRegionState {
  mode: 'cards' | 'all'; category: string; automatic: boolean; reading: CardReadingState;
  entrance: string; departure: string;
}
export interface CardRegionSnapshot extends CardRegionState {
  bounds: CardRegionBounds | null; visibleBounds: CardRegionBounds | null;
  viewportWidth: number; contentWidth: number; overflow: boolean; active: boolean;
  layout: string; inside: boolean; owner: CardInputOwner; reason: string;
  action: 'none' | 'scroll' | 'collapse-preview-and-scroll' | 'collapse-pinned-and-scroll';
}

function rectangle(left: number, top: number, right: number, bottom: number): CardRegionBounds | null {
  if (![left, top, right, bottom].every(Number.isFinite) || right <= left || bottom <= top) return null;
  return { left, top, right, bottom, width: right - left, height: bottom - top };
}
function contains(bounds: CardRegionBounds | null, x: number, y: number) {
  return !!bounds && Number.isFinite(x) && Number.isFinite(y) && x >= bounds.left && x < bounds.right && y >= bounds.top && y < bounds.bottom;
}
function exposed(element: HTMLElement) {
  if (!element.isConnected || !element.getClientRects().length) return false;
  for (let node: HTMLElement | null = element; node; node = node.parentElement) {
    if (node.hidden || node.inert || node.getAttribute('aria-hidden') === 'true') return false;
    const style = getComputedStyle(node);
    if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) <= .001) return false;
  }
  return true;
}

/** No listeners, DOM writes, scroll calls, autoplay changes or animation frames. */
export function createCardInteractionRegion(options: {
  root: HTMLElement; rail: HTMLElement; filters: HTMLElement; controls: HTMLElement;
  state(): CardRegionState;
}) {
  const { root, rail, filters, controls } = options;
  function measureHorizontal() {
    const viewportWidth = rail.clientWidth;
    if (!viewportWidth) return { viewportWidth, contentWidth: 0, overflow: false };
    const nodes = [...rail.querySelectorAll<HTMLElement>('.ar-tool-slot')];
    const stage = rail.querySelector<HTMLElement>('.ar-track-stage') ?? rail;
    const style = getComputedStyle(rail), gap = parseFloat(getComputedStyle(stage).columnGap) || 0;
    // Layout widths stay stable while faces are tilted, enlarged or in flight.
    const contentWidth = nodes.length ? nodes.reduce((sum, node) => sum + node.offsetWidth, 0) +
      (nodes.length - 1) * gap + (parseFloat(style.paddingLeft) || 0) + (parseFloat(style.paddingRight) || 0) : 0;
    return { viewportWidth, contentWidth, overflow: contentWidth > viewportWidth + 1 };
  }
  return {
    measureHorizontal,
    inspect(input?: CardRegionInput): CardRegionSnapshot {
      const state = options.state();
      const active = state.mode === 'cards' && !document.hidden && exposed(rail);
      const controlBox = controls.getBoundingClientRect(), filterBox = filters.getBoundingClientRect();
      const bounds = active ? rectangle(controlBox.left, filterBox.bottom, controlBox.right, controlBox.top) : null;
      const visibleBounds = bounds ? rectangle(Math.max(0, bounds.left), Math.max(0, bounds.top), Math.min(innerWidth, bounds.right), Math.min(innerHeight, bounds.bottom)) : null;
      const snapshot: CardRegionSnapshot = { ...state, ...measureHorizontal(), bounds, visibleBounds, active: !!visibleBounds,
        layout: root.closest<HTMLElement>('.about-refresh')?.dataset.layout ?? '',
        inside: !!input && contains(visibleBounds, input.clientX, input.clientY), owner: 'page', reason: 'no-pointer', action: 'none' };
      const decide = (owner: CardInputOwner, reason: string, action: CardRegionSnapshot['action'] = 'none') => ({ ...snapshot, owner, reason, action });
      if (input?.ctrlKey || input?.metaKey || input?.altKey) return decide('browser', 'browser-modifier');
      if (document.querySelector('dialog[open]:modal')) return decide('overlay', 'modal-reading');
      if (state.mode === 'all') return decide('page', 'catalog-reading');
      if (!snapshot.active) return decide('page', 'region-hidden');
      if (!input) return snapshot;
      const help = root.querySelector<HTMLElement>('.ar-tool-help-panel:not([hidden])');
      if (help && exposed(help)) {
        const r = help.getBoundingClientRect();
        if (contains(rectangle(r.left, r.top, r.right, r.bottom), input.clientX, input.clientY)) return decide('overlay', 'help-reading');
      }
      if (!snapshot.inside) return decide('page', 'outside-region');
      const hit = input.target instanceof Element ? input.target : document.elementFromPoint(input.clientX, input.clientY);
      // A fixed header/nav or another visible surface wins over geometry behind it.
      if (hit && (!root.contains(hit) || filters.contains(hit) || controls.contains(hit))) return decide('page', 'other-control');
      if (hit?.closest('input,textarea,select,[contenteditable="true"]')) return decide('page', 'native-input');
      if (!snapshot.overflow) return decide('page', 'all-cards-visible');
      const action = state.reading === 'pinned' ? 'collapse-pinned-and-scroll' : state.reading === 'preview' ? 'collapse-preview-and-scroll' : 'scroll';
      return decide('cards', 'scrollable-region', action);
    },
  };
}
export type CardInteractionRegion = ReturnType<typeof createCardInteractionRegion>;
