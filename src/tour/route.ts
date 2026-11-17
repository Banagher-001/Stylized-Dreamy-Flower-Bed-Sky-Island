import { sceneConfig } from '../config/scene';
import { firstPillarHeight, samplePillarReading } from './reading';
import type { PillarReadingFrame } from './reading';
import { secondPillarHeight, sampleFilmReading } from './filmReading';
import type { FilmReadingFrame } from './filmReading';
import { thirdPillarHeight, sampleExperimentReading } from './experimentReading';
import type { ExperimentReadingFrame } from './experimentReading';

export type Point3 = [number, number, number];
export type PoseKey = 'O' | 'A' | 'A2' | 'A3' | 'B' | 'B2' | 'B3' | 'B4' | 'C' | 'C2' | 'C3' | 'W';
export interface TourPose {
  position: Point3;
  target: Point3;
  viewHeight: number;
  screenX: number;
}
export interface TourSample {
  h: number;
  stage: string;
  chapter: 'overview' | 'about' | 'films' | 'experiments' | 'water';
  title: string;
  note: string;
  pose: TourPose;
  hold: boolean;
  column?: string;
  reading?: PillarReadingFrame;
  filmReading?: FilmReadingFrame;
  experimentReading?: ExperimentReadingFrame;
}

export const tourTotalH = 12.3;
/** A scroll-distance hold inside the original T3W segment, not a timed pause. */
export const waterHold = { start: 11.45, stop: 11.5, end: 11.55 } as const;
export const tourStops = [
  { id: 'overview', label: '全景', h: 0 },
  { id: 'about', label: '01 关于我', h: 1.74 },
  { id: 'films', label: '02 AI 影像', h: 4.95 },
  { id: 'experiments', label: '03 交互实验', h: 9.14 },
  { id: 'water', label: '水潭', h: 11.5 },
] as const;

/** Three reading pillars, connected by the original sixteen scroll segments. */
export const tourStages = [
  { id: 'S00', start: 0, end: 0.5 },
  { id: 'T01', start: 0.5, end: 1.3 },
  { id: 'A1', start: 1.3, end: 2.1 },
  { id: 'A2', start: 2.1, end: 2.9 },
  { id: 'A3', start: 2.9, end: 3.7 },
  { id: 'T12', start: 3.7, end: 4.4 },
  { id: 'B1', start: 4.4, end: 5.4 },
  { id: 'B2', start: 5.4, end: 6.4 },
  { id: 'B3', start: 6.4, end: 7.2 },
  { id: 'B4', start: 7.2, end: 8 },
  { id: 'T23', start: 8, end: 8.7 },
  { id: 'C1', start: 8.7, end: 9.5 },
  { id: 'C2', start: 9.5, end: 10.5 },
  { id: 'C3', start: 10.5, end: 11.1 },
  { id: 'T3W', start: 11.1, end: 11.8 },
  { id: 'S99', start: 11.8, end: 12.3 },
] as const;

export const tourPoses: Record<PoseKey, TourPose> = {
  O: { position: [...sceneConfig.camera.position], target: [...sceneConfig.camera.target], viewHeight: sceneConfig.camera.viewHeight, screenX: 0.5 },
  A: { position: [-1.14, 6.95, 6.1], target: [-2.34, 2.75, -2.9], viewHeight: 3.6, screenX: 0.34 },
  A2: { position: [-1.14, 6, 6.1], target: [-2.34, 1.8, -2.9], viewHeight: 3.6, screenX: 0.34 },
  A3: { position: [-1.14, 5.05, 6.1], target: [-2.34, 0.85, -2.9], viewHeight: 4.8, screenX: 0.20 },
  B: { position: [5.61, 7, 8], target: [4.41, 2.8, -1], viewHeight: 3.8, screenX: 0.28 },
  B2: { position: [5.61, 6.35, 8], target: [4.41, 2.15, -1], viewHeight: 3.8, screenX: 0.28 },
  B3: { position: [5.61, 5.7, 8], target: [4.41, 1.5, -1], viewHeight: 3.8, screenX: 0.28 },
  B4: { position: [5.61, 5.05, 8], target: [4.41, .85, -1], viewHeight: 3.8, screenX: 0.28 },
  C: { position: [4.16, 6.95, 14.09], target: [2.96, 2.75, 5.09], viewHeight: 3.6, screenX: 0.34 },
  C2: { position: [4.16, 6, 14.09], target: [2.96, 1.8, 5.09], viewHeight: 3.6, screenX: 0.34 },
  C3: { position: [4.16, 5.05, 14.09], target: [2.96, .85, 5.09], viewHeight: 3.6, screenX: 0.34 },
  W: { position: [2.32, 11.15, 7.5], target: [0.12, 0.65, 0], viewHeight: 6.2, screenX: 0.5 },
};

