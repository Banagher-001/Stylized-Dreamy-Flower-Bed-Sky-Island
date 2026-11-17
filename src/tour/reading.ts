/** First-pillar scroll coordinates; public About copy lives in about-refresh/content.ts. */
export const readingStations = [
  { id: 'A1', start: 1.3, end: 2.1, y: 2.75, label: '上部', stop: 1.74 },
  { id: 'A2', start: 2.1, end: 2.9, y: 1.8, label: '中部', stop: 2.54 },
  { id: 'A3', start: 2.9, end: 3.7, y: 0.85, label: '下部', stop: 3.34 },
] as const;

export interface PillarReadingFrame {
  station: (typeof readingStations)[number];
  progress: number;
  opacity: number;
  offsetY: number;
  phase: 'approach' | 'reveal' | 'read' | 'leave';
}

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const smooth = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);

export function firstPillarHeight(h: number) {
  if (h < 1.94) return readingStations[0].y;
  if (h < 2.22) return 2.75 - 0.95 * smooth(clamp((h - 1.94) / 0.28));
  if (h < 2.74) return readingStations[1].y;
  if (h < 3.02) return 1.8 - 0.95 * smooth(clamp((h - 2.74) / 0.28));
  return readingStations[2].y;
}

export function samplePillarReading(h: number): PillarReadingFrame | undefined {
  const station = readingStations.find((item) => h >= item.start && h < item.end);
  if (!station) return undefined;
  const progress = clamp((h - station.start) / (station.end - station.start));
  const phase = progress < 0.15 ? 'approach' : progress < 0.3 ? 'reveal' : progress <= 0.8 ? 'read' : 'leave';
  const opacity = phase === 'approach' ? 0 : phase === 'reveal' ? smooth(clamp((progress - 0.15) / 0.15)) : phase === 'read' ? 1 : 1 - smooth(clamp((progress - 0.8) / 0.2));
  const offsetY = phase === 'leave' ? -10 * (1 - opacity) : 10 * (1 - opacity);
  return { station, progress, phase, opacity, offsetY };
}
