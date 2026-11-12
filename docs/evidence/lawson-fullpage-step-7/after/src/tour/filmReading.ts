/** Second-pillar coordinates and scroll-only presentation, independent of assets. */
export const filmStations = [
  { id: 'B1', start: 4.4, end: 5.4, y: 2.8, label: '影像展映', stop: 4.95 },
  { id: 'B2', start: 5.4, end: 6.4, y: 2.15, label: '画面切片', stop: 5.95 },
  { id: 'B3', start: 6.4, end: 7.2, y: 1.5, label: '视觉探索', stop: 6.84 },
  { id: 'B4', start: 7.2, end: 8, y: .85, label: '影像余韵', stop: 7.64 },
] as const;

export interface FilmReadingFrame {
  station: (typeof filmStations)[number];
  progress: number;
  phase: 'approach' | 'reveal' | 'read' | 'leave';
}
const clamp = (n: number) => Math.max(0, Math.min(1, n));
const smooth = (n: number) => { const t = clamp(n);return t * t * t * (t * (t * 6 - 15) + 10); };
const interval = (n: number, a: number, b: number) => smooth((n - a) / (b - a));

export function secondPillarHeight(h: number) {
  if (h < 5.2) return 2.8;
  if (h < 5.55) return 2.8 - .65 * smooth((h - 5.2) / .35);
  if (h < 6.2) return 2.15;
  if (h < 6.52) return 2.15 - .65 * smooth((h - 6.2) / .32);
  if (h < 7.04) return 1.5;
  if (h < 7.32) return 1.5 - .65 * smooth((h - 7.04) / .28);
  return .85;
}

export function sampleFilmReading(h: number): FilmReadingFrame | undefined {
  const station = filmStations.find((s) => h >= s.start && h < s.end);
  if (!station) return undefined;
  const progress = clamp((h - station.start) / (station.end - station.start));
  const phase = progress < .15 ? 'approach' : progress < .3 ? 'reveal' : progress <= .8 ? 'read' : 'leave';
  return { station, progress, phase };
}

export function sampleFilmPresentation(reading?: FilmReadingFrame, reducedMotion = false) {
  const u = reading?.progress ?? 0;
  const frame = reading ? interval(u, .15, .22) * (1 - interval(u, .9, 1)) : 0;
  const media = reading ? interval(u, .18, .26) * (1 - interval(u, .82, .96)) : 0;
  const title = reading ? interval(u, .21, .27) * (1 - interval(u, .86, .99)) : 0;
  const body = reading ? interval(u, .24, .3) * (1 - interval(u, .8, .94)) : 0;
  return { frame, media, title, body, offset: reducedMotion ? 0 : (u > .8 ? -1 : 1) * 8 * (1 - media) };
}
