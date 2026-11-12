/** Opt-in courtyard pool finish. Legacy water/jet parameters remain untouched. */
export type FountainStyle = 'legacy' | 'refined';
export const fountainConfig = {
  flowSpeed: .035,
  waveSpeed: .36,
  waveStrength: .15,
  rippleStrength: .42,
  foamWidth: [.015, .04] as const,
  colors: {
    shallow: '#B4DAD9', base: '#BED4DF', middle: '#95BECF', deep: '#245B80', shade: '#7FA3BF', white: '#F2FAFC',
    stoneTop: '#F0E5C1', stoneSide: '#C7CCB6', stoneShade: '#7095A1', wetStone: '#557D81', weathering: '#A3B592',
  },
} as const;
