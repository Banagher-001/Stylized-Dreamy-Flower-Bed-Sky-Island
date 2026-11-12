/** Water-only art and motion; approved architecture, vegetation and light stay intact. */
export const waterConfig = {
  enabled: true,
  seed: 62026,
  initialTime: 2,
  maxFrameDelta: 0.05,
  colors: {
    base: '#BED4DF',
    deep: '#245B80',
    shade: '#7FA3BF',
    highlight: '#F2FAFC',
    jet: '#82B0D1',
  },
  surface: { flowSpeed: 0.055, reflectionThreshold: 0.65, waveSpeed: 0.45, waveStrength: 0.24 },
  jet: { emitterHeight: 1.18, radius: 0.18, stemRadius: 0.055, pulse: 0.025 },
  drops: {
    capacity: 32,
    period: 2,
    gravity: 3,
    minVerticalSpeed: 0.7,
    maxVerticalSpeed: 0.9,
    minHorizontalSpeed: 0.95,
    maxHorizontalSpeed: 1.1,
    minRadius: 0.014,
    maxRadius: 0.024,
  },
  ripples: { capacity: 8, lifetime: 0.65, speed: 0.30, strength: 0.58 },
} as const;
