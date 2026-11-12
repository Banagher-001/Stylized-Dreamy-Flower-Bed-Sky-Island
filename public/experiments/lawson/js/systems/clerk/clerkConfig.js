/**
 * Clerk behaviour configuration: shop floor navigation grid, obstacles, task library,
 * per-clerk job profiles and customer-interaction spots.
 *
 * Coordinates are the authored Blender/Web coordinates (x right, y up, z towards the street),
 * ground level y = 0. All positions are [x, z].
 */

export const STORE = {
  // walkable envelope of the sales floor and the stock room (stock room is x -12.05..-2.25, z -7.0..-4.55)
  salesFloor: { x0: -12.05, x1: 12.05, z0: -4.5, z1: 6.92 },
  backroom: { x0: -12.05, x1: -2.25, z0: -7.0, z1: -4.55 },
  doorGap: { x0: -4.28, x1: -3.12, z0: -4.72, z1: -4.38 },
  bodyRadius: 0.28,
  walkSpeed: 1.02,
  turnSpeed: 5.2,
  stride: 1.35,
};

/** Rectangles the NPCs must never walk through ([x0, x1, z0, z1, label]). */
export const OBSTACLES = [
  // 5 central gondola rows (+ their end caps)
  [-9.325, -8.175, -4.02, 3.02, 'gondolaA'],
  [-6.625, -5.475, -4.02, 3.02, 'gondolaB'],
  [-3.925, -2.775, -4.02, 3.02, 'gondolaC'],
  [2.825, 3.975, -4.02, 3.02, 'gondolaD'],
  [5.625, 6.775, -4.02, 3.02, 'gondolaE'],
  // L-shaped front counter / hot food counter (left wall run + front run along the glass)
  [-12.5, -10.9, 1.85, 5.45, 'counterLeftRun'],
  [-12.5, -5.72, 5.38, 6.46, 'counterFrontRun'],
  // front service furniture
  [-11.05, -10.0, 6.4, 6.9, 'impulseRack'],
  [-7.55, -5.85, 6.42, 6.92, 'tobacco'],
  [-5.8, -4.8, 6.86, 7.28, 'magazine'],
  [-6.35, -5.7, 4.98, 5.46, 'basketRack'],
  [-10.95, -10.05, 4.4, 4.9, 'promoIslandA'],
  [-5.1, -4.0, 3.7, 4.9, 'promoTableA'],
  [-2.85, -2.05, 3.75, 4.55, 'promoCartA'],
  [1.9, 3.2, 3.7, 5.0, 'promoIslandC'],
  [5.2, 6.3, 4.2, 5.1, 'promoTableC'],
  [3.25, 4.0, 5.2, 5.9, 'promoCartB'],
  [3.08, 3.82, 6.25, 6.87, 'entranceCart'],
  [1.70, 2.42, 6.28, 6.80, 'basketStack'],
  [2.60, 2.96, 6.70, 7.02, 'plantRight'],
  [-2.96, -2.60, 6.70, 7.02, 'plantLeft'],
  [1.50, 2.08, 6.88, 7.22, 'aFrameRight'],
  [-2.08, -1.50, 6.88, 7.22, 'aFrameLeft'],
  [-12.68, -12.1, -4.62, -2.9, 'cornerShelfRear'],
  [-12.68, -12.2, 6.45, 7.2, 'cornerShelfFront'],
  // right wall equipment
  [10.98, 12.62, -5.05, 0.7, 'coolerBank'],
  [9.98, 11.62, 1.48, 3.0, 'microwaveTable'],
  [11.52, 12.62, 3.3, 4.55, 'atm'],
  [7.75, 10.35, 2.48, 3.85, 'chestFreezer'],
  [8.85, 12.62, -7.1, -4.98, 'diningArea'],
  [8.95, 10.0, -5.08, -4.55, 'diningRecycle'],
  [1.32, 8.28, -6.78, -6.08, 'alcoholWall'],
  [-0.68, 8.48, -7.24, -6.7, 'rearWallCabinet'],
  // stock room
  [-12.6, -10.45, -7.24, -6.5, 'metalRack1'],
  [-10.35, -8.28, -7.24, -6.5, 'metalRack2'],
  [-6.98, -5.3, -7.2, -6.4, 'prepTable'],
  [-8.1, -7.2, -7.2, -6.45, 'washSink'],
  [-5.35, -4.18, -7.2, -6.7, 'drinkCrates'],
  [-10.2, -8.35, -6.55, -5.25, 'cartons'],
  [-2.75, -2.2, -5.95, -5.22, 'handTruck'],
  [-11.2, -10.1, -5.1, -4.66, 'cleanCorner'],
];

