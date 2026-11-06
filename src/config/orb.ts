/** Prototype-only orb. The approved legacy jet/water configuration is untouched. */
export type OrbStyle = 'legacy' | 'lively';
export const orbConfig = {
  radius: .26,
  centerY: 1.37,
  floatAmplitude: .03,
  floatPeriod: 6,
  sphereSegments: [12, 8] as const,
  shape: { first: .018, second: .009, x: .012, y: .015, z: .012, yRatio: .96, envelope: 1.06 },
  stemRadius: .04,
  stemOverlap: .025,
  releaseLatitude: -.16,
  releaseMargin: .004,
  colors: { base: '#80B9D5', light: '#ADDCE8', side: '#4D89B2', shade: '#427192', white: '#F3FBFF' },
} as const;
