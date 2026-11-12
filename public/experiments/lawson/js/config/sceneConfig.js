/**
 * Scene-wide constants. Coordinates are the authored Blender ones:
 * +X right, +Y up, +Z towards the street, 1 unit = 1 m.
 */
export const SITE = {
  storeW: 26,
  storeD: 15,
  eave: 4.6,
  parapet: 5.2,
  doorZ: 7.5,
  sidewalkZ: [7.5, 9.4],
  parkingZ: [9.5, 15.0],
  aisleZ: [15.0, 20.6],
  roadZ: [21.0, 30.0],
  walkY: -0.10,
  parkY: -0.14,
  aisleY: -0.16,
  roadY: -0.18,
  slots: [-10.5, -7.4, -4.3, 4.3, 7.4, 10.5],
  slotW: 2.9,
  parkedZ: 12.5,
  siteX: [-44, 44],
};

export const INTERIOR = {
  floorY: 0.006,
  ceilingY: 3.85,
  boundsX: [-12.45, 12.45],
  boundsZ: [-4.05, 7.1],
  walkBoundsX: [-12.2, 12.2],
  walkBoundsZ: [-4.15, 7.0],
  eyeHeight: 1.62,
};

export const VEHICLE_SPEC = {
  // wheelR / wheelbase / track are measured from each GLB's wheel node positions
  // and tyre mesh bounds (see reports/vehicle_rig_audit.md).
  A: { name: '小顾客车', wheelR: 0.2994, wheelbase: 2.42, track: 1.44, dwell: 8.0, color: '#c9cbd9' },
  B: { name: '罗森配送车', wheelR: 0.3394, wheelbase: 3.30, track: 1.64, dwell: 10.0, color: '#f2f3f5' },
  C: { name: '深紫轿跑', wheelR: 0.3294, wheelbase: 2.76, track: 1.58, dwell: 6.0, color: '#3b2b57' },
};

/** Camera presets: pos / target in world space. */
export const CAMERA_PRESETS = {
  hero:     { pos: [20.5, 5.2, 28.5], target: [2.2, 2.9, 5.5] },
  front:    { pos: [0.0, 5.6, 32.0],   target: [0.0, 2.6, 6.0] },
  left:     { pos: [33.0, 8.4, 2.0],   target: [-1.0, 2.0, 1.0] },
  rear:     { pos: [22.0, 12.0, -24.0], target: [0.0, 2.0, -2.0] },
  top:      { pos: [0.0, 44.0, 8.0],   target: [0.0, 0.0, 2.0] },
  interior: { pos: [0.6, 1.75, 6.4],   target: [0.0, 1.45, -2.8] },
  checkout: { pos: [-4.2, 1.9, 9.0],   target: [-9.2, 1.05, 6.0] },
  vehicle:  { pos: [0, 9, 26],         target: [0, 1.2, 8] },
};

export const CAMERA_LIMITS = {
  minDistance: 4,
  maxDistance: 150,
  maxPolarAngle: Math.PI * 0.494,
  minPolarAngle: 0.05,
  dampingFactor: 0.075,
};

export const QUALITY_PRESETS = {
  high:   { pixelRatio: 2.0, maxPixels: 2.4e6, shadowMap: 1536, bloom: true,  bloomStrength: 0.16, shadows: true, antialias: true },
  medium: { pixelRatio: 1.5, maxPixels: 1.7e6, shadowMap: 1024, bloom: true,  bloomStrength: 0.12, shadows: true, antialias: true },
  low:    { pixelRatio: 1.0, maxPixels: 1.1e6, shadowMap: 512,  bloom: false, bloomStrength: 0.0,  shadows: false, antialias: false },
};

/** Where the automatic doors are (world space). */
export const DOOR_ANCHOR = { x: 0, y: 1.3, z: 7.5, slideTravel: 0.92, openTime: 1.05, holdTime: 3.0, sensor: 3.4 };

/** Roof / ceiling node names to hide in cut-away mode. */
export const ROOF_NODE_NAMES = ['roofRoot'];
export const CEILING_NAME_PATTERNS = [/interiorCeiling/i, /ceilingpanel/i, /ceilling/i, /^ceiling/i, /lightpanel/i];

export const DEFAULT_STATE = {
  quality: 'high',
  timeOfDay: 18.5,
  roofVisible: true,
  cameraMode: 'orbit',
  paused: false,
  traffic: { enabled: true, speed: 1, running: false, current: 'A', phase: 'IDLE' },
  doors: { automatic: true, isOpen: false },
};