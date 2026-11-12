/** Static assets. All local — the page must run offline behind any static server. */
export const MODELS = {
  scene: { key: 'scene', url: './assets/models/lawson_scene.glb', label: '便利店场景' },
  cars: {
    A: { key: 'carA', url: './assets/models/car_A.glb', label: '汽车 A' },
    B: { key: 'carB', url: './assets/models/car_B.glb', label: '汽车 B' },
    C: { key: 'carC', url: './assets/models/car_C.glb', label: '汽车 C' },
  },
};

export const VENDOR = {
  three: './vendor/three/three.module.js',
};

/** Node names we look for after loading. Missing entries are tolerated (reported in console). */
export const IMPORTANT_NODES = {
  roof: ['roofRoot'],
  doors: ['slideDoorLeft_pivot', 'slideDoorRight_pivot'],
  clerks: ['clerkA_root', 'clerkB_root'],
  cars: ['carA_root', 'carB_root', 'carC_root'],
};
