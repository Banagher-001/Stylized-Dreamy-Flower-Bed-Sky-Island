/** World-unit details. Seeds/presets are stable across reloads. */
export const stoneConfig = {
  bevel: 0.028,
  cornerCut: 0.042,
  colorVariation: 0.045,
  joints: { width: 0.038, recess: 0.045 },
  column: {
    layerRatios: [1.07, 0.96, 1.03, 0.94],
    layerSeeds: [11, 29, 47],
    layerChips: [0, 0.028, 0.052],
    baseBevel: 0.024,
    capBevel: 0.038,
    profiles: [
      { layers: [0, 1, 0, 2], offsets: [-0.012, 0.012, -0.008, 0], capCorner: 2, capChip: 0.12 },
      { layers: [1, 2, 0, 1], offsets: [0.008, -0.01, 0.01, 0], capCorner: 1, capChip: 0.095 },
      { layers: [2, 0, 1, 0], offsets: [-0.008, 0.012, -0.008, 0], capCorner: 3, capChip: 0.145 },
    ],
  },
  fountain: { copingHeight: 0.14, jointWidth: 0.032, bevel: 0.024, chippedSegments: [1, 5], chipSize: 0.1 },
  wall: { bodyBlocks: 3, capBlocks: 2 },
  path: { bevel: 0.014, cornerCut: 0.045, chippedSlabs: [1, 4, 6], chipSize: 0.065 },
} as const;
