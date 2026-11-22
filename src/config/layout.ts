/** World units, Y up. Every object group is anchored at ground level. */
export const layoutConfig = {
  fountain: {
    position: [0.12, 0, 0] as const,
    rotationY: 0.12,
    baseRadius: 2.76,
    baseHeight: 0.12,
    outerRadius: 2.65,
    innerRadius: 2.28,
    rimHeight: 0.46,
    waterHeight: 0.32,
    pedestalFootSize: 0.9,
    pedestalFootHeight: 0.12,
    pedestalSize: 0.64,
    pedestalHeight: 0.62,
    pedestalCapSize: 0.82,
    pedestalCapHeight: 0.1,
  },
  columnShape: {
    baseWidth: 1.04,
    baseDepth: 1.08,
  },
  columns: [
    { name: 'columnUpperLeft', position: [-2.34, 0, -2.9] as const, rotationY: 0 },
    { name: 'columnRight', position: [4.41, 0, -1.0] as const, rotationY: 0 },
    { name: 'columnLower', position: [2.96, 0, 5.09] as const, rotationY: 0 },
  ],
  wall: {
    position: [-4.25, 0, 2.25] as const,
    rotationY: -0.5,
    length: 4.1,
    depth: 0.38,
    height: 0.55,
    baseHeight: 0.12,
    baseDepth: 0.62,
    capHeight: 0.1,
    capDepth: 0.48,
    endSize: 0.64,
    endHeight: 0.25,
  },
  path: {
    position: [5.33, 0, 1.38] as const,
    rotationY: 0,
    // Center and dimensions are measured in the path group's XZ plane.
    // Cuts run from the -X/-Z corner toward +X first.
    // Each lower bevel sits below grade and each chip ends above it.
    stones: [
      {
        id: 'A', center: [-1.055, -0.355], width: 0.34, depth: 0.33, rotationDegrees: 12,
        cuts: [0.073, 0.019, 0.053, 0.025],
        profile: { exposedHeight: 0.085, embeddedDepth: 0.014, bevel: 0.011, chipVertex: 7, chipSize: 0.062 },
      },
      {
        id: 'B', center: [-1.111, 0.205], width: 0.66, depth: 0.44, rotationDegrees: -7,
        cuts: [0.025, 0.064, 0.036, 0.049],
        profile: { exposedHeight: 0.093, embeddedDepth: 0.016, bevel: 0.014, chipVertex: 5, chipSize: 0.079 },
      },
      {
        id: 'C', center: [-0.465, -0.275], width: 0.45, depth: 0.33, rotationDegrees: -9,
        cuts: [0.058, 0.021, 0.047, 0.032],
        profile: { exposedHeight: 0.078, embeddedDepth: 0.017, bevel: 0.009, chipVertex: 0, chipSize: 0.035 },
      },
      {
        id: 'D', center: [-0.381, 0.305], width: 0.59, depth: 0.43, rotationDegrees: 6,
        cuts: [0.033, 0.055, 0.023, 0.071],
        profile: { exposedHeight: 0.096, embeddedDepth: 0.015, bevel: 0.013, chipVertex: 5, chipSize: 0.044 },
      },
      {
        id: 'E', center: [0.207, -0.014], width: 0.31, depth: 0.69, rotationDegrees: -16,
        cuts: [0.028, 0.068, 0.015, 0.053],
        profile: { exposedHeight: 0.088, embeddedDepth: 0.014, bevel: 0.010, chipVertex: 1, chipSize: 0.061 },
      },
      {
        id: 'F', center: [0.765, -0.259], width: 0.51, depth: 0.32, rotationDegrees: 10,
        cuts: [0.066, 0.022, 0.055, 0.031],
        profile: { exposedHeight: 0.076, embeddedDepth: 0.018, bevel: 0.008, chipVertex: 2, chipSize: 0.027 },
      },
      {
        id: 'G', center: [0.659, 0.279], width: 0.53, depth: 0.40, rotationDegrees: -9,
        cuts: [0.019, 0.059, 0.041, 0.072],
        profile: { exposedHeight: 0.090, embeddedDepth: 0.015, bevel: 0.012, chipVertex: 4, chipSize: 0.049 },
      },
      {
        id: 'H', center: [1.237, 0.170], width: 0.43, depth: 0.41, rotationDegrees: 8,
        cuts: [0.053, 0.028, 0.073, 0.021],
        profile: { exposedHeight: 0.084, embeddedDepth: 0.015, bevel: 0.011, chipVertex: 3, chipSize: 0.075 },
      },
    ],
  },
} as const;
