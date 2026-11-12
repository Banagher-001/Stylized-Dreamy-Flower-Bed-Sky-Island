import lawsonCover from '../assets/lawson-cover.png';
import { courtyardProject } from './experimentContent';

export type ProjectId = 'lawson' | 'courtyard';
export type ProjectTab = 'live' | 'archive';
export interface ActiveProject { readonly id: ProjectId; readonly tab: ProjectTab }
export type EmbeddedProjectState = 'prepared' | 'loading' | 'slow' | 'error' | 'ready';

export const projects = {
  lawson: {
    id: 'lawson', title: '罗森便利店', shortTitle: '罗森', kind: '交互网页场景',
    summary: '在一家微缩便利店里，切换昼夜，观察店员与车辆。',
    cover: { src: lawsonCover, width: 1280, height: 720, alt: '蓝色 LAWSON 招牌与方块樱花环绕的微缩便利店' },
    experience: { kind: 'embedded-page', entryPath: 'experiments/lawson/index.html' },
    introduction: '从街角望进灯火，再走近生活的细节。切换昼夜，观察店员与车辆，让微缩世界以自己的节奏运转。',
    features: [
      { title: '昼夜与灯光', body: '观察白天、黄昏与夜晚，使用原页面的灯光控制。' },
      { title: '店员与车辆', body: '看角色自主活动，切换车辆演示与行驶速度。' },
      { title: '镜头与场景', body: '通过原视角、屋顶及物件入口探索这间便利店。' },
    ],
  },
  courtyard: { ...courtyardProject, id: 'courtyard', shortTitle: '庭院', experience: { kind: 'host-scene' } },
} as const;

/** The same entry is used by independent opening and the future iframe adapter. */
export function resolveProjectEntry(id: ProjectId): string | undefined {
  const experience = projects[id].experience;
  return experience.kind === 'embedded-page'
    ? new URL(experience.entryPath, new URL(import.meta.env.BASE_URL, document.baseURI)).href
    : undefined;
}
