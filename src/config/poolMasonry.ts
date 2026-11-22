interface PoolCourse {
  /** Change to the band’s outer radius, in courtyard units. */
  spread: number;
  /** Position of the joint, along the original side from its first corner. */
  joint?: number;
  skew?: number;
  wear?: number;
}

interface PoolCrown extends PoolCourse {
  rise: number;
  bevel: number;
  smallStone?: { end: 'start' | 'finish'; name: string; rise: number };
  cut?: { corner: 0 | 1; along: number; inward: number };
  chip?: number;
}

export interface PoolEdge {
  side: number;
  bed: number;
  foot: PoolCourse & { rise: number };
  lower: PoolCourse;
  upper: PoolCourse;
  innerJoint?: readonly [start: number, joint: number, end: number];
  crown: PoolCrown;
}

/** Ordered by the water-stop study numbers. Side indices match the original coping meshes. */
export const poolEdges: readonly PoolEdge[] = [
  {
    side: 5, bed: .218, // 1 · Long coping with a short repair at the left corner.
    foot: { spread: -.003, joint: .56, rise: .006 },
    lower: { spread: .016, joint: .40, skew: .015, wear: .068 },
    upper: { spread: -.015, joint: .67, skew: -.027 },
    crown: {
      spread: .008, joint: .27, skew: .025, rise: .004, bevel: .025,
      smallStone: { end: 'start', name: 'repair', rise: -.019 },
    },
  },
  {
    side: 4, bed: .243, // 2 · Short, lowered stone close to side 1.
    foot: { spread: -.009, joint: .68, rise: -.004 },
    lower: { spread: .009, joint: .27 },
    upper: { spread: -.024, joint: .57, skew: .023, wear: .053 },
    crown: {
      spread: -.012, joint: .77, skew: -.023, rise: -.002, bevel: .023,
      smallStone: { end: 'finish', name: 'step', rise: -.054 },
    },
  },
  {
    side: 3, bed: .232, // 3 · Recessed seam above the shaded inner wall.
    foot: { spread: -.023, rise: .003 },
    lower: { spread: .005, joint: .28 },
    upper: { spread: -.009, joint: .69 },
    innerJoint: [.49, .642, .79],
    crown: { spread: -.018, rise: -.009, bevel: .021, chip: .043 },
  },
  {
    side: 2, bed: .251, // 4 · Large rear slab with a narrow end stone.
    foot: { spread: -.028, rise: -.009 },
    lower: { spread: -.006, joint: .58 },
    upper: { spread: -.022, joint: .37, skew: .017 },
    crown: {
      spread: .011, joint: .81, skew: -.012, rise: .005, bevel: .024,
      smallStone: { end: 'finish', name: 'end', rise: -.006 },
    },
  },
  {
    side: 1, bed: .233, // 5 · Continuous bright edge and a bevel facing side 6.
    foot: { spread: -.015, rise: .005 },
    lower: { spread: .003 },
    upper: { spread: -.012, joint: .55 },
    crown: {
      spread: .003, rise: .003, bevel: .024,
      cut: { corner: 0, along: .082, inward: .048 },
    },
  },
  {
    side: 0, bed: .241, // 6 · Clear stretch of the lining for the shallow step.
    foot: { spread: -.012, rise: -.006 },
    lower: { spread: .004, joint: .54, skew: -.020 },
    upper: { spread: -.021, joint: .25 },
    crown: { spread: -.006, rise: -.005, bevel: .021 },
  },
  {
    side: 7, bed: .220, // 7 · Broken outer corner close to side 8.
    foot: { spread: 0, joint: .67, rise: .008 },
    lower: { spread: .012, joint: .47, skew: -.023 },
    upper: { spread: -.017, joint: .29, skew: .018, wear: .047 },
    crown: {
      spread: .017, rise: .009, bevel: .024, chip: .112,
      cut: { corner: 0, along: .163, inward: .116 },
    },
  },
  {
    side: 6, bed: .252, // 8 · Long pale front edge over offset joints.
    foot: { spread: -.007, joint: .43, rise: -.004 },
    lower: { spread: .016, joint: .30, skew: .018 },
    upper: { spread: -.006, joint: .66, skew: -.021 },
    crown: { spread: .004, rise: -.004, bevel: .025, chip: .042 },
  },
];
