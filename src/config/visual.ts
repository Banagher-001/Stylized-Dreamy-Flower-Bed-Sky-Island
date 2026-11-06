export const pixelResolutions = [320, 384, 448] as const;
export type PixelResolution = typeof pixelResolutions[number];
export type FinishProfile = 'clean' | 'soft';

export interface PixelOptions {
  resolution: PixelResolution;
  finish: FinishProfile;
  storage: 'auto' | 'byte';
}

/** A fixed scene grid preserves world detail across viewport/DPR changes. */
export const visualConfig = {
  resolution: 384 as PixelResolution,
  finish: 'clean' as FinishProfile,
  finishes: {
    clean: { levels: 0, dither: 0 },
    soft: { levels: 64, dither: 0.18 },
  },
} as const;

/** Comparison controls live in URLs/configuration, not in the product toolbar. */
export function resolveVisualOptions(query: URLSearchParams): PixelOptions {
  const requested = Number(query.get('pixelSize'));
  return {
    resolution: pixelResolutions.some(size => size === requested) ? requested as PixelResolution : visualConfig.resolution,
    finish: query.get('finish') === 'soft' ? 'soft' : visualConfig.finish,
    storage: 'auto',
  };
}
