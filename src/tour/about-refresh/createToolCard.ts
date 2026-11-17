import { aboutRefreshContent } from './content';
import { button, clamp, element } from './dom';
import { toolMarks } from './toolMarks';
import type { CategoryId, ToolCard } from './types';
import './toolCards.css';
import './cardDetails.css';
import './cardDeparture.css';

export interface ToolCardPose { pitch: number; yaw: number; roll?: number; scale?: number; lift?: number; }
export interface ToolCardReadingPose {
  amount: number; x: number; y: number; z: number; scale: number; pitch: number; yaw: number;
}
export const restingReadingPose: Readonly<ToolCardReadingPose> = { amount: 0, x: 0, y: 0, z: 0, scale: 1, pitch: 0, yaw: 0 };
export interface ToolCardFlightPose { x: number; y: number; z: number; pitch: number; yaw: number; roll: number; }
export const restingFlightPose: Readonly<ToolCardFlightPose> = { x: 0, y: 0, z: 0, pitch: 0, yaw: 0, roll: 0 };
export type ToolDetailMode = 'summary' | 'preview' | 'pinned' | 'catalog';
export interface ToolCardView {
  element: HTMLElement;
  setPose(pose: ToolCardPose): void;
  setReading(pose?: ToolCardReadingPose): void;
  setFlight(pose?: ToolCardFlightPose): void;
  setExpanded(expanded: boolean): void;
  setDetail(mode: ToolDetailMode, width?: number, reveal?: number): void;
  probeDetail<T>(width: number, measure: () => T): T;
  measure(): { faces: DOMRect[]; bounds: { left: number; top: number; right: number; bottom: number }; depth: number; };
  dispose(): void;
}

const categories: Record<CategoryId, { accent: string; symbol: string }> = {
  G1: { accent: '#739a83', symbol: 'M34 48Q50 25 66 48Q50 72 34 48ZM50 28V71' },
  G2: { accent: '#7ba6ae', symbol: 'M28 45Q39 33 50 45T72 45M28 56Q39 44 50 56T72 56' },
  G3: { accent: '#b4a76f', symbol: 'M50 29V39M50 61V71M29 50H39M61 50H71M40 50L50 39L60 50L50 61Z' },
  G4: { accent: '#7c9b8f', symbol: 'M50 29L68 40V60L50 71L32 60V40ZM32 40L50 51L68 40M50 51V71' },
  G5: { accent: '#9aab76', symbol: 'M31 35H69V65H31ZM31 45H69M43 35V65M56 35V65M31 55H69' },
  G6: { accent: '#a39db1', symbol: 'M31 33H62V57H31ZM39 41H70V67H39' },
  G7: { accent: '#6e9f97', symbol: 'M40 35L27 50L40 65M60 35L73 50L60 65M55 31L45 69' },
};
const instances = new WeakMap<HTMLElement, ToolCardView>();
const labels: Readonly<Record<string, string>> = aboutRefreshContent.controls;
const ns = 'http://www.w3.org/2000/svg';
let serial = 0;

