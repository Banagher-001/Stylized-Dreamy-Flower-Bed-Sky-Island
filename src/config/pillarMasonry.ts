import type { layoutConfig } from './layout';
import type { MossFace, MossPoint } from './pavingMoss';
import type { StoneColors } from '../materials/createArtMaterial';

export type PillarName = (typeof layoutConfig.columns)[number]['name'];
type StoneBand = 'base' | 'shaft' | 'cap';

export interface MasonryCourse {
  range: readonly [bottom: number, top: number];
  size: readonly [width: number, depth: number];
  cuts: readonly [northWest: number, northEast: number, southEast: number, southWest: number];
  offset?: MossPoint;
  /** Local X displacement from the bottom to the top of the course. */
  lean?: number;
  /** Split plane in plan view, expressed in column-local coordinates. */
  seam?: readonly [normalX: number, normalZ: number, offset: number, gap: number];
  /** The top of the second piece can sit lower on a fractured crown. */
  step?: number;
  /** Expose the cooler stone underneath the pale crown on the second piece. */
  exposedBed?: boolean;
  chip?: number;
  bevel?: number;
}

export interface PillarMossSite {
  band: StoneBand;
  course: number;
  piece: number;
  face: MossFace;
  shape: 'cluster' | 'strip' | 'flecks';
  anchor: MossPoint;
  size: MossPoint;
  rise: number;
  angle?: number;
}

interface PillarDesign {
  colors: StoneColors;
  base: readonly MasonryCourse[];
  shaft: readonly MasonryCourse[];
  cap: readonly MasonryCourse[];
  moss: readonly PillarMossSite[];
}

