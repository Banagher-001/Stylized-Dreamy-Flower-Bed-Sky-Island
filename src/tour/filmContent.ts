import signalImage from '../assets/signal-garden.webp';
import formImage from '../assets/liquid-form.webp';

export interface ExhibitionWork {
  id: string;
  title: string;
  summary: string;
  provenance: 'design-sample' | 'real';
  image: { src: string; width: number; height: number; alt: string };
  video?: { kind: 'file' | 'external'; src: string; mime?: string };
  responsibilities?: string[];
}
export const sampleLabel = '网页设计样片 / 非个人实际项目';
export function workLabel(work: ExhibitionWork) { return work.provenance === 'design-sample' ? sampleLabel : '个人作品'; }

export interface FilmSliceItem {
  work: ExhibitionWork;
  framedViews?: boolean;
  originalSrc?: string;
}

/** Existing website-design concepts; no personal film or production credit supplied. */
export const filmWorks: readonly ExhibitionWork[] = [
  {
    id: 'signal-garden', title: '异星来信', summary: '关于遗迹、信号与生命的视觉设想。', provenance: 'design-sample',
    image: { src: signalImage, width: 1672, height: 941, alt: '粉色天空与浅水花园中，巨型石环包围悬浮镜面球体，远处有微小人物' },
  },
  {
    id: 'liquid-form', title: '流动标本', summary: '在金属与玻璃之间，观察悬浮的形态。', provenance: 'design-sample',
    image: { src: formImage, width: 1122, height: 1402, alt: '淡紫背景上，半透明玻璃与金属组成悬浮环结，下方为浅绿基座' },
  },
];

export const filmSliceWorks: readonly [FilmSliceItem, ...FilmSliceItem[]] = [
  { work: filmWorks[0]!, framedViews: true },
];

export const filmAvailability = {
  presentation: 'design-sample',
  realFilm: 'not-supplied',
  productionFrames: 'not-supplied',
  responsibilities: 'not-supplied',
  realProjectIndex: 'not-supplied',
} as const;
