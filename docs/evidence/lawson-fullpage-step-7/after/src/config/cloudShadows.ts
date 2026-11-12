/** Broad, repeatable cloud shade in world units; no texture or shadow-map pass. */
export const cloudShadowConfig = {
  period: 32,
  speed: .22,
  softness: [.46, 1.30] as const,
  unionSoftness: .24,
  patches: [
    { along: -3.0, across: -1.4, radius: [4.6, 3.3] as const, density: 1.0 },
    { along: 12.0, across: 4.6, radius: [5.6, 3.7] as const, density: .88 },
  ] as const,
  response: { ground: .18, stone: .14, foliage: .13, flower: .10, water: .075, orb: .05, jet: .045 },
} as const;
