import { birdConfig } from '../config/birds';
import { Vector3 } from 'three';
import type { Camera } from 'three';
import type { BirdRect, BirdView } from '../scene/createBirds';

/** Reuse rectangles while the camera/layout is held. Only the three reader
 * shells are considered, never a fresh measurement of ten article trees.
 */
export function createBirdVisibility(app: HTMLElement, host: HTMLElement, wake: () => void) {
  const fixed = [...app.querySelectorAll<HTMLElement>('.tour-header,.tour-footer,.tour-stops')];
  const dynamic = [...app.querySelectorAll<HTMLElement>('.tour-heading,.pillar-reading,.film-reading,.experiment-reading')];
  const live = app.querySelector<HTMLElement>('.tour-project-live-space');
  const main = app.querySelector<HTMLElement>('main')!;
  const title = app.querySelector('#tour-title')!;
  const glyphPoint = new Vector3();
  const copy = (r: DOMRect): BirdRect => ({ left: r.left, top: r.top, right: r.right, bottom: r.bottom });
  let layoutKey = '', poseKey = '', fixedRects: BirdRect[] = [];
  let generation = 0;
  const records = dynamic.map(element => ({ element, heading: element.classList.contains('tour-heading'), generation: -1, signature: '',
    width: 0, height: 0, left: 0, top: 0, dx: 0, dy: 0 }));
  let disposed = false;
  const sizes = new WeakMap<Element, string>();
  const resize = new ResizeObserver(entries => {
    if (disposed) return;
    let changed = false;
    for (const e of entries) { const key = `${e.contentRect.width}/${e.contentRect.height}`;if (sizes.get(e.target) !== key) { sizes.set(e.target, key);changed = true; } }
    if (changed) { generation++;layoutKey = '';poseKey = '';wake(); }
  });
  for (const e of [host, ...fixed, ...dynamic, ...(live ? [live] : [])]) resize.observe(e);
  const view: BirdView = { bounds: { left: 0, top: 0, right: 1, bottom: 1 }, avoid: [], margin: birdConfig.desktopMargin, key: '' };
  // The existing presentation/readers explicitly write visibility/opacity.
  // Reading those inline values avoids a new forced style/layout flush after
  // their position writes on every camera frame.
  const visible = (e: HTMLElement) => !e.hidden && e.style.visibility !== 'hidden' && e.style.display !== 'none' && e.style.opacity !== '0';
  const translateY = (e: HTMLElement) => Number(e.style.transform.match(/translateY\(([-\d.]+)px\)/)?.[1] ?? 0);
  function rectangle(r: typeof records[number]) {
    const e = r.element;
    const station = e.classList.contains('pillar-reading') ? host.dataset.readingStation : e.classList.contains('film-reading') ? host.dataset.filmStation : host.dataset.experimentStation;
    const signature = r.heading ? `${e.dataset.kind}/${title.textContent}` : `${station}/${e.style.width}/${e.style.getPropertyValue('--film-media-height')}`;
    const left = parseFloat(e.style.left), top = parseFloat(e.style.top);
    if (r.generation !== generation || r.signature !== signature) {
      const box = e.getBoundingClientRect();r.generation = generation;r.signature = signature;r.width = box.width;r.height = box.height;
      r.left = box.left;r.top = box.top - (r.heading ? translateY(e) : 0);
      r.dx = box.left - (Number.isFinite(left) ? left : box.left);r.dy = box.top - (Number.isFinite(top) ? top : box.top);
    }
    const x = r.heading || !Number.isFinite(left) ? r.left : left + r.dx;
    const y = r.heading ? r.top + translateY(e) : Number.isFinite(top) ? top + r.dy : r.top;
    return { left: x, top: y, right: x + r.width, bottom: y + r.height };
  }
  return {
    measure(layout: string, pose: string, projectLive: boolean, camera: Camera, glyph?: Vector3) {
      if (layoutKey !== layout) { layoutKey = layout;view.bounds = copy(host.getBoundingClientRect());fixedRects = fixed.filter(visible).map(e => copy(e.getBoundingClientRect()));poseKey = ''; }
      if (poseKey !== pose) {
        poseKey = pose;
        view.avoid = projectLive ? [] : main.dataset.readingMode === 'stable' ? [view.bounds] : [...fixedRects, ...records.filter(r => visible(r.element)).map(rectangle)];
        if (!projectLive && glyph && main.dataset.readingMode !== 'stable') {
          glyphPoint.copy(glyph).project(camera);const b = view.bounds;
          const x = b.left + (glyphPoint.x * .5 + .5) * (b.right - b.left), y = b.top + (.5 - glyphPoint.y * .5) * (b.bottom - b.top);
          const radius = .55 * Math.abs(camera.projectionMatrix.elements[5]!) * (b.bottom - b.top) * .5;
          view.avoid = [...view.avoid, { left: x - radius, right: x + radius, top: y - radius, bottom: y + radius }];
        }
        if (projectLive && live) {
          // Projection uses the complete original canvas. Clip/safe margins use
          // the real live pane separately; never create another scene/camera.
          const r = copy(live.getBoundingClientRect()), b = view.bounds;
          view.avoid = [
            { left: b.left - 1000, right: r.left, top: b.top - 1000, bottom: b.bottom + 1000 },
            { left: r.right, right: b.right + 1000, top: b.top - 1000, bottom: b.bottom + 1000 },
            { left: r.left, right: r.right, top: b.top - 1000, bottom: r.top },
            { left: r.left, right: r.right, top: r.bottom, bottom: b.bottom + 1000 },
          ];
        }
        view.margin = view.bounds.right - view.bounds.left < 600 ? birdConfig.mobileMargin : birdConfig.desktopMargin;
        view.key = `${generation}/${layout}/${pose}`;
      }
      return view;
    },
    dispose() { if (disposed) return;disposed = true;resize.disconnect(); },
  };
}