function rect(x0, x1, z0, z1) { return { x0, x1, z0, z1 }; }

/**
 * Task library. clerk = 'A' | 'B'.
 * targets: list of { x, z, face: [dx, dz], area } - face is the direction the clerk should look at.
 * anims: animation sequence (state names in AnimLibrary) cycled during the task.
 */
export const TASKS = {
  // ---------------------------------------------------------------- clerk A
  A: [
    { id: 'observe_entrance', weight: 10, duration: [2.4, 4.2], anims: ['Idle_LookAround'],
      targets: [{ x: -2.35, z: 6.05, face: [0, 1], area: 'entrance' }], cooldown: 18 },
    { id: 'tidy_counter', weight: 20, duration: [5, 9], anims: ['Counter_Clean', 'Cashier_Scan'],
      targets: [{ x: -9.2, z: 5.1, face: [0, 1], area: 'counter' }], cooldown: 24 },
    { id: 'check_display', weight: 15, duration: [4, 8], anims: ['Shelf_Inspect', 'Shelf_Reach_Low'],
      targets: [{ x: -5.5, z: 4.7, face: [1, 0], area: 'frontShelf' }], cooldown: 30 },
    { id: 'impulse_tidy', weight: 12, duration: [4, 8], anims: ['Shelf_Reach_Low', 'Shelf_Inspect'],
      targets: [{ x: -6.9, z: 4.4, face: [0, 1], area: 'frontShelf' }], cooldown: 30 },
    { id: 'nearby_shelf', weight: 10, duration: [5, 9], anims: ['Shelf_Inspect', 'Shelf_Reach_High'],
      targets: [{ x: -3.1, z: 3.6, face: [-1, 0], area: 'aisleFront' }], cooldown: 34 },
    { id: 'look_around', weight: 12, duration: [2.5, 4.5], anims: ['Idle_LookAround', 'Idle_Stand'],
      targets: [{ x: -9.2, z: 5.1, face: [0, 1], area: 'counter' }], cooldown: 12 },
    { id: 'short_wait', weight: 10, duration: [3, 6], anims: ['Idle_ShiftWeight', 'Idle_Stand'],
      targets: [{ x: -9.2, z: 5.1, face: [0, 1], area: 'counter' }], cooldown: 14 },
    { id: 'bag_check', weight: 9, duration: [3.5, 6], anims: ['Cashier_Bag'],
      targets: [{ x: -9.2, z: 5.1, face: [0, 1], area: 'counter' }], cooldown: 20 },
  ],
  // ---------------------------------------------------------------- clerk B
  B: [
    { id: 'shelf_inspect', weight: 17, duration: [5, 10],
      anims: ['Shelf_Inspect', 'Shelf_Reach_High', 'Shelf_Reach_Low'],
      targets: [
        { x: -7.42, z: 0.60, face: [-1, 0], area: 'aisleA' },
        { x: -4.70, z: 0.20, face: [-1, 0], area: 'aisleB' },
        { x: -2.45, z: 0.40, face: [-1, 0], area: 'aisleC' },
        { x: 2.55, z: 0.40, face: [1, 0], area: 'aisleD' },
        { x: 4.82, z: 0.20, face: [1, 0], area: 'aisleE' },
        { x: 7.42, z: 0.60, face: [-1, 0], area: 'aisleE' },
        { x: -8.75, z: 3.55, face: [0, -1], area: 'aisleFront' },
        { x: 6.20, z: 3.55, face: [0, -1], area: 'aisleFront' },
      ], cooldown: 22 },
    { id: 'restock', weight: 15, duration: [12, 20], carry: true,
      anims: ['Shelf_Restock', 'Shelf_Reach_Low', 'Shelf_Restock'],
      targets: [
        { x: -7.42, z: 1.30, face: [-1, 0], area: 'aisleA' },
        { x: -4.70, z: 1.10, face: [-1, 0], area: 'aisleB' },
        { x: 2.55, z: 1.10, face: [1, 0], area: 'aisleD' },
        { x: 7.42, z: 1.30, face: [-1, 0], area: 'aisleE' },
      ], pickup: { x: -3.72, z: -5.28, face: [-1, 0] }, cooldown: 70 },
    { id: 'cooler_check', weight: 13, duration: [5, 10], anims: ['Fridge_Inspect', 'Shelf_Reach_High'],
      targets: [{ x: 10.5, z: -2.2, face: [1, 0], area: 'cooler' }], cooldown: 40 },
    { id: 'hotfood_check', weight: 12, duration: [5, 9], anims: ['Counter_Clean', 'Shelf_Inspect'],
      targets: [{ x: -9.85, z: 4.45, face: [-1, 0], area: 'hotfood' }], cooldown: 42 },
    { id: 'floor_clean', weight: 9, duration: [6, 12], tool: 'broom', anims: ['Floor_Clean'],
      targets: [
        { x: 0.2, z: 4.3, face: [0, -1], area: 'entranceHall' },
        { x: 0.1, z: 1.5, face: [-1, 0], area: 'centerAisle' },
        { x: 4.82, z: -1.6, face: [1, 0], area: 'aisleE' },
        { x: -7.42, z: 2.2, face: [-1, 0], area: 'aisleA' },
        { x: 9.4, z: 4.1, face: [0, -1], area: 'rightHall' },
      ], cooldown: 36 },
    { id: 'dining_tidy', weight: 9, duration: [5, 10], anims: ['Table_Clean'],
      targets: [{ x: 10.9, z: -4.55, face: [0, -1], area: 'dining' }], cooldown: 50 },
    { id: 'backroom_run', weight: 7, duration: [6, 10], anims: ['Box_Pickup', 'Box_Putdown'],
      targets: [{ x: -3.72, z: -5.28, face: [-1, 0], area: 'backroom' }], cooldown: 60 },
    { id: 'idle_observe', weight: 8, duration: [3, 6], anims: ['Idle_LookAround', 'Idle_ShiftWeight'],
      targets: [{ x: 2.45, z: -0.55, face: [0, -1], area: 'home' }], cooldown: 15 },
  ],
};

