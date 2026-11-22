/** World-unit details. Seeds/presets are stable across reloads. */
export const stoneConfig = {
  bevel: 0.028,
  cornerCut: 0.042,
  colorVariation: 0.045,
  joints: { width: 0.038, recess: 0.045 },
  wall: { bodyBlocks: 3, capBlocks: 2 },
} as const;
