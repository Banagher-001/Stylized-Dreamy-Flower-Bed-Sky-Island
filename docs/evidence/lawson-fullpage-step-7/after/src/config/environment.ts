/** Subtle environment motion; the seeded plant distribution is configured separately. */
export const environmentConfig = {
  seed: 82026,
  enabled: true,
  wind: {
    direction: [1, 0.32] as const,
    grassAngle: 8 * Math.PI / 180,
    flowerAngle: 6 * Math.PI / 180,
    gapAngle: 2.5 * Math.PI / 180,
    periods: [5.8, 4.4] as const,
    gustPeriod: 16,
  },
  canopy: { period: 10.5, secondaryPeriod: 12, displacement: 0.045, holeShade: 0.025 },
  petals: { enabled: false, capacity: 8, period: 11, lifetime: 6, drift: 0.16, minHeight: 0.07, maxHeight: 0.65 },
} as const;

export interface EnvironmentOptions {
  enabled: boolean;
  wind: boolean;
  canopy: boolean;
  petals: boolean;
}

export function resolveEnvironmentOptions(query: URLSearchParams): EnvironmentOptions {
  return {
    enabled: query.get('env') !== 'off' && environmentConfig.enabled,
    wind: query.get('wind') !== 'off',
    canopy: query.get('canopy') !== 'off',
    petals: query.get('petals') === 'on' || environmentConfig.petals.enabled,
  };
}
