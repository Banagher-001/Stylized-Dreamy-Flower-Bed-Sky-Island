/** Prototype-only orb. The approved legacy jet/water configuration is untouched. */
export type ParticleOrbStyle = 'particles' | 'particle-wave' | 'particle-flow' | 'particle-drops';
export type OrbStyle = 'legacy' | 'lively' | ParticleOrbStyle;

export const particleOrbWave = {
  primary: { amplitude: .032, period: 4, direction: [2.5, 2, -1.55] },
  secondary: { amplitude: .008, period: 2.6, direction: [-3.1, 1.2, 4.4] },
  stemFade: [-.84, -.48],
  interiorFollow: .25,
} as const;

export const particleOrbFlow = {
  // A small circle in orb space, calibrated against the water stop's diagonal.
  axis: [.766434, -.575767, .284730],
  front: [.330778, .733779, .593426],
  offset: -.306825,
  frontTime: 3.5,
  crestWidth: [.056, .167],
  backWeight: .30,
  colors: { crest: '#E2F5FB', shade: '#4C8BAE' },
} as const;

export const particleOrbDrops = {
  clearance: .02,
  // Two release directions on the lower arc reached by the surface flow.
  beads: [
    { direction: [-.82, -.26, .51], phase: .36, formationTime: .16, radius: .024, speed: .84, vy: -.06, strength: 1.6 },
    { direction: [-.74, -.25, .62], phase: .88, formationTime: .14, radius: .019, speed: .81, vy: -.06, strength: 1.12 },
  ],
} as const;

export const orbConfig = {
  radius: .26,
  centerY: 1.37,
  floatAmplitude: .03,
  floatPeriod: 6,
  sphereSegments: [12, 8] as const,
  // The two radial waves total 3.4%; this replaces, rather than adds to, the old waves.
  shape: { first: .025, second: .009, x: .012, y: .015, z: .012, yRatio: .96, envelope: (1 + .025 + .009) * 1.012 },
  flow: { mainPeriod: 7.2, detailPeriod: 4.1, turnPeriod: 23,
    main: [2.2, 7.4, .8] as const, bend: [3.2, 0, 2] as const, bendStrength: .8,
    detail: [2.1, -3, 7] as const },
  stemRadius: .04,
  stemOverlap: .025,
  releaseLatitude: -.16,
  releaseMargin: .004,
  colors: { base: '#80B9D5', light: '#ADDCE8', side: '#4D89B2', shade: '#427192', white: '#F3FBFF' },
} as const;
