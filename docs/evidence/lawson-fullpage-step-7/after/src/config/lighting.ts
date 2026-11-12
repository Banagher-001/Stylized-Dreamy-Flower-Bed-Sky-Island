/** Art-directed daylight; independent of the approved camera and object layout. */
export const lightingConfig = {
  sun: {
    position: [8.5, 11, -1] as const,
    intensity: 1.0,
  },
  fill: { intensity: 0.75 },
  shadows: {
    enabled: true,
    mapSize: 2048,
    extent: 8,
    near: 0.5,
    far: 32,
    bias: -0.0001,
    normalBias: 0.012,
    radius: 1,
  },
  treeShadows: {
    enabled: true,
    edgeNoiseScale: 3.2,
    edgeNoiseAmount: 0.22,
    edgeSoftness: 0.008,
    // World X/Z ellipses: one upper-left cluster and two overlapping lower-left lobes.
    // These ground-only silhouettes establish composition; leaf details come in step 5.
    patches: [
      { center: [-6.1, -3.2] as const, radius: [2.8, 1.55] as const, rotation: 0.08 },
      { center: [-3.4, 6.0] as const, radius: [3.1, 1.5] as const, rotation: -0.15 },
      { center: [-4.6, 4.4] as const, radius: [1.2, 1.4] as const, rotation: 0.2 },
    ],
  },
} as const;
