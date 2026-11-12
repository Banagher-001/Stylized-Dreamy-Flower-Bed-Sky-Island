import { sampleMagic } from './magicStyle';

export const experimentStations = [
  { id: 'C1', start: 8.7, end: 9.5, y: 2.75, label: '创作', stop: 9.14 },
  { id: 'C2', start: 9.5, end: 10.5, y: 1.8, label: '交互作品', stop: 10.05 },
  { id: 'C3', start: 10.5, end: 11.1, y: .85, label: '继续', stop: 10.83 },
] as const;
export interface ExperimentReadingFrame {
  station: (typeof experimentStations)[number];
  progress: number;
  phase: 'approach' | 'reveal' | 'read' | 'leave';
}
const smooth = (n: number) => { const t = Math.max(0, Math.min(1, n));return t * t * t * (t * (t * 6 - 15) + 10); };
export function thirdPillarHeight(h: number) {
  if (h <= 9.34) return 2.75;
  if (h < 9.65) return 2.75 - .95 * smooth((h - 9.34) / .31);
  if (h <= 10.30) return 1.8;
  if (h < 10.59) return 1.8 - .95 * smooth((h - 10.30) / .29);
  return .85;
}
export function sampleExperimentReading(h: number): ExperimentReadingFrame | undefined {
  const station = experimentStations.find((s) => h >= s.start && h < s.end);
  if (!station) return undefined;
  const progress = Math.max(0, Math.min(1, (h - station.start) / (station.end - station.start)));
  return { station, progress, phase: progress < .15 ? 'approach' : progress < .3 ? 'reveal' : progress <= .8 ? 'read' : 'leave' };
}
export function sampleExperimentPresentation(reading?: ExperimentReadingFrame, reduced = false) {
  const state = sampleMagic(reading, reduced);
  return { frame: state.veil, title: state.title, body: state.body, offset: reduced ? 0 : state.bodyY };
}
