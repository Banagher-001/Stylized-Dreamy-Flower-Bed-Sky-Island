/**
 * Vehicle routes + state machine constants (world space, +y up, +z towards road).
 *
 * Car models (car_A/B/C.glb) are authored with:
 *   root node carX_root (identity transform, extras.forward_axis = "-Z")
 *   front wheels: steerFL / steerFR (steering pivot) -> wheelFL / wheelFR (spin)
 *   rear wheels : wheelRL / wheelRR (spin)
 *   spin axis   : local +X (wheel node local frame equals root frame)
 *   -Z = car forward, +Y = up, +X = car right.
 *
 * Parking slots are at z = 12.5, cars nose-in (facing the store, -Z).
 * Leaving the slot: REVERSE straight back to the aisle (z = 16.8), stop,
 * then drive FORWARD in a right-hand arc onto the aisle and east onto the road.
 */

export const PARKED_Z = 12.5;
export const REVERSE_END_Z = 17.9;
export const ROAD_Z = 23.4;
export const OFFSCREEN_X = 41;

export const ROUTES = {
  A: {
    in: [[-41, 23.4], [-30, 23.4], [-22.3, 23.4], [-16.1, 23.4], [-13.3, 22.65], [-11.25, 20.6],
         [-10.6, 18.6], [-10.5, 17.8], [-10.5, 16.5], [-10.5, 14.6], [-10.5, 12.5]],
  },
  B: {
    in: [[-41, 23.4], [-26, 23.4], [-10, 23.4], [1.8, 23.4], [3.25, 23.21], [4.6, 22.65],
         [6.65, 20.6], [7.21, 19.25], [7.4, 17.8], [7.4, 16.5], [7.4, 14.6], [7.4, 12.5]],
  },
  C: {
    in: [[-41, 23.4], [-28, 23.4], [-14.5, 23.4], [-1.3, 23.4], [0.15, 23.21], [1.5, 22.65],
         [2.66, 21.76], [3.55, 20.6], [4.11, 19.25], [4.3, 17.8], [4.3, 16.5], [4.3, 14.6],
         [4.3, 12.5]],
  },
};

/** Straight backing line from the slot to the reverse end position. */
export function reverseRoute(slotX) {
  return [[slotX, PARKED_Z], [slotX, PARKED_Z + 1.2], [slotX, PARKED_Z + 2.6],
          [slotX, PARKED_Z + 4.1], [slotX, REVERSE_END_Z]];
}

/** Forward exit: right-hand arc out of the slot, along the aisle, east onto the road, off-screen. */
export function exitRoute(slotX) {
  // forward drive out of the aisle: start heading -Z (north), right-hand arc onto +X (east),
  // then a long, shallow S-curve onto the road and off the east edge of the scene.
  const R = 2.2;
  const z0 = REVERSE_END_Z;
  const ex = slotX + R;
  const arc = [];
  for (let i = 0; i <= 6; i++) {
    const a = Math.PI + (i / 6) * (Math.PI / 2);   // PI -> 3PI/2 : -Z -> +X
    arc.push([slotX + R + Math.cos(a) * R, z0 + Math.sin(a) * R]);
  }
  return [
    ...arc,
    [ex + 1.6, z0 - R + 0.12],
    [ex + 4.0, z0 - R + 0.40],
    [ex + 6.6, z0 - R + 1.20],
    [ex + 9.0, z0 - R + 2.60],
    [ex + 11.0, z0 - R + 4.30],
    [ex + 12.8, z0 - R + 6.10],
    [ex + 15.0, z0 - R + 7.10],
    [ex + 18.5, z0 - R + 7.60],
    [ex + 23.0, z0 - R + 7.70],
    [OFFSCREEN_X, z0 - R + 7.70],
  ];
}

export const SPEEDS = {
  approach: 8.2,
  turning: 3.4,
  parking: 1.5,
  reverse: 2.2,          // m/s (about 27% of the 8.2 m/s approach speed)
  reverseAccel: 1.2,     // m/s^2
  reverseBrake: 1.4,     // m/s^2
  exitAccel: 2.4,        // m/s^2
  exitCruise: 9.0,       // m/s
  entryAccel: 0,         // entry legs follow the curve at a constant speed
};

/** Split points for the entry curve (u along the in-curve). */
export const IN_SPLIT = [0.0, 0.46, 0.74, 1.0];

/** State machine states required by the vehicle rework spec. */
export const PHASES = {
  OFFSCREEN_WAIT: 'OFFSCREEN_WAIT',
  APPROACHING: 'APPROACHING',
  TURNING_IN: 'TURNING_IN',
  PARKING: 'PARKING',
  PARKED: 'PARKED',
  REVERSE_PREPARE: 'REVERSE_PREPARE',
  REVERSING_OUT: 'REVERSING_OUT',
  REVERSE_STOP: 'REVERSE_STOP',
  SHIFT_TO_DRIVE: 'SHIFT_TO_DRIVE',
  ALIGNING_TO_EXIT: 'ALIGNING_TO_EXIT',
  DRIVING_OUT: 'DRIVING_OUT',
  OFFSCREEN_RESET: 'OFFSCREEN_RESET',
};

/** How long each hold state lasts (seconds). */
export const HOLD = {
  reversePrepare: 0.9,
  reverseStop: 0.9,
  shiftToDrive: 0.6,
  offscreenReset: 1.2,
  betweenCars: 1.6,
  parkBrakeOff: 0.7,
};

export const TURN_SIGNAL = { in: [0.34, 0.62], out: [0.30, 0.55] };