function svg(tag: 'svg' | 'path' | 'circle' | 'text', attributes: Record<string, string>) {
  const node = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

/** An octagonal prism with a single accessible, selectable front. No owned clock. */
export function createToolCard(card: ToolCard, options: { prefix: string; full: boolean; expanded: boolean }): ToolCardView {
  const uid = `${options.prefix}-${options.full ? 'all' : 'rail'}-${card.id}`;
  const ownId = `ar-card-${++serial}`;
  const root = element('article', 'ar-tool-card ar-stone-card');
  root.dataset.toolId = card.id;root.dataset.kind = card.kind;
  root.dataset.presentation = options.full ? 'catalog' : 'rail';
  root.dataset.geometryReady = 'false';root.dataset.expanded = String(options.expanded);
  root.style.setProperty('--ar-card-accent', categories[card.category].accent);
  const position = element('div', 'ar-card-position');
  const reading = element('div', 'ar-card-reading');
  const flight = element('div', 'ar-card-flight');
  const orientation = element('div', 'ar-card-orientation');
  const entity = element('div', 'ar-card-entity');
  const front = element('div', 'ar-card-face ar-card-front');
  front.dataset.cardFace = 'front';
  const classification = element('p', 'ar-card-classification', aboutRefreshContent.categories.find(c => c.id === card.category)!.name);
  const heading = element('div', 'ar-card-heading');
  const badge = element('span', 'ar-card-emblem');
  badge.setAttribute('aria-hidden', 'true');
  const image = element('img', 'ar-tool-mark');
  image.src = toolMarks[card.id]!.src;image.alt = '';image.width = 42;image.height = 42;
  image.decoding = 'async';image.loading = 'eager';image.draggable = false;
  root.dataset.markKind = toolMarks[card.id]!.kind;
  root.dataset.markState = 'loading';
  const events = new AbortController();
  image.addEventListener('load', () => { root.dataset.markState = 'ready'; }, { signal: events.signal });
  image.addEventListener('error', () => { root.dataset.markState = 'error'; }, { signal: events.signal });
  badge.append(image);
  const title = element('h3', 'ar-card-name', card.name);title.id = `${uid}-title`;
  root.setAttribute('aria-labelledby', title.id);heading.append(badge, title);
  if (card.kind === 'practice') heading.append(element('span', 'ar-kind', '能力'));
  const use = element('p', 'ar-card-use', card.use);
  const detail = element('p', 'ar-card-detail', card.detail);detail.id = `${uid}-detail`;
  const footer = element('div', 'ar-card-footer');
  const tags = element('ul', 'ar-card-tags');tags.setAttribute('aria-label', '用途标签');
  for (const tag of card.tags) tags.append(element('li', '', tag));
  footer.append(tags);
  let toggle: HTMLButtonElement | undefined;
  if (!options.full) {
    toggle = button('', 'ar-button ar-detail-toggle');toggle.dataset.action = 'detail';toggle.dataset.toolId = card.id;
    toggle.setAttribute('aria-controls', detail.id);footer.append(toggle);
  }
  const rim = svg('svg', { class: 'ar-card-rim', 'aria-hidden': 'true', focusable: 'false' });
  const rimOuter = svg('path', { fill: 'none', stroke: '#9aac8b', 'stroke-width': '1.2' });
  const rimInner = svg('path', { fill: 'none', stroke: '#fffdf2', 'stroke-width': '1', opacity: '.85' });
  rim.append(rimOuter, rimInner);
  const frontSigil = svg('svg', { class: 'ar-card-front-sigil', viewBox: '0 0 100 100', 'aria-hidden': 'true', focusable: 'false' });
  frontSigil.append(
    svg('path', { d: 'M50 20L76 35V65L50 80L24 65V35Z', fill: 'none', stroke: 'currentColor', 'stroke-width': '.6' }),
    svg('path', { d: categories[card.category].symbol, fill: 'none', stroke: 'currentColor', 'stroke-width': '1.2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
  );
  front.append(classification, heading, use, detail, footer, frontSigil, rim);

  const back = element('div', 'ar-card-face ar-card-back');
  back.dataset.cardFace = 'back';back.setAttribute('aria-hidden', 'true');back.inert = true;
  const engraving = svg('svg', { class: 'ar-card-engraving', viewBox: '0 0 100 132', 'aria-hidden': 'true', focusable: 'false' });
  engraving.append(
    svg('path', { d: 'M24 12H76L89 25V96L76 109H24L11 96V25ZM30 20H70M24 101H76', fill: 'none', stroke: '#8ca185', 'stroke-width': '.9' }),
    svg('circle', { cx: '50', cy: '50', r: '28', fill: 'none', stroke: 'currentColor', 'stroke-width': '1' }),
    svg('circle', { cx: '50', cy: '50', r: '24', fill: 'none', stroke: 'currentColor', 'stroke-width': '.4' }),
    svg('path', { d: categories[card.category].symbol, fill: 'none', stroke: 'currentColor', 'stroke-width': '1.4', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }),
    svg('path', { d: 'M36 87Q50 77 64 87M43 92H57M46 9L50 5L54 9M50 79V85', fill: 'none', stroke: 'currentColor', 'stroke-width': '.8' }),
  );
  const signature = svg('text', { x: '50', y: '123', 'text-anchor': 'middle', fill: '#526f56', 'font-size': '8', 'font-family': 'Georgia,serif', 'letter-spacing': '2' });
  signature.textContent = 'sakan';engraving.append(signature);back.append(engraving);
  const sides = Array.from({ length: 8 }, (_, index) => {
    const side = element('span', 'ar-card-side');side.dataset.cardFace = `side-${index}`;side.setAttribute('aria-hidden', 'true');return side;
  });
  const shadow = element('span', 'ar-card-shadow');shadow.setAttribute('aria-hidden', 'true');
  entity.append(shadow, front, back, ...sides);orientation.append(entity);flight.append(orientation);reading.append(flight);position.append(reading);root.append(position);
  let disposed = false;
  let width = 0, height = 0, depth = 6;
  let normals: [number, number][] = [];
  let basePose: ToolCardPose = { pitch: 0, yaw: 0, scale: 1, lift: 0 };
  let currentPose = basePose;
  let readingPose: ToolCardReadingPose = { ...restingReadingPose };
  let flightPose: ToolCardFlightPose = { ...restingFlightPose };
  let detailState: { mode: ToolDetailMode; width?: number; reveal: number } = { mode: options.full ? 'catalog' : 'summary', reveal: 0 };
  let probing = false;

  function light() {
    const pitch = (currentPose.pitch + flightPose.pitch) * Math.PI / 180, yaw = (currentPose.yaw + flightPose.yaw) * Math.PI / 180;
    sides.forEach((side, i) => {
      const [nx, ny] = normals[i] ?? [0, -1];
      const px = nx, py = ny * Math.cos(pitch), pz = ny * Math.sin(pitch);
      const x = px * Math.cos(yaw) + pz * Math.sin(yaw), z = -px * Math.sin(yaw) + pz * Math.cos(yaw);
      const roll = ((currentPose.roll ?? 0) + flightPose.roll) * Math.PI / 180;
      const rx = x * Math.cos(roll) - py * Math.sin(roll), ry = x * Math.sin(roll) + py * Math.cos(roll);
      const amount = clamp(.72 + .30 * (-.40 * rx - .58 * ry + .70 * z), .52, 1.03);
      side.style.backgroundColor = `rgb(${[171, 185, 151].map(v => Math.round(v * amount)).join(' ')})`;
    });
  }
  function shape(w: number, h: number) {
    if (disposed || w <= 0 || h <= 0 || w === width && h === height) return;
    width = w;height = h;
    const styles = getComputedStyle(root);
    depth = parseFloat(styles.getPropertyValue('--ar-card-depth')) || 6;
    const cut = Math.min(parseFloat(styles.getPropertyValue('--ar-card-cut')) || 6, width / 6, height / 6);
    const points = [[0, cut], [cut, 0], [width - cut, 0], [width, cut], [width, height - cut], [width - cut, height], [cut, height], [0, height - cut]];
    normals = [];
    points.forEach((a, i) => {
      const b = points[(i + 1) % points.length]!, dx = b[0]! - a[0]!, dy = b[1]! - a[1]!;
      const length = Math.hypot(dx, dy), ux = dx / length, uy = dy / length;
      const side = sides[i]!;normals.push([uy, -ux]);
      side.style.width = `${length}px`;side.style.height = `${depth}px`;
      // Basis: local x follows the polygon edge; local y traverses thickness.
      side.style.transform = `matrix3d(${ux},${uy},0,0,0,0,1,0,${uy},${-ux},0,0,${a[0]},${a[1]},${-depth},1)`;
    });
    rim.setAttribute('viewBox', `0 0 ${width} ${height}`);
    const outline = (inset: number) => `M${inset},${cut + inset / 2}L${cut + inset / 2},${inset}H${width - cut - inset / 2}L${width - inset},${cut + inset / 2}V${height - cut - inset / 2}L${width - cut - inset / 2},${height - inset}H${cut + inset / 2}L${inset},${height - cut - inset / 2}Z`;
    rimOuter.setAttribute('d', outline(.8));rimInner.setAttribute('d', outline(2.2));
    root.dataset.geometryReady = 'true';root.dataset.entitySize = `${width.toFixed(3)},${height.toFixed(3)},${depth}`;
    light();
  }
  const observer = new ResizeObserver(entries => {
    const entry = entries[0];if (!entry || disposed) return;
    const size = entry.borderBoxSize[0];
    if (size) shape(size.inlineSize, size.blockSize);
    else shape(parseFloat(getComputedStyle(front).width), parseFloat(getComputedStyle(front).height));
  });
  observer.observe(front);

  function renderPose() {
    const amount = clamp(readingPose.amount, 0, 1);
    currentPose = { pitch: basePose.pitch * (1 - amount) + readingPose.pitch,
      yaw: basePose.yaw * (1 - amount) + readingPose.yaw, roll: (basePose.roll ?? 0) * (1 - amount),
      scale: (basePose.scale ?? 1) * readingPose.scale, lift: (basePose.lift ?? 0) + readingPose.y };
    root.style.setProperty('--ar-card-pitch', `${currentPose.pitch}deg`);
    root.style.setProperty('--ar-card-yaw', `${currentPose.yaw}deg`);
    root.style.setProperty('--ar-card-roll', `${currentPose.roll}deg`);
    root.style.setProperty('--ar-card-read-scale', String(currentPose.scale));
    root.style.setProperty('--ar-card-lift', `${currentPose.lift}px`);
    root.style.setProperty('--ar-card-read-x', `${readingPose.x}px`);
    root.style.setProperty('--ar-card-read-z', `${readingPose.z}px`);
    root.style.setProperty('--ar-card-read-amount', String(amount));
    updateFacing();
    root.dataset.pose = `${currentPose.pitch},${currentPose.yaw}`;
    root.dataset.readingPose = [amount, readingPose.x, readingPose.y, readingPose.z, readingPose.scale, readingPose.pitch, readingPose.yaw].map(v => v.toFixed(4)).join(',');
    light();
  }
  function updateFacing() {
    const readable = Math.cos((currentPose.pitch + flightPose.pitch) * Math.PI / 180) * Math.cos((currentPose.yaw + flightPose.yaw) * Math.PI / 180) > .5;
    front.inert = !readable;front.setAttribute('aria-hidden', String(!readable));
  }
  function setFlight(pose: ToolCardFlightPose = { ...restingFlightPose }) {
    if (disposed) return;
    flightPose = { ...pose };
    for (const axis of ['x','y','z','pitch','yaw','roll'] as const) {
      root.style.setProperty(`--ar-card-flight-${axis}`, `${pose[axis]}${axis === 'x' || axis === 'y' || axis === 'z' ? 'px' : 'deg'}`);
    }
    root.dataset.flightPose = Object.values(pose).map(v => v.toFixed(4)).join(',');
    updateFacing();light();
  }
  function setPose(pose: ToolCardPose) {
    if (disposed) return;
    basePose = { pitch: clamp(pose.pitch, -80, 80), yaw: clamp(pose.yaw, -180, 180), roll: clamp(pose.roll ?? 0, -30, 30), scale: clamp(pose.scale ?? 1, .7, 1.3), lift: pose.lift ?? 0 };
    renderPose();
  }
  function setReading(pose: ToolCardReadingPose = { ...restingReadingPose }) {
    if (disposed) return;
    readingPose = { ...pose, amount: clamp(pose.amount, 0, 1), scale: clamp(pose.scale, 1, 1.16), pitch: clamp(pose.pitch, -5, 5), yaw: clamp(pose.yaw, -7, 7) };
    renderPose();
  }
  function setDetail(mode: ToolDetailMode, panelWidth?: number, reveal = 1) {
    if (disposed) return;
    detailState = { mode, width: panelWidth, reveal: clamp(reveal, 0, 1) };
    const expanded = mode !== 'summary', wide = panelWidth !== undefined;
    root.dataset.detailState = mode;root.dataset.detailWide = String(wide);root.dataset.expanded = String(expanded);
    if (wide) root.style.setProperty('--ar-detail-width', `${panelWidth}px`);else root.style.removeProperty('--ar-detail-width');
    root.style.setProperty('--ar-detail-reveal', String(detailState.reveal));
    detail.hidden = !expanded || reveal <= 0;
    detail.setAttribute('aria-hidden', String(detail.hidden || probing));
    if (toggle && !probing) {
      const text = mode === 'preview' ? '固定阅读' : expanded ? labels['collapse-detail']! : labels['expand-detail']!;
      if (toggle.textContent !== text) toggle.textContent = text;
      toggle.setAttribute('aria-expanded', String(!detail.hidden));
      toggle.setAttribute('aria-label', `${mode === 'preview' ? '固定阅读' : expanded ? '收起' : '展开'} ${card.name} 的详情`);
    }
    // Width animation and probes update the real prism in the same frame.
    shape(front.offsetWidth, front.offsetHeight);
  }
  function setExpanded(expanded: boolean) { setDetail(options.full ? 'catalog' : expanded ? 'pinned' : 'summary'); }
  function probeDetail<T>(panelWidth: number, measure: () => T): T {
    const previous = { ...detailState };probing = true;
    try { setDetail('preview', panelWidth);return measure(); }
    finally { setDetail(previous.mode, previous.width, previous.reveal);probing = false;detail.setAttribute('aria-hidden', String(detail.hidden)); }
  }
  const view: ToolCardView = {
    element: root, setPose, setReading, setFlight, setExpanded, setDetail, probeDetail,
    measure() {
      const faces = [front, back, ...sides].map(node => node.getBoundingClientRect());
      const shade = shadow.getBoundingClientRect(), margin = Math.ceil(3 * (7 + readingPose.amount * .2) * (currentPose.scale ?? 1) * 1.05);
      return { faces, depth, bounds: {
        left: Math.min(shade.left - margin, ...faces.map(r => r.left)), top: Math.min(shade.top - margin, ...faces.map(r => r.top)),
        right: Math.max(shade.right + margin, ...faces.map(r => r.right)), bottom: Math.max(shade.bottom + margin, ...faces.map(r => r.bottom)),
      } };
    },
    dispose() { if (disposed) return;disposed = true;observer.disconnect();events.abort();instances.delete(root); },
  };
  instances.set(root, view);root.dataset.cardInstance = ownId;
  setExpanded(options.expanded);setPose(options.full ? { pitch: 0, yaw: 0 } : currentPose);
  return view;
}

export function measureToolCardProjection(node: HTMLElement) { return instances.get(node)?.measure(); }
export function setToolCardPose(node: HTMLElement, pose: ToolCardPose) { instances.get(node)?.setPose(pose); }
