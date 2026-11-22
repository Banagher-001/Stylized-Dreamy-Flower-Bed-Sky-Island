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
  waveSpeed: .36,
  waveStrength: .15,
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
    shallow: '#C3E3D8', base: '#B7D3E2', middle: '#9DBFD5', deep: '#2F6481', shade: '#779CB6', white: '#F2FAFC',
    impactLight: '#E9F9F8',
    shelfWater: '#B0C8BA', shelfTop: '#C5D0B7', shelfSide: '#9CB2A4', shelfShade: '#85A5A1',
    stoneTop: '#F0E5C1', stoneSide: '#C7CCB6', stoneShade: '#7095A1', wetStone: '#557D81', weathering: '#A3B592',
  },
} as const;
