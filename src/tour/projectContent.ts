import lawsonCover from '../assets/lawson-cover.png';
import bottleOceanCover from '../assets/bottle-ocean-cover.png';
import { courtyardProject } from './experimentContent';

export const projectOrder = ['lawson', 'bottle-ocean', 'courtyard'] as const;
export type ProjectId = typeof projectOrder[number];
export type EmbeddedProjectId = Exclude<ProjectId, 'courtyard'>;
export type ProjectTab = 'live' | 'archive';
export type EmbeddedProjectState = 'prepared' | 'loading' | 'slow' | 'error' | 'ready';

export const projects = {
  lawson: {
    id: 'lawson', label: 'LAWSON', title: '罗森便利店',
    summary: '在一家微缩便利店里，切换昼夜，观察店员与车辆。',
    cover: { src: lawsonCover, width: 1280, height: 720, alt: '蓝色 LAWSON 招牌与方块樱花环绕的微缩便利店' },
    experience: { kind: 'embedded-page', entryPath: 'experiments/lawson/index.html' },
    introduction: '从街角望进灯火，再走近生活的细节。切换昼夜，观察店员与车辆，让微缩世界以自己的节奏运转。',
    archive: { kicker: 'LAWSON / INTERACTIVE WORLD', headline: ['一间店，', '几个日夜。'], caption: '罗森便利店 · 场景画面' },
    features: [
      { title: '昼夜与灯光', body: '观察白天、黄昏与夜晚，使用原页面的灯光控制。' },
      { title: '店员与车辆', body: '看角色自主活动，切换车辆演示与行驶速度。' },
      { title: '镜头与场景', body: '通过原视角、屋顶及物件入口探索这间便利店。' },
    ],
  },
  'bottle-ocean': {
    id: 'bottle-ocean', label: 'BOTTLE OCEAN', title: '瓶中海洋',
    summary: '黄昏海岸的一只玻璃瓶，装着起伏的海浪与随波浮沉的三桅帆船。',
    cover: { src: bottleOceanCover, width: 1920, height: 1080, alt: '黄昏海岸的玻璃瓶中，三桅帆船随微型海浪起伏' },
    experience: { kind: 'embedded-page', entryPath: 'experiments/bottle-ocean/index.html' },
    introduction: '拖动镜头绕过玻璃，看浪头托起船身；调整风、浪与水位，再在沙地留下自己的布置。',
    archive: { kicker: 'BOTTLE OCEAN / INTERACTIVE WORLD', headline: ['让一片海，', '托起一艘船。'], caption: '瓶中海洋 · 黄昏海岸' },
    features: [
      { title: '海浪与船体', body: '波高、速度、方向与水位变化，带动船体浮沉、俯仰和横摇。' },
      { title: '黄昏像素海岸', body: '玻璃瓶、外海与灯塔组成微缩海岸，可以调节夕阳、亮度和像素强度。' },
      { title: '镜头与沙盒', body: '切换五个镜头，在沙地放置石头和贝壳，撤销或恢复布置，并保存当前场景。' },
    ],
  },
  courtyard: { ...courtyardProject, id: 'courtyard', label: 'COURTYARD', shortTitle: '庭院', primaryAction: '现场体验', experience: { kind: 'host-scene' } },
} as const;

/** Resolve original pages under the site's production base path. */
export function resolveProjectEntry(id: ProjectId): string | undefined {
  const experience = projects[id].experience;
  return experience.kind === 'embedded-page'
    ? new URL(experience.entryPath, new URL(import.meta.env.BASE_URL, document.baseURI)).href
    : undefined;
}
