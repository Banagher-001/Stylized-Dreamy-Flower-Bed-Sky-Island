export type RenderMode = 'native' | 'pixel';

/** Approved step 2 composition. Lighting is configured separately in lighting.ts. */
export const sceneConfig = {
  camera: {
    position: [4.5, 23, 16] as const,
    target: [0, 0.45, 0] as const,
    viewHeight: 11.3,
    near: 0.1,
    far: 100,
  },
  ground: { size: 40 },
} as const;

export const renderConfig = {
  defaultMode: 'pixel' as RenderMode,
  maxDevicePixelRatio: 2,
} as const;
