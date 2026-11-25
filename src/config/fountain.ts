import { layoutConfig } from './layout';

/** Shared geometry and colour coordinates for the shallows on study edge 6. */
export const fountainShelf = {
  side: 0,
  origin: [layoutConfig.fountain.innerRadius, 0],
  tangent: [-Math.sin(Math.PI / 8), -Math.cos(Math.PI / 8)],
  edgeLength: layoutConfig.fountain.innerRadius * 2 * Math.sin(Math.PI / 8),
  bedInset: .015,
  thickness: .078,
  stones: [
    { span: [.17, .494], reach: .195, bankY: .342, lipY: .300, fall: -.006, cut: [.086, .117, .050, .096] },
    { span: [.507, .74], reach: .162, bankY: .338, lipY: .299, fall: .006, cut: [.044, .083, .081, .105] },
  ],
} as const;

export type FountainStyle = 'legacy' | 'refined';
export const fountainConfig = {
  flowSpeed: .035,
  windRipples: {
    wavelength: .36,
    speed: .17,
    halfWidth: .0105,
    strength: .51,
    light: '#D4ECF8',
  },
  waterOptics: {
    refractiveIndex: 1.333,
    normalTilt: .018,
    absorption: 3.8,
  },
  cloudReflection: {
    heightAboveWater: 2.8,
    driftSpeed: .06,
    repeatDistance: 5.4,
    waveInfluence: .23,
    rearCenter: [.002, -3.554] as const,
    nearCenter: [-1.331, -.937] as const,
    body: '#E6EFF4',
    edge: '#BCD4E5',
  },
  shoreFoam: {
    white: '#F4FAF5',
    shade: '#C2DEE9',
    // Along-edge spans and distances from the inner wall, in pool-local units.
    // Edge 6 uses the individual stone profiles in fountainShelf.
    patches: [
      { edge: 4, span: [.19, .49], contact: .006, reach: .033, opacity: .52, seed: 8.1, fragments: 0 },
      { edge: 5, span: [-.33, -.02], contact: .004, reach: .064, opacity: .84, seed: 3.6, fragments: 0 },
      { edge: 5, span: [.31, .60], contact: .003, reach: .055, opacity: .76, seed: 8.8, fragments: 0 },
      { edge: 7, span: [-.74, -.33], contact: .077, reach: .174, opacity: .94, seed: 5.3, fragments: .64 },
      { edge: 7, span: [.02, .47], contact: .078, reach: .168, opacity: .89, seed: 4.4, fragments: .46 },
      { edge: 8, span: [-.76, -.31], contact: .147, reach: .243, opacity: .94, seed: 2.7, fragments: .54 },
      { edge: 8, span: [-.19, .29], contact: .148, reach: .247, opacity: 1, seed: 6.4, fragments: .66 },
      { edge: 8, span: [.48, .83], contact: .148, reach: .235, opacity: .88, seed: 7.8, fragments: .46 },
    ],
  },
  // Pool-local centre of the two landing paths, used to quiet the background waves.
  dropFocus: [-.72, .53] as const,
  impact: {
    contactDuration: .082,
    contactRadius: .032,
    startRadius: .025,
    primaryHalfWidth: .013,
    secondaryHalfWidth: .008,
    secondaryDelay: .15,
    strength: { contact: .62, primary: .42, secondary: .22 },
  },
  edgeGlintWidth: [.022, .049] as const,
  clearWaterRadius: [.96, 1.22] as const,
  colors: {
    shallow: '#A7D7D9', base: '#79B7E7', middle: '#63A7DC', deep: '#285D86', shade: '#3E7099', white: '#F2FAFC',
    impactLight: '#E9F9F8',
    shelfWater: '#B3D4B6', submergedLip: '#66A6AF',
    shelfTop: '#C5D0B7', shelfSide: '#9CB2A4', shelfShade: '#85A5A1',
    stoneTop: '#F0E5C1', stoneSide: '#C7CCB6', stoneShade: '#7095A1', wetStone: '#557D81', weathering: '#A3B592',
  },
} as const;