interface Travel {
  from: PoseKey;
  to: PoseKey;
  eyeControls: [Point3, Point3];
  targetControls: [Point3, Point3];
  heightControls: [number, number];
}
const travels: Record<string, Travel> = {
  T01: { from: 'O', to: 'A', eyeControls: [[3, 20, 13], [0.6, 12, 8.5]], targetControls: [[-0.8, 1.6, -0.8], [-2, 2.9, -2.4]], heightControls: [11.3, 7] },
  T12: { from: 'A3', to: 'B', eyeControls: [[0.3, 10.1, 6.3], [4.9, 11.55, 7]], targetControls: [[-1.5, 2.8, -5.2], [3.1, 3.55, -4.5]], heightControls: [8.8, 8.8] },
  T23: { from: 'B4', to: 'C', eyeControls: [[8.8, 11.3, 11.7], [8.4, 11.3, 15.1]], targetControls: [[7, 3.3, 0.2], [6.6, 3.3, 3.6]], heightControls: [8.8, 8.8] },
  T3W: { from: 'C3', to: 'W', eyeControls: [[7.3, 13.7, 14], [5, 13, 12.5]], targetControls: [[4.8, 1.7, 3], [2.5, 1, 1.5]], heightControls: [8.6, 7.5] },
  WIDE: { from: 'W', to: 'O', eyeControls: [[3, 15, 10], [4, 21, 14]], targetControls: [[0.1, 0.6, 0], [0, 0.5, 0]], heightControls: [7, 10.5] },
};

const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n));
const smoother = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);
function cubic(a: number, b: number, c: number, d: number, t: number) {
  const u = 1 - t;
  return u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d;
}
function point(a: Point3, b: Point3, c: Point3, d: Point3, t: number): Point3 {
  return [0, 1, 2].map((i) => cubic(a[i]!, b[i]!, c[i]!, d[i]!, t)) as Point3;
}
function copy(pose: TourPose): TourPose { return { ...pose, position: [...pose.position], target: [...pose.target] }; }
function travel(key: string, progress: number): TourPose {
  const spec = travels[key]!;
  const a = tourPoses[spec.from], b = tourPoses[spec.to];
  const t = smoother(clamp(progress, 0, 1));
  return {
    position: point(a.position, ...spec.eyeControls, b.position, t),
    target: point(a.target, ...spec.targetControls, b.target, t),
    viewHeight: cubic(a.viewHeight, ...spec.heightControls, b.viewHeight, t),
    screenX: a.screenX + (b.screenX - a.screenX) * t,
  };
}