/** Virtual customer interaction spots (customer-system interface, no visible customer NPCs are spawned). */
export const CUSTOMER_SPOTS = {
  entrance: { x: 0.0, z: 6.0, face: [0, 1], area: 'entrance' },
  checkout: { x: -9.2, z: 5.1, face: [0, 1], area: 'counter' },
  checkoutSupport: { x: -7.45, z: 5.05, face: [0, 1], area: 'counter' },
  aisleHelp: { x: -4.6, z: -1.2, face: [-1, 0], area: 'aisleB' },
  shelfHelp: { x: 4.8, z: -1.2, face: [1, 0], area: 'aisleE' },
};

export const CUSTOMER_EVENT = {
  autoDemo: true,           // demo event generator so the cashier/help behaviours are exercised
  minInterval: 26,
  maxInterval: 52,
  enterChance: 0.35,
  checkoutChance: 0.5,
  helpChance: 0.15,
};

export const CLERK_PROFILES = {
  A: {
    name: '店员 A',
    role: '收银与顾客接待',
    home: { x: -9.2, z: 5.1, face: [0, 1] },
    taskList: 'A',
    speed: 1.0,
    alwaysReturnForCheckout: true,
  },
  B: {
    name: '店员 B',
    role: '货架整理与店内维护',
    home: { x: 2.45, z: -0.55, face: [0, -1] },
    taskList: 'B',
    speed: 1.05,
    alwaysReturnForCheckout: false,
  },
};