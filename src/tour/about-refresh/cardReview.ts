import { aboutRefreshContent, getCard, initialEntryIds } from './content';
import { createToolCard } from './createToolCard';
import type { ToolCardView, ToolCardPose } from './createToolCard';
import { button, element } from './dom';
import './aboutRefresh.css';
import './cardReview.css';

const host = document.querySelector<HTMLElement>('#card-review')!;
const events = new AbortController();
const options = { signal: events.signal };
const controls = element('div', 'ar-review-controls');
const label = element('label', '', '查看工具');
const select = element('select');
for (const card of aboutRefreshContent.cards) {
  const option = element('option', '', card.name);option.value = card.id;select.append(option);
}
label.append(select);controls.append(label);
const poseNames = { front: '正面', quarter: '斜侧面', side: '侧面', back: '背面', detail: '完整介绍', left: '左侧极值', right: '右侧极值' } as const;
type PoseName = keyof typeof poseNames;
for (const [key, name] of Object.entries(poseNames)) {
  const control = button(name);control.dataset.cardReviewPose = key;controls.append(control);
}
const large = button('大字 200%');large.dataset.cardReviewLarge = '';large.setAttribute('aria-pressed', 'false');controls.append(large);
const stage = element('section', 'ar-review-theatre');stage.setAttribute('aria-label', '卡牌静态视角');
const specimenSlot = element('div', 'ar-review-specimen-slot');stage.append(specimenSlot);
const status = element('p', 'ar-review-metrics');status.setAttribute('role', 'status');
const intro = element('p', 'ar-review-description', '浅色石材、八段侧边、6px 厚度与浅刻纹。正式网页保持正面可读，飞行与鼠标跟随留在后续步骤。');
const galleryTitle = element('h2', 'ar-review-gallery-title', '首批四张');
const gallery = element('section', 'ar-review-gallery');gallery.setAttribute('aria-label', '首批四张工具卡牌');
host.append(controls, stage, status, intro, galleryTitle, gallery);
let specimen: ToolCardView;
let poseName: PoseName = 'front';
let disposed = false;
let metricFrame: number | undefined;
const galleryCards: ToolCardView[] = [];
const poses: Record<PoseName, ToolCardPose> = {
  front: { pitch: 0, yaw: 0 }, quarter: { pitch: -14, yaw: -32 },
  side: { pitch: 0, yaw: -85 }, back: { pitch: 0, yaw: 180 },
  detail: { pitch: 0, yaw: 0 }, left: { pitch: -7, yaw: -10 }, right: { pitch: 7, yaw: 10 },
};
function metrics() {
  if (disposed || !specimen) return;
  const size = specimen.element.dataset.entitySize?.split(',') ?? [];
  status.textContent = `${getCard(select.value)!.name} · ${poseNames[poseName]} · ${size[0] ?? '…'} × ${size[1] ?? '…'}px · 厚度 ${size[2] ?? '6'}px`;
}
function queueMetrics() {
  if (disposed || metricFrame !== undefined) return;
  metricFrame = requestAnimationFrame(() => { metricFrame = undefined;metrics(); });
}
function applyPose(name: PoseName) {
  poseName = name;
  const expanded = name === 'detail' || name === 'left' || name === 'right';
  specimen.setExpanded(expanded);
  specimen.element.style.width = expanded ? '16.675rem' : '14.5rem';
  specimen.setPose(poses[name]);
  for (const control of controls.querySelectorAll<HTMLButtonElement>('[data-card-review-pose]')) control.setAttribute('aria-pressed', String(control.dataset.cardReviewPose === name));
  queueMetrics();
}
function choose(id: string) {
  specimen?.dispose();specimen?.element.remove();
  select.value = id;
  specimen = createToolCard(getCard(id)!, { prefix: 'review-specimen', full: false, expanded: false });
  specimenSlot.append(specimen.element);applyPose(poseName);
  sizes.disconnect();sizes.observe(specimen.element);
}
const sizes = new ResizeObserver(queueMetrics);
choose('midjourney');
for (const id of initialEntryIds) {
  const view = createToolCard(getCard(id)!, { prefix: 'review-gallery', full: false, expanded: false });
  galleryCards.push(view);gallery.append(view.element);
}
select.addEventListener('change', () => choose(select.value), options);
controls.addEventListener('click', event => {
  const control = (event.target as Element).closest<HTMLButtonElement>('button');
  if (!control) return;
  if (control.dataset.cardReviewPose) applyPose(control.dataset.cardReviewPose as PoseName);
  else if (control === large) {
    const enabled = large.getAttribute('aria-pressed') !== 'true';
    large.setAttribute('aria-pressed', String(enabled));document.documentElement.style.fontSize = enabled ? '200%' : '';queueMetrics();
  }
}, options);
host.addEventListener('click', event => {
  const target = (event.target as Element).closest<HTMLButtonElement>('[data-action="detail"]');
  if (!target) return;
  const view = [specimen, ...galleryCards].find(item => item.element.contains(target));
  if (view) { view.setExpanded(view.element.dataset.expanded !== 'true');queueMetrics(); }
}, options);
function dispose() {
  if (disposed) return;disposed = true;events.abort();sizes.disconnect();
  if (metricFrame !== undefined) cancelAnimationFrame(metricFrame);
  specimen.dispose();for (const view of galleryCards) view.dispose();
}
declare global {
  interface Window {
    __toolCardReview: {
      readonly specimen: ToolCardView; readonly currentPose: PoseName;
      select(id: string): void; pose(name: PoseName): void;
      capture(): { id: string; pose: PoseName; size: string | undefined; faces: ReturnType<DOMRect['toJSON']>[]; bounds: { left: number; top: number; right: number; bottom: number }; depth: number };
      dispose(): void;
    };
  }
}
window.__toolCardReview = {
  get specimen() { return specimen; }, get currentPose() { return poseName; }, select: choose, pose: applyPose,
  capture() { const m = specimen.measure();return { id: select.value, pose: poseName, size: specimen.element.dataset.entitySize, faces: m.faces.map(r => r.toJSON()), bounds: m.bounds, depth: m.depth }; },
  dispose,
};
addEventListener('pagehide', dispose, { once: true });
if (import.meta.hot) import.meta.hot.dispose(dispose);
