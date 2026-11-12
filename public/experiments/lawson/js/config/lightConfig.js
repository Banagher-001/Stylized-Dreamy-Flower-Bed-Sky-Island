/**
 * Light rig authored in JS (the GLB lights are stripped — 209 punctual lights are far
 * too many for a realtime WebGL scene, and we need them grouped/toggleable anyway).
 *
 * Emissive materials inside the model keep their authored HDR strength; each light group
 * scales both its real lights and the matching emissive materials so switches are real.
 */
export const LIGHT_GROUPS = [
  { id: 'StoreInterior', label: '店内灯光', emissive: [/emitwarm/i, /emit.*white/i, /interiorlight/i, /ceil/i, /panel/i, /_warm/i], intensity: 1.0 },
  { id: 'LawsonSign', label: 'LAWSON 招牌', emissive: [/sign/i, /lawson/i, /logo/i, /shield/i, /lightbox/i], intensity: 1.0 },
  { id: 'FacadeStrip', label: '外墙灯带', emissive: [/facade/i, /canopy/i, /stripe/i, /eave/i, /band/i], intensity: 1.0 },
  { id: 'StreetLamp', label: '路灯', emissive: [/street/i, /lamp/i, /pylon/i], intensity: 1.0 },
  { id: 'CoolerLighting', label: '冷柜灯光', emissive: [/cooler/i, /fridge/i, /freezer/i, /led/i, /cold/i], intensity: 1.0 },
  { id: 'VendingLighting', label: '售货机灯光', emissive: [/vend/i], intensity: 1.0 },
  { id: 'WarmExterior', label: '墙面暖光', emissive: [/wall/i, /warm/i, /pendant/i, /bakery/i], intensity: 1.0 },
  { id: 'VehicleLights', label: '车辆灯光', emissive: [/headlight/i, /taillight/i, /tail/i, /head/i, /brake/i, /turn/i, /reverse/i, /plate/i, /veh/i], intensity: 1.0 },
];

/**
 * Real lights. type: point | spot | dir. Aim (target) is optional for spot.
 * These positions come from the Blender lighting rig (metres, +Y up).
 */
export const LIGHTS = [
  // --- 2nd interior deepening: dining nook (warm) + alcohol wall (bright) ---
  { group: 'StoreInterior', type: 'point', pos: [10.35, 2.90, -5.90], color: '#ffd9a8',
    intensity: 8, distance: 6.5, decay: 1.8, name: 'DiningWarm' },
  { group: 'StoreInterior', type: 'point', pos: [4.75, 3.05, -6.25], color: '#eef5ff',
    intensity: 7, distance: 6.0, decay: 1.8, name: 'AlcoholWall' },
  // interior warm ceiling lights
  { group: 'StoreInterior', type: 'point', pos: [-8.0, 3.45, 0.0], color: '#ffdfae', intensity: 6.0, distance: 13, decay: 1.75 },
  { group: 'StoreInterior', type: 'point', pos: [-2.6, 3.45, 0.0], color: '#ffdfae', intensity: 6.0, distance: 13, decay: 1.75 },
  { group: 'StoreInterior', type: 'point', pos: [3.0, 3.45, 0.0], color: '#ffdfae', intensity: 6.0, distance: 13, decay: 1.75 },
  { group: 'StoreInterior', type: 'point', pos: [8.6, 3.45, 0.0], color: '#ffdfae', intensity: 6.0, distance: 13, decay: 1.75 },
  { group: 'StoreInterior', type: 'point', pos: [-5.0, 3.30, 5.0], color: '#ffdfb8', intensity: 4.0, distance: 12, decay: 1.8 },
  { group: 'StoreInterior', type: 'point', pos: [5.0, 3.30, 4.6], color: '#ffdfb8', intensity: 4.0, distance: 12, decay: 1.8 },
  // lawson sign wash
  { group: 'LawsonSign', type: 'spot', pos: [-5.0, 4.0, 10.4], target: [-5.0, 3.9, 7.6], color: '#bcd6ff', intensity: 20, angle: 0.62, penumbra: 0.7, distance: 26, decay: 1.4 },
  { group: 'LawsonSign', type: 'spot', pos: [5.0, 4.0, 10.4], target: [5.0, 3.9, 7.6], color: '#bcd6ff', intensity: 20, angle: 0.62, penumbra: 0.7, distance: 26, decay: 1.4 },
  // shop-front strip
  { group: 'FacadeStrip', type: 'spot', pos: [-6.5, 3.05, 9.6], target: [-6.5, 2.2, 7.5], color: '#d6ebff', intensity: 12, angle: 0.85, penumbra: 0.85, distance: 24, decay: 1.5 },
  { group: 'FacadeStrip', type: 'spot', pos: [6.5, 3.05, 9.6], target: [6.5, 2.2, 7.5], color: '#d6ebff', intensity: 12, angle: 0.85, penumbra: 0.85, distance: 24, decay: 1.5 },
  // street lamps
  { group: 'StreetLamp', type: 'spot', pos: [-13.0, 6.1, 12.0], target: [-11.0, 0.0, 13.0], color: '#ffd9a8', intensity: 110, angle: 0.92, penumbra: 0.75, distance: 34, decay: 1.6, shadow: true },
  { group: 'StreetLamp', type: 'spot', pos: [13.0, 6.1, 13.5], target: [11.0, 0.0, 14.5], color: '#ffd9a8', intensity: 110, angle: 0.92, penumbra: 0.75, distance: 34, decay: 1.6 },
  { group: 'StreetLamp', type: 'spot', pos: [0.0, 5.6, 24.0], target: [0.0, 0.0, 24.5], color: '#ffd2a0', intensity: 70, angle: 1.0, penumbra: 0.8, distance: 30, decay: 1.7 },
  // cooler bank cool wash
  { group: 'CoolerLighting', type: 'point', pos: [11.1, 1.75, -2.0], color: '#cfe9ff', intensity: 10, distance: 11, decay: 1.6 },
  { group: 'CoolerLighting', type: 'point', pos: [9.0, 1.2, 2.6], color: '#d6eeff', intensity: 5, distance: 7, decay: 1.8 },
  // vending machines
  { group: 'VendingLighting', type: 'point', pos: [-14.3, 1.5, 8.7], color: '#cfe4ff', intensity: 8, distance: 8, decay: 1.7 },
  // warm wall lamps on the facade
  { group: 'WarmExterior', type: 'point', pos: [-11.6, 3.1, 9.3], color: '#ffbf7d', intensity: 6.5, distance: 11, decay: 1.7 },
  { group: 'WarmExterior', type: 'point', pos: [11.6, 3.1, 9.3], color: '#ffbf7d', intensity: 6.5, distance: 11, decay: 1.7 },
  { group: 'WarmExterior', type: 'point', pos: [-13.4, 3.0, 2.4], color: '#ffb877', intensity: 7, distance: 9, decay: 1.6 },
  { group: 'WarmExterior', type: 'point', pos: [13.4, 3.0, 2.4], color: '#ffb877', intensity: 7, distance: 9, decay: 1.6 },
];

