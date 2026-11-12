/** Three deliberately offset world-space flights; no placement RNG is consumed. */
export const birdConfig = {
  routes: [
    { center: [-.6, 1.3], radii: [7.2, 5.5], height: 4.45, rotation: .05, period: 48, phase: .14, direction: 1, span: .34, flapCycle: 5.2, flapDuration: 1.4, flapRate: 1.7 },
    { center: [.4, .7], radii: [6.1, 6.4], height: 5.10, rotation: -.65, period: 54, phase: .55, direction: -1, span: .32, flapCycle: 5.4, flapDuration: 1.6, flapRate: 1.9 },
    { center: [-.4, 1.1], radii: [7.8, 4.9], height: 5.75, rotation: .35, period: 61, phase: .81, direction: 1, span: .33, flapCycle: 4.9, flapDuration: 1.3, flapRate: 1.6 },
  ],
  colors: { warm: '#F3EAC4', light: '#F8FCED', cool: '#7095A1', tip: '#405B55', beak: '#DCCB9D' },
  bodyRadius: .69,
  clearance: .25,
  desktopMargin: 20,
  mobileMargin: 14,
  fadePixels: 26,
  minimumAlpha: .015,
} as const;
