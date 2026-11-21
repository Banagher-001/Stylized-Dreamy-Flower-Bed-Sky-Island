/** Static, seeded environment detail; independent of viewport and render mode. */
export const vegetationConfig = {
  seed: 52026,
  enabled: true,
  rootHeight: 0.003,
  ground: {
    enabled: true,
    macroScale: 0.48,
    macroStrength: 0.24,
    detailScale: 17,
    detailStrength: 0.018,
    detailDensity: 0.16,
    quietCenter: [0, -5.4] as const,
    quietRadius: [1.8, 1.25] as const,
    // The seeded scatter reserves the original paving area. The final plants
    // are checked against the current stones after scattering.
    pavingReserve: { x: [3.905, 6.755], z: [0.805, 1.955] },
  },
  grass: {
    count: 240,
    // Path-local XZ roots with blade heights measured from each root.
    pavingTufts: [
      { center: [-0.773, -0.078], height: 0.076 },       // B–C opening
      { center: [-0.745075, 0.004656], height: 0.064 },  // B–C–D junction
      { center: [-0.375382, 0.001139], height: 0.070 },  // C–D opening
      { center: [-0.002447, -0.311354], height: 0.061 }, // Behind C–E
      { center: [0.734412, -0.003957], height: 0.068 },  // F–G diagonal gap
    ],
    minHeight: 0.065,
    maxHeight: 0.14,
    clearance: 0.06,
    gapWidthScale: 0.6,
  },
  flowers: {
    count: 144,
    minHeight: 0.085,
    maxHeight: 0.15,
    minDiameter: 0.085,
    maxDiameter: 0.125,
    clusters: [
      { center: [-4.2, -1.2] as const, radius: 0.62 },
      { center: [-0.9, -4.0] as const, radius: 0.58 },
      { center: [3.3, -3.2] as const, radius: 0.55 },
      { center: [4.6, 0.9] as const, radius: 0.58 },
      { center: [-0.5, 3.5] as const, radius: 0.60 },
      { center: [-2.9, 3.4] as const, radius: 0.62 },
      { center: [0.0, 4.8] as const, radius: 0.58 },
      { center: [-3.1, 0.2] as const, radius: 0.48 },
      { center: [-4.1, -4.1] as const, radius: 0.55 },
      { center: [1.6, -5.2] as const, radius: 0.52 },
      { center: [-3.4, 1.3] as const, radius: 0.48 },
      { center: [3.6, 2.7] as const, radius: 0.50 },
    ],
  },
  treeDetail: {
    enabled: true,
    branchScale: 2.2,
    leafScale: 18,
    edgeBreakup: 0.12,
    gapStrength: 1,
  },
} as const;