/** Time-of-day keys: sky/sun/fog/exposure/lamp auto behaviour. */
export const DAY_NIGHT_KEYS = [
  { t: 0.0,  skyTop: '#050817', skyBottom: '#0d1330', fog: '#0a1024', sun: 0.05, sunColor: '#9fb4e8', hemi: 0.10, ambient: 0.06, exposure: 0.82, lamps: 1.0, emissive: 1.15 },
  { t: 5.0,  skyTop: '#0e1734', skyBottom: '#3a3550', fog: '#1b1f3a', sun: 0.10, sunColor: '#9fb4e8', hemi: 0.22, ambient: 0.09, exposure: 0.84, lamps: 0.85, emissive: 1.05 },
  { t: 6.6,  skyTop: '#4a5f96', skyBottom: '#e0a97e', fog: '#8f8ba6', sun: 1.1, sunColor: '#ffb88a', hemi: 0.52, ambient: 0.14, exposure: 0.8, lamps: 0.15, emissive: 0.75 },
  { t: 9.0,  skyTop: '#3f86d8', skyBottom: '#cbe6fb', fog: '#bfd9ee', sun: 2.6, sunColor: '#fff3e2', hemi: 0.95, ambient: 0.22, exposure: 0.84, lamps: 0.0, emissive: 0.36 },
  { t: 13.0, skyTop: '#3d86dd', skyBottom: '#d6ecfc', fog: '#c8e0f4', sun: 3.1, sunColor: '#fffaf0', hemi: 1.05, ambient: 0.24, exposure: 0.84, lamps: 0.0, emissive: 0.35 },
  { t: 17.2, skyTop: '#5b6db0', skyBottom: '#f0b183', fog: '#b9a3a6', sun: 2.0, sunColor: '#ffcf9e', hemi: 0.62, ambient: 0.16, exposure: 0.8, lamps: 0.35, emissive: 0.85 },
  { t: 18.5, skyTop: '#3b2f70', skyBottom: '#ef9a6d', fog: '#5f4f7e', sun: 1.15, sunColor: '#ffc490', hemi: 0.52, ambient: 0.15, exposure: 0.80, lamps: 1.0, emissive: 1.0 },
  { t: 20.0, skyTop: '#241f47', skyBottom: '#7a4a63', fog: '#2e2844', sun: 0.36, sunColor: '#cf9fb8', hemi: 0.30, ambient: 0.11, exposure: 0.84, lamps: 1.0, emissive: 0.98 },
  { t: 22.0, skyTop: '#0a0f26', skyBottom: '#1a1e3c', fog: '#0d1330', sun: 0.08, sunColor: '#9fb4e8', hemi: 0.18, ambient: 0.09, exposure: 0.86, lamps: 1.0, emissive: 1.0 },
  { t: 24.0, skyTop: '#050817', skyBottom: '#0d1330', fog: '#0a1024', sun: 0.05, sunColor: '#9fb4e8', hemi: 0.10, ambient: 0.06, exposure: 0.82, lamps: 1.0, emissive: 1.15 },
];

export const PRESETS = { day: 9.0, dusk: 18.5, night: 22.0 };