export const pillarMasonry: Record<PillarName, PillarDesign> = {
  columnUpperLeft: {
    colors: { top: '#A7B8BE', side: '#7895A2', shade: '#3B5A6A' },
    base: [
      { range: [-0.012, 0.125], size: [1.03, 1.07], cuts: [.077, .054, .103, .046], chip: .058 },
      { range: [.117, .227], size: [.91, .92], offset: [-.016, .01], cuts: [.068, .03, .049, .08], seam: [1, .36, -.11, .021] },
    ],
    shaft: [
      { range: [.216, .630], size: [.721, .766], offset: [-.014, -.009], cuts: [.061, .045, .073, .061], seam: [-.4, .91, .052, .025], lean: .037 },
      { range: [.663, 1.376], size: [.741, .775], offset: [-.012, .008], cuts: [.047, .063, .062, .052], seam: [1, .29, -.126, .032], lean: -.035, chip: .055 },
      { range: [1.410, 2.340], size: [.686, .749], offset: [-.041, -.016], cuts: [.058, .047, .104, .087], seam: [-.23, 1, .082, .023], lean: .061, chip: .109 },
      { range: [2.363, 3.224], size: [.744, .782], offset: [0, .008], cuts: [.086, .039, .066, .051], seam: [1, -.26, .154, .032], lean: -.041, chip: .054 },
    ],
    cap: [
      { range: [3.205, 3.295], size: [.866, .838], offset: [-.036, .017], cuts: [.094, .055, .061, .042], bevel: .014 },
      { range: [3.287, 3.485], size: [1.035, .982], offset: [-.024, .018], cuts: [.145, .047, .076, .112], seam: [.28, -1, .085, .026], chip: .114, bevel: .026 },
    ],
    moss: [
      { band: 'cap', course: 1, piece: 0, face: 'top', shape: 'cluster', anchor: [-.249, .176], size: [.452, .398], rise: .026, angle: -.51 },
      { band: 'cap', course: 1, piece: 1, face: 'top', shape: 'flecks', anchor: [.213, -.241], size: [.288, .242], rise: .017, angle: .26 },
      { band: 'base', course: 1, piece: 0, face: 'top', shape: 'strip', anchor: [-.409, .025], size: [.055, .193], rise: .019, angle: -.12 },
    ],
  },
  columnRight: {
    colors: { top: '#BDC2B8', side: '#81959A', shade: '#406072' },
    base: [
      { range: [-.016, .148], size: [1.015, 1.072], offset: [.009, 0], cuts: [.053, .111, .062, .034], seam: [1, -.22, .29, .028], chip: .045 },
      { range: [.141, .208], size: [.878, .86], offset: [.03, -.021], cuts: [.075, .048, .054, .09], bevel: .012 },
    ],
    shaft: [
      { range: [.195, .569], size: [.776, .796], offset: [.011, -.014], cuts: [.071, .043, .093, .048], seam: [1, -.12, -.124, .031], lean: .035, chip: .058 },
      { range: [.606, 1.339], size: [.707, .778], offset: [.018, .007], cuts: [.056, .052, .063, .067], seam: [1, -.2, .156, .031], lean: -.021, chip: .055 },
      { range: [1.374, 1.989], size: [.756, .794], offset: [.021, -.024], cuts: [.04, .091, .074, .046], seam: [.24, 1, -.013, .035], lean: .018, chip: .062 },
      { range: [2.024, 2.644], size: [.698, .746], offset: [-.043, -.004], cuts: [.084, .035, .075, .043], seam: [1, .31, -.129, .029], lean: -.037 },
      { range: [2.684, 3.215], size: [.831, .817], offset: [.05, -.02], cuts: [.071, .082, .103, .042], seam: [-.17, 1, .021, .03], lean: .043, chip: .096 },
    ],
    cap: [
      { range: [3.199, 3.284], size: [.947, .865], offset: [.044, -.008], cuts: [.059, .107, .055, .07], bevel: .013 },
      { range: [3.277, 3.475], size: [1.105, 1.045], offset: [.028, -.025], cuts: [.067, .203, .054, .106], seam: [.84, -.78, .15, .047], step: -.091, exposedBed: true, chip: .106, bevel: .026 },
    ],
    moss: [
      { band: 'cap', course: 1, piece: 1, face: 'top', shape: 'cluster', anchor: [.271, -.208], size: [.285, .303], rise: .03, angle: .52 },
      { band: 'cap', course: 1, piece: 0, face: 'top', shape: 'strip', anchor: [-.134, .286], size: [.31, .166], rise: .019, angle: -.63 },
      { band: 'shaft', course: 2, piece: 1, face: 'right', shape: 'strip', anchor: [.035, .158], size: [.134, .236], rise: .016, angle: -.48 },
    ],
  },
  columnLower: {
    colors: { top: '#9DAFB5', side: '#70909E', shade: '#355263' },
    base: [
      { range: [-.017, .121], size: [1.026, 1.073], offset: [-.005, -.002], cuts: [.11, .067, .091, .053], seam: [.76, .65, -.16, .027], chip: .065 },
      { range: [.115, .238], size: [.859, .896], offset: [-.036, .027], cuts: [.102, .05, .068, .084], chip: .086 },
    ],
    shaft: [
      { range: [.225, .604], size: [.771, .819], offset: [-.018, .014], cuts: [.079, .052, .109, .062], seam: [.89, -.42, .023, .033], lean: -.051 },
      { range: [.642, 1.310], size: [.721, .776], offset: [.027, .015], cuts: [.062, .08, .038, .117], seam: [1, .29, -.116, .035], lean: .054, chip: .075 },
      { range: [1.346, 1.621], size: [.821, .865], offset: [.034, -.012], cuts: [.082, .065, .131, .101], seam: [.2, 1, .001, .034], lean: -.077, chip: .06, bevel: .024 },
      { range: [1.656, 2.419], size: [.673, .735], offset: [-.041, .008], cuts: [.05, .089, .091, .043], seam: [1, -.19, .177, .035], lean: .038, chip: .083 },
      { range: [2.453, 3.247], size: [.755, .815], offset: [.006, .02], cuts: [.105, .056, .062, .096], seam: [-.4, 1, -.039, .034], lean: -.079, chip: .096 },
    ],
    cap: [
      { range: [3.214, 3.295], size: [.89, .878], offset: [-.039, .025], cuts: [.092, .056, .105, .07], bevel: .013 },
      { range: [3.282, 3.506], size: [1.092, 1.025], offset: [-.058, .035], cuts: [.13, .161, .222, .059], seam: [1, -.55, -.03, .047], step: -.091, chip: .146, bevel: .028 },
    ],
    moss: [
      { band: 'cap', course: 1, piece: 0, face: 'top', shape: 'strip', anchor: [-.327, .187], size: [.311, .449], rise: .027, angle: -.4 },
      { band: 'cap', course: 1, piece: 1, face: 'top', shape: 'cluster', anchor: [.218, -.061], size: [.245, .325], rise: .028, angle: .49 },
      { band: 'shaft', course: 0, piece: 0, face: 'front', shape: 'flecks', anchor: [-.221, -.015], size: [.135, .122], rise: .018, angle: .3 },
    ],
  },
};