export function sampleTour(value: number): TourSample {
  const h = clamp(Number.isFinite(value) ? value : 0, 0, tourTotalH);
  const stage = tourStages.find((s) => h < s.end) ?? tourStages[tourStages.length - 1]!;
  const base = { h, stage: stage.id };
  if (h < 0.5 || h >= 11.8) return { ...base, chapter: 'overview', title: h < 0.5 ? '让想象，动起来。' : 'sakan · 张辰翰', note: 'AI动画 · 视觉创作 · 交互实验', pose: copy(tourPoses.O), hold: true };
  if (h < 1.3) return { ...base, chapter: 'about', title: '走近，关于我的故事', note: '沿石柱向下，阅读身份、经历与工具。', pose: travel('T01', (h - 0.5) / 0.8), hold: false };
  if (h < 3.7) {
    const pose = copy(tourPoses.A);
    const height = firstPillarHeight(h);
    pose.position[1] += height - pose.target[1];
    pose.target[1] = height;
    const wide = smoother(clamp((h - 2.74) / .28, 0, 1));
    pose.viewHeight += (tourPoses.A3.viewHeight - tourPoses.A.viewHeight) * wide;
    pose.screenX += (tourPoses.A3.screenX - tourPoses.A.screenX) * wide;
    return { ...base, chapter: 'about', title: '01 / 关于我', note: '沿柱阅读 · 上、中、下三段随滚动交接。', pose, hold: !(h > 1.94 && h < 2.22 || h > 2.74 && h < 3.02), column: 'columnUpperLeft', reading: samplePillarReading(h) };
  }
  if (h < 4.4) return { ...base, chapter: 'films', title: '关于我 / AI影像', note: '01 ↔ 02 · 移步，继续看见创作。', pose: travel('T12', (h - 3.7) / 0.7), hold: false };
  if (h < 8) {
    const pose = copy(tourPoses.B);
    const height = secondPillarHeight(h);
    pose.position[1] += height - pose.target[1];pose.target[1] = height;
    return { ...base, chapter: 'films', title: '02 / AI 影像', note: '展映 · 切片 · 探索，沿柱向下展开。', pose, hold: !(h > 5.2 && h < 5.55 || h > 6.2 && h < 6.52 || h > 7.04 && h < 7.32), column: 'columnRight', filmReading: sampleFilmReading(h) };
  }
  if (h < 8.7) return { ...base, chapter: 'experiments', title: 'AI影像 / 交互实验', note: '02 ↔ 03 · 从画面，走进可以探索的世界。', pose: travel('T23', (h - 8) / 0.7), hold: false };
  if (h < 11.1) {
    const pose = copy(tourPoses.C), height = thirdPillarHeight(h);
    pose.position[1] += height - pose.target[1];pose.target[1] = height;
    return { ...base, chapter: 'experiments', title: '03 / 交互实验', note: '从想法到交互，进入一座可以停留的庭院。', pose, hold: !(h > 9.34 && h < 9.65 || h > 10.30 && h < 10.59), column: 'columnLower', experimentReading: sampleExperimentReading(h) };
  }
  if (h < waterHold.start) return { ...base, chapter: 'water', title: '回到中央水潭', note: '沿着水面，重新看见庭院。', pose: travel('T3W', (h - 11.1) / (waterHold.start - 11.1)), hold: false };
  if (h <= waterHold.end) return { ...base, chapter: 'water', title: '停一会儿，看水与风', note: '水球轻浮，庭院仍在生长。', pose: copy(tourPoses.W), hold: true };
  return { ...base, chapter: 'water', title: '重新看见庭院', note: '把这一座庭院，留在想象里。', pose: travel('WIDE', (h - waterHold.end) / (11.8 - waterHold.end)), hold: false };
}

/** Keep approved scene content, adapting only the camera frame for viewport shape. */
export function resolveTourPose(pose: TourPose, aspect: number) {
  const ratio = Math.max(0.1, aspect);
  const viewHeight = pose.viewHeight * Math.max(1, 1 / ratio);
  const dx = pose.position[0] - pose.target[0], dz = pose.position[2] - pose.target[2];
  const distance = Math.hypot(dx, dz);
  const pan = (0.5 - pose.screenX) * viewHeight * ratio;
  const shift: Point3 = [dz / distance * pan, 0, -dx / distance * pan];
  return {
    position: pose.position.map((v, i) => v + shift[i]!) as Point3,
    target: pose.target.map((v, i) => v + shift[i]!) as Point3,
    viewHeight,
  };
}
