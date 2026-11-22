import { Group, Matrix4, Mesh } from 'three';
import type { BufferGeometry, Material } from 'three';
import { layoutConfig } from '../config/layout';
import { pillarMasonry } from '../config/pillarMasonry';
import type { MasonryCourse, PillarMossSite } from '../config/pillarMasonry';
import type { MossPatch, MossPoint } from '../config/pavingMoss';
import { createPavingMossGeometry } from '../geometry/createPavingMossGeometry';
import { createStoneBlockGeometry, createStonePrismGeometry } from '../geometry/createStoneBlockGeometry';

const mossShapes: Record<PillarMossSite['shape'], MossPatch['lobes']> = {
  cluster: [
    {
      outline: [[-.47, -.15], [-.36, -.38], [-.08, -.42], [.08, -.28], [.36, -.24], [.48, .03],
        [.24, .18], [.12, .42], [-.18, .38], [-.26, .22], [-.46, .2]],
      peak: [-.035, .018], rise: 1, rim: .29,
    },
    {
      outline: [[.03, .19], [.19, .16], [.39, .24], [.46, .38], [.28, .49], [.12, .42]],
      peak: [.23, .31], rise: .62, rim: .19,
    },
  ],
  strip: [
    {
      outline: [[-.43, -.28], [-.15, -.44], [.12, -.38], [.38, -.47], [.47, -.18],
        [.31, .05], [.42, .28], [.19, .44], [-.08, .37], [-.29, .28], [-.48, .11]],
      peak: [.03, -.05], rise: 1, rim: .23,
    },
  ],
  flecks: [
    {
      outline: [[-.47, -.24], [-.27, -.41], [-.11, -.31], [-.035, -.08], [-.22, .15], [-.42, .04]],
      peak: [-.25, -.13], rise: 1, rim: .26,
    },
    {
      outline: [[.015, .085], [.21, -.02], [.42, .07], [.45, .32], [.28, .46], [.075, .34]],
      peak: [.23, .19], rise: .69, rim: .20,
    },
  ],
};
const materialSeeds = { base: 61, shaft: 0, cap: 133 } as const;

function mossPatch(site: PillarMossSite): MossPatch {
  const cos = Math.cos(site.angle ?? 0), sin = Math.sin(site.angle ?? 0);
  function point([x, z]: MossPoint): MossPoint {
    const sx = x * site.size[0], sz = z * site.size[1];
    return [cos * sx - sin * sz, sin * sx + cos * sz];
  }
  return {
    anchor: site.anchor,
    lobes: mossShapes[site.shape].map(lobe => ({
      outline: lobe.outline.map(point), peak: point(lobe.peak),
      rise: site.rise * lobe.rise, rim: site.rise * lobe.rim,
    })),
  };
}

function outline(course: MasonryCourse): MossPoint[] {
  const x = course.size[0] / 2, z = course.size[1] / 2;
  const [nw, ne, se, sw] = course.cuts;
  const [ox, oz] = course.offset ?? [0, 0];
  const corners: MossPoint[] = [
    [-x + nw, -z], [x - ne, -z], [x, -z + ne], [x, z - se],
    [x - se, z], [-x + sw, z], [-x, z - sw], [-x, -z + nw],
  ];
  return corners.map(([x, z]) => [x + ox, z + oz]);
}

function splitCourse(points: MossPoint[], seam: NonNullable<MasonryCourse['seam']>, side: number): MossPoint[] {
  const [normalX, normalZ, offset, gap] = seam;
  const halfGap = Math.hypot(normalX, normalZ) * gap / 2;
  const distance = ([x, z]: MossPoint) => side * (normalX * x + normalZ * z - offset) + halfGap;
  const result: MossPoint[] = [];
  for (let i = 0; i < points.length; i++) {
    const a = points[i]!, b = points[(i + 1) % points.length]!;
    const da = distance(a), db = distance(b);
    if (da <= 0) result.push(a);
    if (da * db < 0) {
      const t = da / (da - db);
      result.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    }
  }
  return result;
}

export function createMasonryPillar(
  placement: (typeof layoutConfig.columns)[number], index: number,
  materials: { stone: Material; exposedStone: Material; moss: Material },
  own: (geometry: BufferGeometry) => BufferGeometry,
) {
  const design = pillarMasonry[placement.name];
  const column = new Group();
  column.name = placement.name;
  const [x, y, z] = placement.position;
  column.position.set(x, y, z);
  column.rotation.y = placement.rotationY;
  const shaft = new Group();
  shaft.name = `${column.name}-shaft`;
  column.add(shaft);
  let stoneNumber = 0;

  function place(parent: Group | Mesh, name: string, geometry: BufferGeometry, material: Material, y = 0) {
    const mesh = new Mesh(own(geometry), material);
    mesh.name = name;
    mesh.position.y = y;
    mesh.castShadow = mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }

  const bed = design.shaft[0]!.range[0];
  const crown = design.shaft.at(-1)!.range[1];
  place(shaft, `${column.name}-joint-0`, createStoneBlockGeometry(.43, crown - bed, .46, {
    bevel: 0, cornerCut: .027, seed: 47,
  }), materials.stone, (bed + crown) / 2);

  for (const band of ['base', 'shaft', 'cap'] as const) {
    for (const [courseIndex, course] of design[band].entries()) {
      const points = outline(course);
      const pieces = course.seam ? [splitCourse(points, course.seam, 1), splitCourse(points, course.seam, -1)] : [points];
      for (const [pieceIndex, piece] of pieces.entries()) {
        const [bottom, top] = course.range;
        const height = top - bottom + (pieceIndex === 1 ? course.step ?? 0 : 0);
        const seed = 31 + index * 79 + materialSeeds[band] + courseIndex * 11 + pieceIndex * 17;
        const geometry = createStonePrismGeometry(piece, height, {
          bevel: course.bevel ?? (band === 'shaft' ? .019 : .022),
          cornerCut: 0, seed,
          chipCorner: (index + courseIndex + pieceIndex * 3) % piece.length,
          chipSize: course.chip,
        });
        if (course.lean) geometry.applyMatrix4(new Matrix4().set(
          1, course.lean / height, 0, 0,
          0, 1, 0, 0,
          0, 0, 1, 0,
          0, 0, 0, 1,
        ));
        const name = band === 'shaft' ? `block-${stoneNumber++}` : `${band}-${courseIndex}-${pieceIndex}`;
        const material = pieceIndex === 1 && course.exposedBed ? materials.exposedStone : materials.stone;
        const stone = place(band === 'shaft' ? shaft : column, `${column.name}-${name}`, geometry, material, bottom + height / 2);
        for (const [mossIndex, site] of design.moss.entries()) {
          if (site.band !== band || site.course !== courseIndex || site.piece !== pieceIndex) continue;
          const moss = createPavingMossGeometry(geometry, mossPatch(site), site.face);
          if (moss) place(stone, `${column.name}-moss-${mossIndex}`, moss, materials.moss);
        }
      }
    }
  }
  return column;
}
