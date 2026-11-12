export interface MagicReadingFrame { station: { id: string }; progress: number; }

/** Local to the reading prototype; the courtyard palette and lighting stay intact. */
export const magicStyle = {
  stone: { top: '#A4B398', side: '#405B55', shade: '#263E3A' },
  joint: { top: '#354B41', side: '#253D35', shade: '#1B302D' },
  ink: '#EDF4E6', title: '#FFF1CD', cool: '#C4DFDB', gold: '#DCCB9D', lilac: '#CDBFE4', etch: '#657B6C',
  veil: '#223B33', sigilSize: 0.54, surfaceOffset: 0.008, faceMargin: 0.05,
  pool: 24, mobilePool: 12, readCount: 8, mobileReadCount: 4,
} as const;

const unit = (n: number) => Math.max(0, Math.min(1, n));
const smooth = (n: number) => { const t = unit(n);return t * t * t * (t * (t * 6 - 15) + 10); };
const interval = (u: number, a: number, b: number) => smooth((u - a) / (b - a));
export function sampleMagic(reading?: MagicReadingFrame, reducedMotion = false) {
  const u = reading?.progress ?? 0;
  const trace = reading ? interval(u, 0, .15) * (1 - interval(u, .96, 1)) : 0;
  const glyph = reading ? interval(u, 0, .15) * (1 - interval(u, .9, 1)) : 0;
  const title = reading ? interval(u, .15, .22) * (1 - interval(u, .88, 1)) : 0;
  const body = reading ? interval(u, .2, .3) * (1 - interval(u, .8, .96)) : 0;
  const dust = reading && !reducedMotion ? interval(u, .08, .2) * (1 - interval(u, .88, 1)) : 0;
  const burst = reducedMotion || !reading ? 0 : u < .3 ? Math.sin(Math.PI * unit((u - .08) / .22)) ** 2 : u > .8 ? Math.sin(Math.PI * unit((u - .8) / .2)) ** 2 : 0;
  return { trace: reducedMotion && reading ? 1 : trace, glyph: reducedMotion ? (title > 0 ? 1 : 0) : glyph, title, body, veil: Math.max(title, body), dust, burst, disperse: reducedMotion ? 0 : interval(u, .8, 1), titleY: (u > .8 ? -1 : 1) * 6 * (1 - title), bodyY: (u > .8 ? -1 : 1) * 8 * (1 - body) };
}
export type MagicFrame = ReturnType<typeof sampleMagic>;
