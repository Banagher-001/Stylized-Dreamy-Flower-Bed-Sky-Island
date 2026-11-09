/** Prototype-only orb. The approved legacy jet/water configuration is untouched. */
export type OrbStyle = 'legacy' | 'lively';
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
