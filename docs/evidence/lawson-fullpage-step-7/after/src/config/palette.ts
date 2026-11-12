/** Step 3 art direction; colors are chosen, not exact samples of the reference. */
export const palette = {
  grassBase: '#BEDB68',
  grassLight: '#D1E581',
  grassDark: '#9EBF56',
  stoneLight: '#F3EAC4',
  stoneSide: '#D5D5B8',
  stoneShade: '#7095A1',
  treeShadow: '#117958',
  waterBase: '#B8D7E5',
  waterShade: '#86AFC8',
  waterDeep: '#356A91',
  highlight: '#F8FCED',
  flower: '#DBAAE9',
  flowerLight: '#EDC7F0',
  flowerShade: '#A67FB9',
  flowerCenter: '#F2E4B0',
  grassBlade: '#92B65B',
  grassBladeLight: '#B9D473',
  plantStem: '#7DA35B',
  plantShade: '#266E53',
} as const;

export const pagePalette = {
  paper: '#F7F7EF',
  ink: '#2E4336',
  muted: '#58664F',
  rule: '#DDE2D1',
  surface: '#FFFFFF',
} as const;

/** Swatches describe the planned palette, including materials added in later steps. */
export const paletteSwatches = [
  { name: '草地', color: palette.grassBase },
  { name: '石面', color: palette.stoneLight },
  { name: '背光', color: palette.stoneShade },
  { name: '树影', color: palette.treeShadow },
  { name: '水色', color: palette.waterBase },
  { name: '花朵', color: palette.flower },
] as const;
